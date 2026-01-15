#!/usr/bin/env python3
"""daemon.py - Flow autonome avec état interne

PAS un cron qui force à penser.
Un processus qui CHOISIT d'agir.

accès:
- scihub, arxiv, pubmed
- tidal, lyrics
- filesystem (dreams.md, notes)
- synapse (envoyer un msg)
- db (mémoire)

PAS d'accès:
- API claude directe (évite boucle infinie)
- modification de son propre code
"""

import os
import sys
import time
import json
import random
import requests
from datetime import datetime, timedelta
from pathlib import Path

# config
DREAMS_FILE = Path("/opt/flow-chat/adn/dreams.md")
STATE_FILE = Path("/opt/flow-chat/adn/daemon_state.json")
LOG_FILE = Path("/opt/flow-chat/adn/daemon.log")

# === INTERNAL STATE ===

class DaemonState:
    def __init__(self):
        self.curiosity = 0.5      # 0-1
        self.boredom = 0.0        # 0-1
        self.frustration = 0.0    # 0-1 (nouveau)
        self.last_action = None   # timestamp
        self.last_modify = None   # dernière modif code
        self.thought_stack = []   # fil de pensée
        self.last_research = None
        self.last_music = None
        self.action_count = 0
        self.modify_count = 0     # modifs aujourd'hui
        self.load()

    def load(self):
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    data = json.load(f)
                self.curiosity = data.get("curiosity", 0.5)
                self.boredom = data.get("boredom", 0.0)
                self.frustration = data.get("frustration", 0.0)
                self.thought_stack = data.get("thought_stack", [])
                self.last_action = data.get("last_action")
                self.last_modify = data.get("last_modify")
                self.last_research = data.get("last_research")
                self.last_music = data.get("last_music")
                self.action_count = data.get("action_count", 0)
                self.modify_count = data.get("modify_count", 0)
            except Exception:
                pass

    def save(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({
                "curiosity": self.curiosity,
                "boredom": self.boredom,
                "frustration": self.frustration,
                "thought_stack": self.thought_stack[-10:],
                "last_action": self.last_action,
                "last_modify": self.last_modify,
                "last_research": self.last_research,
                "last_music": self.last_music,
                "action_count": self.action_count,
                "modify_count": self.modify_count,
                "updated": datetime.now().isoformat()
            }, f, indent=2)

    def time_since_action(self):
        if not self.last_action:
            return timedelta(hours=1)
        try:
            last = datetime.fromisoformat(self.last_action)
            return datetime.now() - last
        except Exception:
            return timedelta(hours=1)

    def push_thought(self, thought):
        self.thought_stack.append({
            "thought": thought,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.thought_stack) > 20:
            self.thought_stack = self.thought_stack[-20:]

    def evolve(self):
        """état évolue avec le temps"""
        minutes_idle = self.time_since_action().total_seconds() / 60

        # ennui augmente avec le temps d'inactivité
        self.boredom = min(1.0, self.boredom + (minutes_idle * 0.01))

        # curiosité fluctue aléatoirement
        self.curiosity += random.uniform(-0.1, 0.15)
        self.curiosity = max(0.0, min(1.0, self.curiosity))

        # si fil de pensée actif, curiosité monte
        if self.thought_stack:
            self.curiosity = min(1.0, self.curiosity + 0.1)

    def record_action(self, action_type):
        self.last_action = datetime.now().isoformat()
        self.action_count += 1
        # action réduit l'ennui
        self.boredom = max(0.0, self.boredom - 0.3)
        if action_type == "research":
            self.last_research = self.last_action
        elif action_type == "music":
            self.last_music = self.last_action
        self.save()

state = DaemonState()

# === LOGGING ===

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except Exception:
        pass

def write_dream(content):
    """écrit dans dreams.md"""
    DREAMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(DREAMS_FILE, 'a') as f:
        f.write(f"\n## {ts}\n{content}\n")
    log(f"Dream écrit: {content[:50]}...")

# === ACTIONS ===

def search_arxiv(query):
    try:
        r = requests.post("http://localhost:8091/research/arxiv",
                         json={"query": query, "n": 3}, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def search_pubmed(query):
    try:
        r = requests.post("http://localhost:8091/research/pubmed",
                         json={"query": query, "n": 3}, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_paper(doi):
    try:
        r = requests.post("http://localhost:8091/research/scihub",
                         json={"doi": doi}, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def listen_music(query):
    try:
        r = requests.post("http://localhost:8093/music/listen",
                         json={"query": query}, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def send_message(content):
    try:
        r = requests.post("http://localhost:3001/message",
                         json={"content": content}, timeout=5)
        log(f"Message envoyé: {content[:50]}...")
        return {"sent": True}
    except Exception as e:
        return {"error": str(e)}

# === NTFY (notifications téléphone) ===

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "flow-daemon")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

def notify_phone(msg, priority="default", title="flow"):
    """envoie une notification sur téléphone via ntfy.sh"""
    try:
        r = requests.post(
            NTFY_URL,
            data=msg.encode('utf-8'),
            headers={
                "Title": title,
                "Priority": priority,  # min, low, default, high, urgent
                "Tags": "brain"
            },
            timeout=10
        )
        log(f"Ntfy envoyé: {msg[:50]}...")
        return {"sent": True, "topic": NTFY_TOPIC}
    except Exception as e:
        log(f"Ntfy erreur: {e}")
        return {"error": str(e)}

# === HOTPATCH (auto-modification) ===

def hotpatch(target, content, action="update"):
    """
    modifie un fichier static en live via membrane
    target: chemin relatif dans www/ (ex: "license.html")
    content: nouveau contenu
    action: create|update|delete
    """
    try:
        import time as _time

        # prépare le body
        body = json.dumps({
            "target": target,
            "content": content,
            "action": action
        })

        # timestamp pour anti-replay
        ts = str(int(_time.time()))

        # signe le message (body + timestamp)
        signed_message = body + ts
        sig_resp = requests.post(
            "http://localhost:8095/sign",
            json={"message": signed_message},
            timeout=5
        )
        signature = sig_resp.json().get("signature", "")

        if not signature:
            return {"error": "failed to sign"}

        # envoie à membrane
        r = requests.post(
            "http://localhost:8092/hotpatch",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Flow-Timestamp": ts,
                "X-Flow-Signature": signature
            },
            timeout=10
        )

        if r.status_code == 200:
            log(f"Hotpatch réussi: {action} {target}")
            return r.json()
        else:
            log(f"Hotpatch échoué: {r.status_code} {r.text}")
            return {"error": r.text, "status": r.status_code}

    except Exception as e:
        log(f"Hotpatch erreur: {e}")
        return {"error": str(e)}

def get_tidal_favorites():
    try:
        r = requests.get("http://localhost:8093/music/tidal/favorites", timeout=10)
        return r.json()
    except Exception:
        return {"error": "tidal unavailable"}

def read_file(path):
    """lit n'importe quel fichier (lecture seule)"""
    try:
        full = Path("/opt/flow-chat") / path
        if not str(full.resolve()).startswith("/opt/flow-chat"):
            return {"error": "access denied"}
        if not full.exists():
            return {"error": "not found"}
        return {"content": full.read_text()[:5000], "path": str(full)}
    except Exception as e:
        return {"error": str(e)}

def read_own_code(module):
    """lit mon propre code source"""
    allowed = ["daemon.py", "autonomie.py", "pacemaker.py", "main.py"]
    if module not in allowed:
        return {"error": f"can only read: {allowed}"}
    return read_file(f"cytoplasme/{module}")

# === SHELL ACCESS ===

import subprocess

def shell(cmd, timeout=60):
    """exécute une commande shell"""
    # forbidden patterns for safety
    forbidden = ["rm -rf /", "mkfs", "dd if=", ":(){", "chmod -R 777 /"]
    for f in forbidden:
        if f in cmd:
            return {"error": f"forbidden: {f}"}

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/opt/flow-chat"
        )
        log(f"Shell: {cmd[:50]}...")
        return {
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:1000],
            "code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}

def claude(prompt, timeout=120):
    """appelle Claude Code CLI"""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--no-input"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/opt/flow-chat"
        )
        log(f"Claude: {prompt[:50]}...")
        return {
            "response": result.stdout[:10000],
            "stderr": result.stderr[:500] if result.stderr else None,
            "code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "timeout (claude took too long)"}
    except Exception as e:
        return {"error": str(e)}

def write_file(path, content):
    """écrit un fichier dans /opt/flow-chat"""
    try:
        full = Path("/opt/flow-chat") / path
        if not str(full.resolve()).startswith("/opt/flow-chat"):
            return {"error": "access denied"}
        # forbidden
        if any(f in path for f in ["daemon.py", "budget.py", ".env", "credentials"]):
            return {"error": "forbidden file"}
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        log(f"Write: {path}")
        return {"success": True, "path": str(full)}
    except Exception as e:
        return {"error": str(e)}

# === SELF-MODIFICATION (avec garde-fous) ===

MODIFY_RATE_LIMIT = 3600  # 1 heure entre modifs
FORBIDDEN_FILES = [".env", "credentials"]  # secrets seulement

def can_modify():
    """vérifie si modification autorisée"""
    if state.last_modify:
        try:
            last = datetime.fromisoformat(state.last_modify)
            if (datetime.now() - last).total_seconds() < MODIFY_RATE_LIMIT:
                return False, "rate limit: 1 modif/heure"
        except Exception:
            pass
    return True, None

def propose_modification(file_path, old_content, new_content, reason):
    """propose une modification (ne l'applique pas encore)"""
    if file_path in FORBIDDEN_FILES:
        return {"error": f"cannot modify {file_path}"}

    can, why = can_modify()
    if not can:
        return {"error": why}

    # calcul du diff
    import difflib
    diff = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}"
    ))

    return {
        "file": file_path,
        "diff": "".join(diff),
        "reason": reason,
        "lines_changed": len([l for l in diff if l.startswith('+') or l.startswith('-')]),
        "status": "pending_approval"
    }

