# app/oauth_login.py
import os, base64, hashlib, secrets
from urllib.parse import urlencode

AUTH_URL = "https://accounts.spotify.com/authorize"

def gen_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("=")

def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")

def build_auth_url(state: str, challenge: str) -> str:
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
    SCOPES = os.getenv("SCOPES", "")

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "show_dialog": "false",
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    print("[AUTH DEBUG] CLIENT_ID =", CLIENT_ID)
    print("[AUTH DEBUG] REDIRECT_URI =", REDIRECT_URI)
    return url
