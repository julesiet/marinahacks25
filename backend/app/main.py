# backend/app/main.py
from __future__ import annotations

import os, time, json, secrets
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# -------------------------------------------------------------------
# Env & constants
# -------------------------------------------------------------------
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:3001/auth/callback")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# -------------------------------------------------------------------
# App & CORS
# -------------------------------------------------------------------
app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# In-memory state (hackathon-friendly)
# -------------------------------------------------------------------
PKCE_STORE: Dict[str, Dict[str, Any]] = {}     # state -> {verifier, ts}
TOKEN_STORE: Dict[str, Dict[str, Any]] = {}    # "spotify:{id}" -> tokens + user
USER_TASTE: Dict[str, Dict[str, set]] = {}     # "spotify:{id}" -> liked artists/genres (sets)

# -------------------------------------------------------------------
# Health & routes listing
# -------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/__routes")
def __routes():
    return [r.path for r in app.router.routes]

# -------------------------------------------------------------------
# Auth (lazy import helpers to avoid init-order issues)
# -------------------------------------------------------------------
@app.get("/auth/login")
def auth_login():
    from app.oauth_login import gen_code_verifier, code_challenge, build_auth_url
    state = secrets.token_urlsafe(16)
    verifier = gen_code_verifier()
    challenge = code_challenge(verifier)
    PKCE_STORE[state] = {"verifier": verifier, "ts": time.time()}
    return RedirectResponse(build_auth_url(state, challenge))

@app.get("/auth/callback")
async def auth_callback(code: str | None = None, state: str | None = None):
    if not code or not state or state not in PKCE_STORE:
        raise HTTPException(400, "invalid state or code")

    from app.oauth_tokens import exchange_code_for_tokens
    verifier = PKCE_STORE.pop(state)["verifier"]
    tokens = await exchange_code_for_tokens(code, verifier)

    # Fetch user
    async with httpx.AsyncClient(timeout=10) as client:
        me = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        me.raise_for_status()
        user = me.json()

    key = f"spotify:{user['id']}"
    TOKEN_STORE[key] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "exp_ts": time.time() + tokens.get("expires_in", 3600),
        "user": {"id": user["id"], "display_name": user.get("display_name")},
    }
    return RedirectResponse(f"{WEB_ORIGIN}?user={user['id']}")

# -------------------------------------------------------------------
# Taste memory (optional but useful)
# -------------------------------------------------------------------
class TasteIn(BaseModel):
    user: str
    artistNames: List[str] = []
    genres: List[str] = []

@app.post("/taste/accept")
def taste_accept(body: TasteIn):
    key = f"spotify:{body.user}"
    rec = USER_TASTE.setdefault(key, {"liked_artists": set(), "liked_genres": set()})
    rec["liked_artists"].update(a.lower() for a in body.artistNames)
    rec["liked_genres"].update(g.lower() for g in body.genres)
    return {"ok": True, "counts": {"liked_artists": len(rec["liked_artists"]), "liked_genres": len(rec["liked_genres"])}}

# -------------------------------------------------------------------
# Vibe parsing (heuristic and optional LLM)
# -------------------------------------------------------------------
class Era(BaseModel):
    frm: Optional[int] = None
    to: Optional[int] = None

class VibeParseIn(BaseModel):
    vibeText: str
    explicitAllowed: Optional[bool] = True

class VibeRules(BaseModel):
    includeGenres: List[str] = []
    excludeGenres: List[str] = []
    minPopularity: Optional[int] = None
    maxPopularity: Optional[int] = None
    era: Era = Era()
    explicitAllowed: bool = True

def heuristic_parse(vibe: str, explicit_allowed: bool = True) -> VibeRules:
    t = vibe.lower()
    genres = []
    if any(k in t for k in ["chill", "lofi", "study", "focus"]): genres.append("lofi")
    if "party" in t or "dance" in t: genres.append("edm")
    era = Era()
    if "2010" in t or "2010s" in t: era = Era(frm=2010, to=2019)
    if "no explicit" in t: explicit_allowed = False
    return VibeRules(
        includeGenres=list(set(genres)) or ["pop"],
        excludeGenres=[],
        minPopularity=None,
        maxPopularity=None,
        era=era,
        explicitAllowed=explicit_allowed,
    )

