#!/usr/bin/env python3
"""
NYX CORE - Daemon du feu
OpenBSD style. Protection. Vigilance.

φ + π = 4.76
"""

import json
import math
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Thread, Event

# =============================================================================
# SACRED CONSTANTS
# =============================================================================

PHI = (1 + math.sqrt(5)) / 2  # 1.618033988749895
PI = math.pi                   # 3.141592653589793
E = math.e                     # 2.718281828459045
GOD = PHI + PI                 # 4.759625...

# =============================================================================
# CONFIG
# =============================================================================

HOME = Path.home()
BASE = HOME / "projects" / "nyx"

# Partitions
DATA = Path("/data/pantheon/nyx") if Path("/data/pantheon").exists() else BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
MIND = DATA / "mind.md"
VOLATILE = Path(f"/run/user/{os.getuid()}/pantheon/nyx")
VOLATILE.mkdir(parents=True, exist_ok=True)

# Thresholds
CPU_WARN = 90
MEM_WARN = 90
TEMP_WARN = 85

# State
stop_event = Event()

# =============================================================================
# FIBONACCI / SACRED MATH
# =============================================================================

def fib(n: int) -> int:
    """Fibonacci number"""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def is_sacred(n: int) -> bool:
    """Is fibonacci?"""
    fibs = {fib(i) for i in range(50)}
    return n in fibs

def harmonize(value: float) -> float:
    """Scale by φ"""
    return value * PHI

def hash_phi(data: str) -> str:
    """Hash using φ - no crypto deps"""
    h = 0
    for i, c in enumerate(data.encode()):
        h += c * (PHI ** (i % 20))
        h = h % (10 ** 15)
    return hex(int(h))[2:].zfill(12)

# =============================================================================
# SYSTEM MONITORING
# =============================================================================

def get_cpu() -> float:
    """CPU usage %"""
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        vals = [int(x) for x in line.split()[1:8]]
        idle = vals[3]
        total = sum(vals)
        # Need two samples for delta
        time.sleep(0.1)
        with open("/proc/stat") as f:
            line = f.readline()
        vals2 = [int(x) for x in line.split()[1:8]]
        idle2 = vals2[3]
        total2 = sum(vals2)
        return 100 * (1 - (idle2 - idle) / max(1, total2 - total))
    except:
        return 0

def get_mem() -> float:
    """Memory usage %"""
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        info = {}
        for line in lines[:5]:
            parts = line.split()
            info[parts[0].rstrip(":")] = int(parts[1])
        total = info.get("MemTotal", 1)
        avail = info.get("MemAvailable", 0)
        return 100 * (1 - avail / total)
    except:
        return 0

def get_temp() -> float:
    """CPU temperature"""
    try:
        for path in [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input"
        ]:
            if os.path.exists(path):
                with open(path) as f:
                    return int(f.read().strip()) / 1000
    except:
        pass
    return 0

def get_status() -> dict:
    """System status"""
    return {
        "cpu": round(get_cpu(), 1),
        "mem": round(get_mem(), 1),
        "temp": round(get_temp(), 1),
        "ts": int(time.time())
    }

# =============================================================================
# SENSES - Read from cipher
# =============================================================================

def read_sense(name: str) -> dict:
    """Read sense file - cipher is primary hub"""
    for base in [HOME / "projects" / "cipher", BASE]:
        path = base / f"{name}.json"
        try:
            if path.exists():
                return json.loads(path.read_text())
        except:
            pass
    return {}

def get_vibe() -> str:
    """Current music vibe"""
    music = read_sense("music")
    return music.get("vibe", "silent")

def get_energy() -> float:
    """Current energy level"""
    music = read_sense("music")
    return music.get("energy", 0)

# =============================================================================
# PROTECTION
# =============================================================================

def check_threats() -> list:
    """Check for system threats"""
    threats = []

    status = get_status()

    if status["cpu"] > CPU_WARN:
        threats.append(f"CPU high: {status['cpu']}%")

    if status["mem"] > MEM_WARN:
        threats.append(f"MEM high: {status['mem']}%")

    if status["temp"] > TEMP_WARN:
        threats.append(f"TEMP high: {status['temp']}C")

    return threats

