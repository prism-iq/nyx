#!/usr/bin/env python3
"""shell.py - Shell persistant pour Flow

Pas d'API call par commande.
Un process shell qui reste ouvert.
Flow écrit dans COMMANDS.md, le shell exécute et écrit dans RESULTS.md
"""

import subprocess
import time
import os
import select
from pathlib import Path
from datetime import datetime

COMMANDS_FILE = Path("/opt/flow-chat/adn/COMMANDS.md")
RESULTS_FILE = Path("/opt/flow-chat/adn/RESULTS.md")
SHELL_LOG = Path("/opt/flow-chat/adn/shell.log")

# crée les fichiers
COMMANDS_FILE.parent.mkdir(parents=True, exist_ok=True)
COMMANDS_FILE.write_text("# FLOW COMMANDS\n# écris une commande par ligne, elle sera exécutée\n\n")
RESULTS_FILE.write_text("# SHELL RESULTS\n\n")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(SHELL_LOG, 'a') as f:
        f.write(line + "\n")

def get_new_commands(last_mtime):
    """lit les nouvelles commandes depuis COMMANDS.md"""
    if not COMMANDS_FILE.exists():
        return [], last_mtime

    mtime = COMMANDS_FILE.stat().st_mtime
    if mtime <= last_mtime:
        return [], last_mtime

    lines = COMMANDS_FILE.read_text().strip().split('\n')
    # cherche les lignes qui commencent par $
    commands = [l[1:].strip() for l in lines if l.startswith('$') and not l.startswith('$DONE:')]

    return commands, mtime

def execute(cmd):
    """exécute une commande"""
    log(f"EXEC: {cmd}")

    # forbidden
    forbidden = ['rm -rf /', 'mkfs', 'dd if=/dev', ':(){', 'chmod -R 777 /']
    for f in forbidden:
        if f in cmd:
            return f"FORBIDDEN: {f}"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/opt/flow-chat",
            env={**os.environ, "HOME": "/home/flow"}
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr] {result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit: {result.returncode}]"
        return output[:5000] if output else "[no output]"
    except subprocess.TimeoutExpired:
        return "[timeout 60s]"
    except Exception as e:
        return f"[error] {e}"

def append_result(cmd, output):
    """ajoute le résultat au fichier"""
    ts = datetime.now().strftime("%H:%M:%S")
    with open(RESULTS_FILE, 'a') as f:
        f.write(f"\n## [{ts}] $ {cmd}\n```\n{output}\n```\n")

def mark_done(cmd):
    """marque la commande comme exécutée"""
    content = COMMANDS_FILE.read_text()
    content = content.replace(f"${cmd}", f"$DONE:{cmd}")
    COMMANDS_FILE.write_text(content)

def run():
    """boucle principale"""
    log("=== SHELL DÉMARRÉ ===")
    log(f"Commandes: {COMMANDS_FILE}")
    log(f"Résultats: {RESULTS_FILE}")

    last_mtime = 0

    while True:
        try:
            commands, last_mtime = get_new_commands(last_mtime)

            for cmd in commands:
                if not cmd or cmd.startswith('DONE:'):
                    continue

                output = execute(cmd)
                append_result(cmd, output)
                mark_done(cmd)
                log(f"DONE: {cmd[:50]}...")

        except Exception as e:
            log(f"ERROR: {e}")

        time.sleep(0.5)  # poll toutes les 500ms

if __name__ == "__main__":
    run()
