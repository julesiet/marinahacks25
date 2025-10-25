from pathlib import Path
from dotenv import load_dotenv
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
print("[ENV DEBUG] looking for:", ENV_PATH, "exists=", ENV_PATH.exists())
load_dotenv(dotenv_path=ENV_PATH, override=True)

import os, time, secrets, httpx
print("[ENV DEBUG] CLIENT_ID first6:", (os.getenv("SPOTIFY_CLIENT_ID") or "None")[:6])
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.oauth_login import gen_code_verifier, code_challenge, build_auth_url
from app.oauth_tokens import exchange_code_for_tokens

# explicitly load ../.env so env vars are present even when running from app/
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("WEB_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PKCE_STORE: dict[str, dict] = {}   # state -> {verifier, ts}
TOKEN_STORE: dict[str, dict] = {}  # user_key -> tokens + user

@app.get("/healthz")
def healthz():
    return {"ok": True}

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

    user_key = f"spotify:{user['id']}"
    TOKEN_STORE[user_key] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "exp_ts": time.time() + tokens.get("expires_in", 3600),
        "user": {"id": user["id"], "display_name": user.get("display_name")},
    }
    return RedirectResponse(f"{os.getenv('WEB_ORIGIN','http://localhost:3000')}/?user={user['id']}")