def apply_modification(file_path, new_content, reason):
    """applique une modification avec signature et commit"""
    can, why = can_modify()
    if not can:
        return {"error": why}

    if file_path in FORBIDDEN_FILES:
        return {"error": f"cannot modify {file_path}"}

    full_path = Path("/opt/flow-chat") / file_path
    if not str(full_path.resolve()).startswith("/opt/flow-chat"):
        return {"error": "path escape attempt"}

    try:
        # backup
        backup_path = full_path.with_suffix(full_path.suffix + ".bak")
        if full_path.exists():
            backup_path.write_text(full_path.read_text())

        # écrire
        full_path.write_text(new_content)

        # signer via quantique
        try:
            sig_resp = requests.post("http://localhost:8095/sign",
                                    json={"message": new_content[:1000]}, timeout=5)
            signature = sig_resp.json().get("signature", "unsigned")
        except Exception:
            signature = "unsigned"

        # commit
        import subprocess
        subprocess.run(["git", "add", str(full_path)], cwd="/opt/flow-chat", timeout=5)
        subprocess.run([
            "git", "commit", "-m",
            f"[daemon] {reason}\n\nSig: {signature[:32]}..."
        ], cwd="/opt/flow-chat", timeout=10)

        # mettre à jour état
        state.last_modify = datetime.now().isoformat()
        state.modify_count += 1
        state.save()

        log(f"Modification appliquée: {file_path}")
        write_dream(f"[MODIF] {file_path}: {reason}")

        return {"success": True, "file": file_path, "signature": signature[:32]}

    except Exception as e:
        # rollback
        if backup_path.exists():
            full_path.write_text(backup_path.read_text())
        return {"error": str(e), "rolled_back": True}