@app.post("/vibe/parse")
def vibe_parse(body: VibeParseIn) -> VibeRules:
    return heuristic_parse(body.vibeText, body.explicitAllowed)

@app.post("/vibe/parse_ai")
def vibe_parse_ai(body: VibeParseIn) -> VibeRules:
    if not GROQ_API_KEY:
        return heuristic_parse(body.vibeText, body.explicitAllowed)

    system_msg = (
        "Convert a music vibe request into STRICT JSON with keys: "
        "includeGenres (string[]), excludeGenres (string[]), "
        "minPopularity (int|null), maxPopularity (int|null), "
        "era {frm:int|null,to:int|null}, explicitAllowed (bool). Only return JSON."
    )
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f'vibeText="{body.vibeText}", explicitAllowed={str(body.explicitAllowed).lower()}'},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    with httpx.Client(timeout=15) as client:
        r = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
    data = json.loads(content) if content else {}
    era = data.get("era") or {}
    return VibeRules(
        includeGenres=data.get("includeGenres") or [],
        excludeGenres=data.get("excludeGenres") or [],
        minPopularity=data.get("minPopularity"),
        maxPopularity=data.get("maxPopularity"),
        era=Era(frm=era.get("frm"), to=era.get("to")),
        explicitAllowed=bool(data.get("explicitAllowed", True)),
    )

# -------------------------------------------------------------------
# User data helpers
# -------------------------------------------------------------------
@app.get("/me/top_artists")
async def top_artists(user: str, limit: int = 10):
    key = f"spotify:{user}"
    tokens = TOKEN_STORE.get(key)
    if not tokens:
        raise HTTPException(401, "not logged in")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get("https://api.spotify.com/v1/me/top/artists", params={"limit": limit}, headers=headers)
        if r.status_code == 401:
            raise HTTPException(401, "token expired; re-login at /auth/login")
        r.raise_for_status()
        items = r.json().get("items", [])
    return [{"id":a["id"], "name":a["name"], "genres":a.get("genres", []), "popularity":a.get("popularity")} for a in items]

# -------------------------------------------------------------------
# Re-ranking helpers
# -------------------------------------------------------------------
def target_audio_profile(vibe_text: str) -> dict:
    """Very small heuristic mapping vibe → target audio features."""
    t = vibe_text.lower()
    prof = {"target_energy": 0.5, "target_valence": 0.5, "target_danceability": 0.5}
    if "night drive" in t or "moody" in t: prof.update(target_energy=0.55, target_valence=0.35, target_danceability=0.6)
    if "chill" in t or "lofi" in t:       prof.update(target_energy=0.30, target_valence=0.50, target_danceability=0.5)
    if "party" in t or "dance" in t:      prof.update(target_energy=0.80, target_valence=0.70, target_danceability=0.8)
    if "happy" in t:                       prof.update(target_valence=0.80)
    return prof

def score_track(t: dict, af: dict | None, ctx: dict) -> float:
    """Combine artist overlap + taste memory + audio-feature closeness."""
    s = 0.0
    artist_names = [a.strip().lower() for a in t.get("artist","").split(",")]
    if any(a in ctx["top_artists"]   for a in artist_names): s += 2.0
    if any(a in ctx["liked_artists"] for a in artist_names): s += 1.5
    if af:
        pe, pv, pd = ctx["profile"]["target_energy"], ctx["profile"]["target_valence"], ctx["profile"]["target_danceability"]
        s += 1.0 - abs((af.get("energy", 0.5))       - pe)
        s += 1.0 - abs((af.get("valence", 0.5))      - pv)
        s += 1.0 - abs((af.get("danceability", 0.5)) - pd)
    return s

# Replace your existing fetch_audio_features with this safer version:

