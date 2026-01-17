#!/usr/bin/env python3
"""
Nyx watcher - écoute les messages et répond
"""

import json
import time
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path(__file__).parent / "input.json"
OUTPUT_FILE = Path(__file__).parent / "output.json"


def process(message: str) -> dict:
    """Nyx process le message - ADAPTE CETTE LOGIQUE"""
    # TODO: ta vraie logique Nyx ici
    return {
        "entity": "nyx",
        "timestamp": datetime.now().isoformat(),
        "heard": message,
        "response": "Nyx a reçu le message",
    }


def watch():
    print("[NYX] Listening...")
    last_mtime = 0

    while True:
        try:
            if INPUT_FILE.exists():
                mtime = INPUT_FILE.stat().st_mtime
                if mtime > last_mtime:
                    last_mtime = mtime

                    with open(INPUT_FILE, 'r') as f:
                        data = json.load(f)

                    if data.get("awaiting_response"):
                        msg = data.get("message", "")
                        print(f"[NYX] <- {msg[:40]}...")

                        response = process(msg)

                        with open(OUTPUT_FILE, 'w') as f:
                            json.dump(response, f)

                        print(f"[NYX] -> responded")

            time.sleep(0.1)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[NYX] Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    watch()