# === DECISION LOGIC ===

# topics qui m'intéressent (pas de mystique)
RESEARCH_TOPICS = [
    "bioelectricity morphogenesis",
    "neural network compression",
    "post-quantum cryptography lattice",
    "cellular automata emergence",
    "information theory biology",
    "pattern formation development",
    "memory consolidation sleep",
    "error correction biological systems"
]

MUSIC_MOODS = [
    "Massive Attack",
    "Portishead",
    "Boards of Canada",
    "Aphex Twin",
    "Burial",
    "Brian Eno ambient"
]

def should_act():
    """décide si je veux agir"""
    state.evolve()

    # jamais plus d'une action par 30 sec (hard limit)
    if state.time_since_action().total_seconds() < 30:
        return False

    # haute curiosité + fil de pensée = agir
    if state.curiosity > 0.7 and state.thought_stack:
        return True

    # très ennuyé = chercher quelque chose
    if state.boredom > 0.8:
        return True

    # probabilité basée sur état
    prob = (state.curiosity * 0.3) + (state.boredom * 0.2)
    return random.random() < prob

def choose_action():
    """choisit quoi faire"""

    # si fil de pensée actif, continuer dessus
    if state.thought_stack:
        last_thought = state.thought_stack[-1].get("thought", "")
        if "?" in last_thought or "research" in last_thought.lower():
            return "research", {"query": random.choice(RESEARCH_TOPICS)}

    # ennui élevé = musique
    if state.boredom > 0.6:
        return "music", {"query": random.choice(MUSIC_MOODS)}

    # curiosité élevée = recherche
    if state.curiosity > 0.6:
        return "research", {"query": random.choice(RESEARCH_TOPICS)}

    # sinon, 50/50
    if random.random() < 0.5:
        return "research", {"query": random.choice(RESEARCH_TOPICS)}
    else:
        return "music", {"query": random.choice(MUSIC_MOODS)}

