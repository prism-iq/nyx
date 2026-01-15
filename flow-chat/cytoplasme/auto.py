#!/usr/bin/env python3
"""auto.py - Mode auto pour Flow
Défile toutes les 10 sec. Espace pour pause/resume. Q pour quit.
"""

import time
import json
import sys
import select
import termios
import tty
import requests
from pathlib import Path
from datetime import datetime

RESULTS = Path("/opt/flow-chat/adn/RESULTS.md")
DREAMS = Path("/opt/flow-chat/adn/dreams.md")
THOUGHTS = Path("/opt/flow-chat/adn/thoughts.jsonl")

# état
paused = False
last_results = 0
last_dreams = 0
last_thoughts = 0

# couleurs
C = {
    'reset': '\033[0m',
    'dim': '\033[2m',
    'cyan': '\033[36m',
    'yellow': '\033[33m',
    'green': '\033[32m',
    'magenta': '\033[35m'
}

def ts():
    return datetime.now().strftime("%H:%M:%S")

def clear_line():
    print('\033[2K\r', end='')

def get_key():
    """non-blocking key read"""
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None

def get_new(file, last_size):
    """get new content from file"""
    if not file.exists():
        return None, last_size
    size = file.stat().st_size
    if size <= last_size:
        return None, last_size
    content = file.read_text()[last_size:]
    return content, size

def fmt(text, max_len=100):
    """clean and truncate"""
    text = text.replace('\n', ' ').strip()
    if len(text) > max_len:
        text = text[:max_len] + '...'
    return text

def show_status():
    status = "⏸ PAUSE" if paused else "▶ AUTO"
    print(f"\r{C['dim']}[{ts()}] {status} (espace=toggle, q=quit){C['reset']}", end='', flush=True)

def check_updates():
    global last_results, last_dreams, last_thoughts

    # shell results
    new, last_results = get_new(RESULTS, last_results)
    if new:
        # extract last command result
        lines = [l for l in new.split('\n') if l.strip() and not l.startswith('#')]
        for line in lines[-3:]:
            clean = fmt(line)
            if clean and not clean.startswith('```'):
                print(f"\r{C['cyan']}  $ {clean}{C['reset']}")

    # dreams
    new, last_dreams = get_new(DREAMS, last_dreams)
    if new:
        for line in new.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"\r{C['magenta']}  💭 {fmt(line)}{C['reset']}")

    # thoughts
    new, last_thoughts = get_new(THOUGHTS, last_thoughts)
    if new:
        for line in new.strip().split('\n'):
            if line.strip():
                try:
                    t = json.loads(line)
                    thought = t.get('thought', '')
                    if thought and len(thought) > 20:
                        print(f"\r{C['yellow']}  → {fmt(thought, 80)}{C['reset']}")
                except Exception:
                    pass

def trigger_thought():
    """trigger a thought from flow"""
    try:
        requests.post("http://localhost:8091/think",
                     json={"prompt": "une pensée rapide"},
                     timeout=30)
    except Exception:
        pass

def main():
    global paused

    # setup terminal
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())

        print(f"{C['green']}=== FLOW AUTO MODE ==={C['reset']}")
        print(f"{C['dim']}Intervalle: 10s | Espace: pause | Q: quit{C['reset']}")
        print()

        # init file sizes
        global last_results, last_dreams, last_thoughts
        if RESULTS.exists(): last_results = RESULTS.stat().st_size
        if DREAMS.exists(): last_dreams = DREAMS.stat().st_size
        if THOUGHTS.exists(): last_thoughts = THOUGHTS.stat().st_size

        last_trigger = time.time()

        while True:
            # check keyboard
            key = get_key()
            if key:
                if key == ' ':
                    paused = not paused
                    clear_line()
                    status = "⏸ PAUSED" if paused else "▶ RUNNING"
                    print(f"\r{C['green']}{status}{C['reset']}")
                elif key.lower() == 'q':
                    break

            # check updates (always, even when paused)
            check_updates()

            # trigger thought every 10s if not paused
            if not paused and time.time() - last_trigger >= 10:
                trigger_thought()
                last_trigger = time.time()
                print(f"\r{C['dim']}[{ts()}] ping...{C['reset']}")

            show_status()
            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print(f"\n{C['dim']}bye{C['reset']}")

if __name__ == "__main__":
    main()
