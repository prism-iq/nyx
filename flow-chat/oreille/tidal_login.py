#!/usr/bin/env python3
import tidalapi
import json
import sys
from pathlib import Path

session = tidalapi.Session()
login, future = session.login_oauth()

print(login.verification_uri_complete, flush=True)

try:
    future.result(timeout=180)
    if session.check_login():
        session_file = Path("/opt/flow-chat/adn/music/tidal_session.json")
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(json.dumps({
            "token_type": session.token_type,
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expiry_time": session.expiry_time.isoformat() if session.expiry_time else None
        }))
        print(f"OK:{session.user.name}", flush=True)
        sys.exit(0)
except Exception as e:
    print(f"ERR:{e}", flush=True)
    sys.exit(1)
