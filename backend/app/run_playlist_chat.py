import os
from playlist_chat import interactive_session

def main() -> None:
    # optionally override the UID in playlist_chat via env var
    env_uid = os.environ.get("SPOTIFY_UID")
    if env_uid:
        import playlist_chat  # type: ignore
        playlist_chat.UID = env_uid
        print(f"Overriding UID with environment value: {env_uid}")
    interactive_session()

if __name__ == "__main__":
    main()
