# backend/app/main.py
from __future__ import annotations
import os, time, secrets, json
from pathlib import Path
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional

# --- Load environment variables
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)
WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://localhost:3000")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:3001/auth/callback")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# --- Create the app once
app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Simple in-memory stores for PKCE and tokens
PKCE_STORE: dict[str, dict] = {}
TOKEN_STORE: dict[str, dict] = {}

# --- Health route
@app.get("/healthz")
def healthz():
    return {"ok": True}

# --- Debug route to see which paths are registered
@app.get("/__routes")
def __routes():
    return [r.path for r in app.router.routes]

# --- Lazy-import Spotify OAuth helpers so routes always register
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

# --- Data models for vibe parsing
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
    if any(k in t for k in ["chill","lofi","study","focus"]): genres.append("lofi")
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
    # Fallback to heuristic if no Groq key
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
            {"role":"system","content":system_msg},
            {"role":"user","content":f'vibeText=\"{body.vibeText}\", explicitAllowed={str(body.explicitAllowed).lower()}'},
        ],
        "temperature": 0.2,
        "response_format":{"type":"json_object"},
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    with httpx.Client(timeout=15) as client:
        r = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    era_data = data.get("era") or {}
    return VibeRules(
        includeGenres=data.get("includeGenres") or [],
        excludeGenres=data.get("excludeGenres") or [],
        minPopularity=data.get("minPopularity"),
        maxPopularity=data.get("maxPopularity"),
        era=Era(frm=era_data.get("frm"), to=era_data.get("to")),
        explicitAllowed=bool(data.get("explicitAllowed", True)),
    )

# --- Simple mock track generator (replace with real Spotify logic later)
@app.post("/vibe/generate")
def vibe_generate(rules: VibeRules):
    sample_tracks = [
        {"name":"Coffee & Code","artist":"Chillhop Lab","genre":"lofi","uri":"spotify:track:3","year":2013},
        {"name":"Neon Floor","artist":"Club Circuit","genre":"edm","uri":"spotify:track:4","year":2016},
        {"name":"Soft Echoes","artist":"Bedroom Bloom","genre":"indie","uri":"spotify:track:6","year":2011},
        {"name":"Sunset Boardwalk","artist":"Indigo Waves","genre":"indie","uri":"spotify:track:2","year":2015},
    ]
    filtered = [t for t in sample_tracks if t["genre"] in rules.includeGenres] or sample_tracks
    return {"tracks": filtered[:20]}

# --- Test endpoint: fetch top 10 artists for a logged-in user (requires Spotify tokens)
@app.get("/me/top_artists")
async def top_artists(user: str, limit: int = 10):
    key = f"spotify:{user}"
    tokens = TOKEN_STORE.get(key)
    if not tokens:
        raise HTTPException(401, "not logged in")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://api.spotify.com/v1/me/top/artists?limit={limit}",
            headers=headers,
        )
        r.raise_for_status()
        items = r.json().get("items", [])
    return [
        {
            "id": artist["id"],
            "name": artist["name"],
            "genres": artist.get("genres", []),
            "popularity": artist.get("popularity"),
        }
        for artist in items
    ]

from pydantic import BaseModel

class LLMGenIn(BaseModel):
    user: str
    vibeText: str
    count: int = 20

