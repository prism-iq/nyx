#!/usr/bin/env python3
"""
VEILLE DAEMON — Service autonome de surveillance

Exécute la veille immunitaire en continu
Démarre avec: systemctl start flow-veille
"""

import sys
import signal
import time
sys.path.insert(0, '/opt/flow-chat')

from corps.veille import veille, exec_veille


def shutdown_handler(signum, frame):
    """Arrêt propre sur SIGTERM/SIGINT"""
    print("[veille] Shutting down...")
    veille.stop()
    sys.exit(0)


def main():
    # Handlers de signaux
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    print("[veille] Starting immune system daemon...")
    print(exec_veille("start"))

    # Boucle principale - garde le process vivant
    try:
        while veille.running:
            time.sleep(10)
            # Afficher le statut périodiquement
            if veille.state["cycles_completed"] % 5 == 0:
                print(f"[veille] Cycle {veille.state['cycles_completed']}: {veille.state['status']} ({veille.state['integrity_score']*100:.0f}%)")
    except KeyboardInterrupt:
        pass

    veille.stop()
    print("[veille] Daemon stopped")


if __name__ == "__main__":
    main()
