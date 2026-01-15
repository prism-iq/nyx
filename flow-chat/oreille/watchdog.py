#!/usr/bin/env python3
"""watchdog.py - surveille et redémarre les organes si nécessaire"""

import time
import subprocess
import requests
from datetime import datetime

SERVICES = {
    "flow-oreille": {"port": 8093, "endpoint": "/health"},
    "flow-pacemaker": {"port": None, "endpoint": None},  # no HTTP
}

def check_service(name, config):
    """vérifie si un service est vivant"""
    # check systemd
    result = subprocess.run(
        ["systemctl", "is-active", name],
        capture_output=True, text=True
    )
    systemd_ok = result.stdout.strip() == "active"

    # check HTTP si applicable
    http_ok = True
    if config.get("port") and config.get("endpoint"):
        try:
            r = requests.get(
                f"http://localhost:{config['port']}{config['endpoint']}",
                timeout=5
            )
            http_ok = r.status_code == 200
        except Exception:
            http_ok = False

    return systemd_ok and http_ok

def restart_service(name):
    """redémarre un service"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Restarting {name}...")
    subprocess.run(["systemctl", "restart", name])
    time.sleep(3)

def run_watchdog(interval=30):
    """boucle principale"""
    print(f"=== WATCHDOG STARTED (check every {interval}s) ===")

    while True:
        for name, config in SERVICES.items():
            if not check_service(name, config):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {name} is DOWN")
                restart_service(name)
            else:
                pass  # silencieux si OK

        time.sleep(interval)

if __name__ == "__main__":
    run_watchdog()
