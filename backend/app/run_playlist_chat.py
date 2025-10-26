"""
Entry point for the playlist chat CLI.

Usage:
  1. Ensure your FastAPI backend is running.
  2. Activate your Python virtual environment.
  3. Optionally set SPOTIFY_UID in the environment.
  4. Run: python run_playlist_chat.py
"""

import os
from playlist_chat import interactive_session

def main() -> None:
    # Optionally override the UID in playlist_chat via env var
    env_uid = os.environ.get("SPOTIFY_UID")
    if env_uid:
        import playlist_chat  # type: ignore
        playlist_chat.UID = env_uid
        print(f"Overriding UID with environment value: {env_uid}")
    interactive_session()

if __name__ == "__main__":
    main()
