import os, httpx

TOKEN_URL = "https://accounts.spotify.com/api/token"
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET") 
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

async def exchange_code_for_tokens(code: str, verifier: str):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
        "client_secret": CLIENT_SECRET,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(TOKEN_URL, data=data)
        r.raise_for_status()
        return r.json()  # {access_token, refresh_token, expires_in, ...}