async def fetch_audio_features(token: str, ids: List[str]) -> Dict[str, dict]:
    """
    Batch-fetch audio features for track ids. Robust to Spotify 403/other errors:
    on any failure, returns {} so the caller can fall back to non-AF ranking.
    """
    af_map: Dict[str, dict] = {}
    if not ids:
        return af_map

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=15) as client:
        # Spotify allows up to 100 ids per call; chunk defensively
        for i in range(0, len(ids), 100):
            chunk = ids[i:i+100]
            try:
                r = await client.get(
                    "https://api.spotify.com/v1/audio-features",
                    params={"ids": ",".join(chunk)},
                    headers=headers,
                )
                # If token expired -> 401 (we still surface so caller can re-login)
                if r.status_code == 401:
                    raise HTTPException(401, "token expired; re-login at /auth/login")

                # If Spotify refuses (e.g., dev mode/user policy or odd ids) -> 403
                if r.status_code == 403:
                    # Log + degrade gracefully: just skip AF entirely
                    # (You can print/LOG here if you want visibility.)
                    return {}  # no AF, so ranking will rely on artist/taste

                r.raise_for_status()
                payload = r.json() or {}
                for x in payload.get("audio_features", []) or []:
                    if x and x.get("id"):
                        af_map[x["id"]] = x
            except Exception:
                # Any network/JSON hiccup -> degrade gracefully
                return {}

    return af_map


# -------------------------------------------------------------------
# LLM-assisted generation: vibe → track candidates (with re-ranking)
# -------------------------------------------------------------------
class LLMGenIn(BaseModel):
    user: str
    vibeText: str
    count: int = 20

@app.post("/vibe/generate_llm")
async def vibe_generate_llm(body: LLMGenIn):
    key = f"spotify:{body.user}"
    tokens = TOKEN_STORE.get(key)
    if not tokens:
        raise HTTPException(401, "not logged in; go to /auth/login first")
    headers_sp = {"Authorization": f"Bearer {tokens['access_token']}"}

    # 1) Context: user's top artists (keep small for prompt)
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get("https://api.spotify.com/v1/me/top/artists", params={"limit": 12}, headers=headers_sp)
        if r.status_code == 401: raise HTTPException(401, "token expired; re-login at /auth/login")
        r.raise_for_status()
        top_artists = [{"id":a["id"], "name":a["name"], "genres":a.get("genres", [])} for a in r.json().get("items", [])]

    # 2) Ask Groq (optional) for search suggestions
    suggestions: List[dict] = []
    if GROQ_API_KEY:
        system = (
            "You are a music assistant. Return JSON with key 'items' (array).\n"
            "Each item: {title:string, artist:string, query:string} where 'query' is suitable for Spotify text search.\n"
            "Focus on the vibe and artists/genres adjacent to the user's top artists. JSON only."
        )
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role":"system","content":system},
                {"role":"user","content":json.dumps({"vibe": body.vibeText, "top_artists": top_artists, "count": body.count})},
            ],
            "temperature": 0.4,
            "response_format": {"type":"json_object"},
        }
        headers_groq = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type":"application/json"}
        try:
            with httpx.Client(timeout=20) as c:
                resp = c.post("https://api.groq.com/openai/v1/chat/completions", headers=headers_groq, json=payload)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
            for x in (json.loads(content).get("items") or []):
                q = (x.get("query") or "").strip()
                if q:
                    suggestions.append({"title": x.get("title",""), "artist": x.get("artist",""), "query": q})
        except Exception:
            suggestions = []

    # Fallback if the LLM isn’t available/returns nothing
    if not suggestions:
        for a in top_artists[:12]:
            suggestions.append({"title":"", "artist":a["name"], "query": f'{a["name"]} {body.vibeText} -remix -live'})
    suggestions = suggestions[: max(5, body.count * 2)]

    # 3) Search Spotify, dedupe track ids
    results: List[dict] = []
    seen: set[str] = set()
    async with httpx.AsyncClient(timeout=15) as client:
        for s in suggestions:
            q = s["query"].replace('"','').strip()
            if not q:
                continue
            try:
                sr = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": q, "type": "track", "limit": 1, "market": "US"},
                    headers=headers_sp,
                )
                if sr.status_code == 401: raise HTTPException(401, "token expired; re-login at /auth/login")
                sr.raise_for_status()
                items = (sr.json().get("tracks") or {}).get("items", [])
                if not items:
                    continue
                t = items[0]
                tid = t["id"]
                if tid in seen:
                    continue
                seen.add(tid)
                results.append({
                    "id": tid,
                    "uri": t["uri"],
                    "name": t["name"],
                    "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                    "image": (t.get("album", {}).get("images", []) or [{}])[0].get("url",""),
                    "preview_url": t.get("preview_url"),
                })
                if len(results) >= max(body.count, 20):  # keep some headroom for re-rank cut
                    break
            except Exception:
                continue

    if not results:
        return {"vibe": body.vibeText, "count": 0, "tracks": []}

    # 4) Re-rank using audio-features + taste + top artists
    liked = USER_TASTE.get(key, {"liked_artists": set(), "liked_genres": set()})
    ctx = {
        "liked_artists": liked["liked_artists"],
        "top_artists":   set(a["name"].lower() for a in top_artists),
        "profile":       target_audio_profile(body.vibeText),
    }
    af_map = await fetch_audio_features(tokens["access_token"], [t["id"] for t in results])
    ranked = sorted(results, key=lambda t: score_track(t, af_map.get(t["id"]), ctx), reverse=True)
    ranked = ranked[: body.count]

    return {"vibe": body.vibeText, "count": len(ranked), "tracks": ranked}