@app.post("/vibe/generate_llm")
async def vibe_generate_llm(body: LLMGenIn):
    user_key = f"spotify:{body.user}"
    tokens = TOKEN_STORE.get(user_key)
    if not tokens:
        raise HTTPException(401, "not logged in; go to /auth/login first")

    headers_sp = {"Authorization": f"Bearer {tokens['access_token']}"}
    async with httpx.AsyncClient(timeout=15) as client:
        # 1) pull top artists (keep it small to fit in prompt)
        r = await client.get("https://api.spotify.com/v1/me/top/artists?limit=12", headers=headers_sp)
        if r.status_code == 401:
            raise HTTPException(401, "token expired; re-login at /auth/login")
        r.raise_for_status()
        top_artists = [{"id":a["id"], "name":a["name"], "genres":a.get("genres", [])} for a in r.json().get("items", [])]

    # 2) ask Groq for structured suggestions
    suggestions = []
    if GROQ_API_KEY:
        system = (
            "You are a music assistant. Produce a JSON object with key 'items' = array of suggestions.\n"
            "Each suggestion must be: {title:string, artist:string, query:string}.\n"
            "The 'query' should be suitable for Spotify text search to find a track.\n"
            "Keep it focused on the given vibe and the user's top artists/adjacent genres. No commentary, JSON only."
        )
        user_msg = {
            "vibe": body.vibeText,
            "top_artists": top_artists,
            "count": body.count
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role":"system","content":system},
                {"role":"user","content":json.dumps(user_msg)}
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
            data = json.loads(content)
            raw = data.get("items") or []
            # Normalize and cap
            for x in raw:
                q = (x.get("query") or "").strip()
                if q:
                    suggestions.append({"title": x.get("title",""), "artist": x.get("artist",""), "query": q})
            suggestions = suggestions[: max(5, body.count * 2)]  # extra to allow dedupe
        except Exception as e:
            # graceful fallback
            suggestions = []

    # 3) fallback suggestions if no LLM or it failed
    if not suggestions:
        # simple heuristic: for each top artist, build a query with the vibe text
        base = [a["name"] for a in top_artists]
        for name in base:
            suggestions.append({"title":"", "artist":name, "query": f'{name} {body.vibeText}  -remix -live'})
        suggestions = suggestions[: max(5, body.count * 2)]

    # 4) Spotify Search for each suggestion, collect unique tracks
    results = []
    seen_ids = set()
    async with httpx.AsyncClient(timeout=15) as client:
        for s in suggestions:
            q = s["query"]
            # keep the query tidy and short
            q = q.replace('"','').strip()
            if not q:
                continue
            try:
                sr = await client.get(
                    "https://api.spotify.com/v1/search",
                    params={"q": q, "type": "track", "limit": 1, "market": "US"},
                    headers=headers_sp,
                )
                if sr.status_code == 401:
                    raise HTTPException(401, "token expired; re-login at /auth/login")
                sr.raise_for_status()
                items = (sr.json().get("tracks") or {}).get("items", [])
                if not items:
                    continue
                t = items[0]
                tid = t["id"]
                if tid in seen_ids:
                    continue
                seen_ids.add(tid)
                results.append({
                    "id": tid,
                    "uri": t["uri"],
                    "name": t["name"],
                    "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                    "image": (t.get("album", {}).get("images", []) or [{}])[0].get("url",""),
                    "preview_url": t.get("preview_url"),
                })
                if len(results) >= body.count:
                    break
            except Exception:
                continue

    return {"vibe": body.vibeText, "count": len(results), "tracks": results}

from pydantic import BaseModel

class CreatePlaylistIn(BaseModel):
    user: str
    name: str
    description: str | None = None
    public: bool = True
    trackUris: list[str]

@app.post("/playlist/create_from_tracks")
async def create_playlist_from_tracks(body: CreatePlaylistIn):
    key = f"spotify:{body.user}"
    tokens = TOKEN_STORE.get(key)
    if not tokens:
        raise HTTPException(401, "not logged in; visit /auth/login first")

    headers_sp = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Content-Type": "application/json",
    }

    # 1) Create playlist
    async with httpx.AsyncClient(timeout=15) as client:
        c_resp = await client.post(
            f"https://api.spotify.com/v1/users/{body.user}/playlists",
            headers=headers_sp,
            json={
                "name": body.name,
                "description": body.description or "",
                "public": body.public,
            },
        )
        if c_resp.status_code == 401:
            raise HTTPException(401, "token expired; please re-login at /auth/login")
        c_resp.raise_for_status()
        pl = c_resp.json()
        playlist_id = pl["id"]
        playlist_url = (pl.get("external_urls", {}) or {}).get("spotify", "")

    # 2) Add tracks (batch up to 100)
    uris = [u for u in body.trackUris if u.startswith("spotify:track:")]
    if uris:
        async with httpx.AsyncClient(timeout=15) as client:
            for i in range(0, len(uris), 100):
                chunk = uris[i : i + 100]
                add_resp = await client.post(
                    f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
                    headers=headers_sp,
                    json={"uris": chunk},
                )
                if add_resp.status_code == 401:
                    raise HTTPException(401, "token expired; please re-login at /auth/login")
                add_resp.raise_for_status()

    return {"playlistId": playlist_id, "url": playlist_url, "added": len(uris)}