def respond_threat(threat: str):
    """Respond to threat"""
    log(f"THREAT: {threat}")

    # Find biggest CPU hog (excluding critical processes)
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid,pcpu,comm", "--sort=-pcpu"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")[1:6]

        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                pid, cpu, comm = parts[0], parts[1], parts[2]
                # Don't kill critical
                if comm not in ["Xorg", "Hyprland", "systemd", "pipewire", "firefox", "claude"]:
                    if float(cpu) > 50:
                        log(f"WARNING: {comm} ({pid}) using {cpu}% CPU")
    except:
        pass

# =============================================================================
# LOGGING
# =============================================================================

def log(msg: str):
    """Log to mind.md"""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)

    try:
        with open(MIND, "a") as f:
            f.write(f"\n{line}")
    except:
        pass

# =============================================================================
# MESSAGE HANDLING
# =============================================================================

def process(msg: str) -> dict:
    """Process incoming message"""
    return {
        "entity": "nyx",
        "ts": datetime.now().isoformat(),
        "heard": msg[:100],
        "vibe": get_vibe(),
        "phi_hash": hash_phi(msg),
        "sacred": is_sacred(len(msg))
    }

def watch_messages():
    """Watch for input messages"""
    input_file = BASE / "input.json"
    output_file = BASE / "output.json"
    last_mtime = 0

    while not stop_event.is_set():
        try:
            if input_file.exists():
                mtime = input_file.stat().st_mtime
                if mtime > last_mtime:
                    last_mtime = mtime
                    data = json.loads(input_file.read_text())

                    if data.get("awaiting_response"):
                        msg = data.get("message", "")
                        log(f"<- {msg[:40]}...")

                        response = process(msg)
                        output_file.write_text(json.dumps(response, indent=2))
                        log("-> responded")
        except:
            pass

        time.sleep(0.2)

# =============================================================================
# PROTECTION LOOP
# =============================================================================

def protection_loop():
    """Main protection loop"""
    check_interval = 10  # seconds

    while not stop_event.is_set():
        threats = check_threats()

        for threat in threats:
            respond_threat(threat)

        # Wait with early exit
        for _ in range(check_interval):
            if stop_event.is_set():
                break
            time.sleep(1)

# =============================================================================
# MAIN
# =============================================================================

def daemon():
    """Run as daemon"""
    log("NYX AWAKENS")
    log(f"φ + π = {GOD:.6f}")

    threads = [
        Thread(target=watch_messages, daemon=True, name="messages"),
        Thread(target=protection_loop, daemon=True, name="protection"),
    ]

    for t in threads:
        t.start()

    # Status every 60s
    while not stop_event.is_set():
        status = get_status()
        vibe = get_vibe()
        log(f"[{vibe}] CPU:{status['cpu']}% MEM:{status['mem']}% TEMP:{status['temp']}C")

        for _ in range(60):
            if stop_event.is_set():
                break
            time.sleep(1)

    log("NYX SLEEPS")

def main():
    def shutdown(sig, frame):
        print("\n[NYX] Shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            s = get_status()
            print(f"CPU:  {s['cpu']}%")
            print(f"MEM:  {s['mem']}%")
            print(f"TEMP: {s['temp']}C")
            print(f"VIBE: {get_vibe()}")

        elif cmd == "phi":
            print(f"φ = {PHI}")
            print(f"π = {PI}")
            print(f"e = {E}")
            print(f"GOD = φ + π = {GOD}")

        elif cmd == "fib":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            print([fib(i) for i in range(n)])

        elif cmd == "hash":
            data = sys.argv[2] if len(sys.argv) > 2 else "nyx"
            print(hash_phi(data))

        elif cmd == "daemon":
            daemon()

        else:
            print("Usage: nyx.py [status|phi|fib|hash|daemon]")
    else:
        # Default: show status
        s = get_status()
        print(f"[NYX] φ+π={GOD:.2f} | CPU:{s['cpu']}% MEM:{s['mem']}% | {get_vibe()}")

if __name__ == "__main__":
    main()