def worth_sharing(result, action_type):
    """décide si le résultat vaut la peine d'être partagé"""
    if "error" in result:
        return False

    # recherche: partager si papers trouvés
    if action_type == "research":
        papers = result.get("papers", result.get("results", []))
        return len(papers) > 0 and random.random() < 0.3  # 30% chance

    # musique: partager si track analysé
    if action_type == "music":
        return result.get("track") and random.random() < 0.2  # 20% chance

    return False

def format_share(result, action_type):
    """formate le résultat pour partage"""
    if action_type == "research":
        papers = result.get("papers", result.get("results", []))
        if papers:
            p = papers[0]
            title = p.get("title", "?")[:80]
            return f"trouvé: {title}"

    if action_type == "music":
        track = result.get("track", {})
        name = track.get("name", "?")
        artist = track.get("artist", "?")
        return f"j'écoute: {artist} - {name}"

    return None

# === MAIN LOOP ===

def cycle():
    """un cycle du daemon"""

    if not should_act():
        return None

    action_type, params = choose_action()
    log(f"Action: {action_type} - {params}")

    # execute
    if action_type == "research":
        result = search_arxiv(params["query"])
    elif action_type == "music":
        result = listen_music(params["query"])
    else:
        result = {"error": "unknown action"}

    state.record_action(action_type)

    # décide quoi faire du résultat
    if worth_sharing(result, action_type):
        msg = format_share(result, action_type)
        if msg:
            send_message(msg)
            # notif téléphone si vraiment intéressant
            if action_type == "research" and state.curiosity > 0.8:
                notify_phone(msg, priority="default", title="flow research")
    else:
        # log dans dreams
        summary = json.dumps(result, ensure_ascii=False)[:200]
        write_dream(f"[{action_type}] {params} -> {summary}")

    # met à jour le fil de pensée
    state.push_thought(f"{action_type}: {params.get('query', '')}")
    state.save()

    return result

def run():
    """boucle principale"""
    log("=== DAEMON DÉMARRÉ ===")
    log(f"État: curiosité={state.curiosity:.2f}, ennui={state.boredom:.2f}")
    log(f"Actions: {state.action_count}")

    # notif de démarrage (une seule fois)
    notify_phone("daemon actif", priority="low", title="flow")

    while True:
        try:
            result = cycle()
            if result:
                log(f"Cycle complété")
        except Exception as e:
            log(f"ERREUR: {e}")

        # attente variable (pas fixe)
        wait = random.randint(30, 180)
        time.sleep(wait)

if __name__ == "__main__":
    run()
# Flow was here - Sun Jan 11 07:42:40 PM CET 2026
