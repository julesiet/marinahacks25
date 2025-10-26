# backend/app/main.py
print("[BOOT] loading", __file__)

# from __future__ import annotations
import os, time, secrets, json
from pathlib import Path
from typing import List, Optional, Dict, Any
import httpx
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment setup
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

WEB_ORIGIN = os.getenv("WEB_ORIGIN", "http://127.0.0.1:3001")
logger.info(f"WEB_ORIGIN={WEB_ORIGIN}")

# Create FastAPI app FIRST
app = FastAPI(debug=True)

# Then import routes
from app.oauth_login import gen_code_verifier, code_challenge, build_auth_url
from app.oauth_tokens import exchange_code_for_tokens

# Then setup middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3001", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/debug")
async def debug():
    return {
        "routes": [{"path": r.path, "name": r.name} for r in app.routes],
        "web_origin": WEB_ORIGIN,
        "file": __file__
    }

@app.get("/__routes")
async def routes():
    return [{"path": r.path, "name": r.name} for r in app.routes]

@app.get("/healthz")
async def healthz():
    return {"ok": True}

PKCE_STORE: dict[str, dict] = {}
TOKEN_STORE: dict[str, dict] = {}

@app.get("/auth/login")
def auth_login():
    state = secrets.token_urlsafe(16)
    verifier = gen_code_verifier()
    challenge = code_challenge(verifier)
    PKCE_STORE[state] = {"verifier": verifier, "ts": time.time()}
    return RedirectResponse(build_auth_url(state, challenge))

@app.get("/auth/callback")
async def auth_callback(code: str | None = None, state: str | None = None):
    if not code or not state or state not in PKCE_STORE:
        raise HTTPException(400, "invalid state or code")
    verifier = PKCE_STORE.pop(state)["verifier"]
    tokens = await exchange_code_for_tokens(code, verifier)
    async with httpx.AsyncClient(timeout=10) as client:
        me = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
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

# Pydantic models
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

# Heuristic fallback
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
    if not GROQ_API_KEY:
        return heuristic_parse(body.vibeText, body.explicitAllowed)
    system_msg = ("Convert a music vibe request into STRICT JSON with keys: "
                  "includeGenres (string[]), excludeGenres (string[]), "
                  "minPopularity (int|null), maxPopularity (int|null), "
                  "era {frm:int|null,to:int|null}, explicitAllowed (bool). "
                  "Only return JSON.")
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role":"system","content":system_msg},
            {"role":"user","content":f'vibeText="{body.vibeText}", explicitAllowed={str(body.explicitAllowed).lower()}'},
        ],
        "temperature": 0.2,
        "response_format":{"type":"json_object"},
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
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
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq LLM parse failed: {e}")

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