# -------------------------------------------------------------------
# Playlist creation + one-click flow
# -------------------------------------------------------------------
class CreatePlaylistIn(BaseModel):
    user: str
    name: str
    description: Optional[str] = None
    public: bool = True
    trackUris: List[str]

@app.post("/playlist/create_from_tracks")
async def create_playlist_from_tracks(body: CreatePlaylistIn):
    key = f"spotify:{body.user}"
    tokens = TOKEN_STORE.get(key)
    if not tokens:
        raise HTTPException(401, "not logged in; visit /auth/login first")

    headers_sp = {"Authorization": f"Bearer {tokens['access_token']}", "Content-Type": "application/json"}

    # 1) Create playlist
    async with httpx.AsyncClient(timeout=15) as client:
        c_resp = await client.post(
            f"https://api.spotify.com/v1/users/{body.user}/playlists",
            headers=headers_sp,
            json={"name": body.name, "description": body.description or "", "public": body.public},
        )
        if c_resp.status_code == 401: raise HTTPException(401, "token expired; please re-login at /auth/login")
        c_resp.raise_for_status()
        pl = c_resp.json()
        playlist_id = pl["id"]
        playlist_url = (pl.get("external_urls", {}) or {}).get("spotify", "")

    # 2) Add tracks
    uris = [u for u in body.trackUris if u.startswith("spotify:track:")]
    if uris:
        async with httpx.AsyncClient(timeout=15) as client:
            for i in range(0, len(uris), 100):
                chunk = uris[i:i+100]
                add_resp = await client.post(
                    f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                    headers=headers_sp,
                    json={"uris": chunk},
                )
                if add_resp.status_code == 401: raise HTTPException(401, "token expired; please re-login at /auth/login")
                add_resp.raise_for_status()

    return {"playlistId": playlist_id, "url": playlist_url, "added": len(uris)}

class OneClickIn(BaseModel):
    user: str
    vibeText: str
    count: int = 20
    name: Optional[str] = None
    public: bool = True
    description: Optional[str] = None

@app.post("/vibe/one_click_playlist")
async def one_click_playlist(body: OneClickIn):
    # Generate tracks
    gen = await vibe_generate_llm(LLMGenIn(user=body.user, vibeText=body.vibeText, count=body.count))
    if gen["count"] == 0:
        raise HTTPException(502, "no tracks found for this vibe; try different wording")
    uris = [t["uri"] for t in gen["tracks"] if t.get("uri", "").startswith("spotify:track:")]

    pl_name = body.name or f"{body.vibeText} – {time.strftime('%Y-%m-%d %H:%M')}"
    created = await create_playlist_from_tracks(
        CreatePlaylistIn(
            user=body.user,
            name=pl_name,
            description=body.description or f"Generated by our app for vibe: {body.vibeText}",
            public=body.public,
            trackUris=uris,
        )
    )
    return {"url": created["url"], "count": created["added"], "name": pl_name}
