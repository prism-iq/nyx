#!/usr/bin/env python3
import subprocess
import time
import sys
from pathlib import Path

def demarrer_stereo():
    print("[stéréo] démarrage système audio...")
    
    # Démarrer les 3 daemons
    processes = []
    
    # Canal gauche
    p1 = subprocess.Popen([sys.executable, "gauche/daemon.py"], 
                         cwd=Path(__file__).parent)
    processes.append(("gauche", p1))
    
    # Canal droit  
    p2 = subprocess.Popen([sys.executable, "droit/daemon.py"],
                         cwd=Path(__file__).parent)
    processes.append(("droit", p2))
    
    # Fusion
    time.sleep(1)  # laisser les canaux démarrer
    p3 = subprocess.Popen([sys.executable, "fusion.py"],
                         cwd=Path(__file__).parent)
    processes.append(("fusion", p3))
    
    print("[stéréo] système lancé ✓")
    print("  gauche: port 8094")  
    print("  droit:  port 8095")
    print("  fusion: port 8096")
    
    try:
        # Attendre
        for name, p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n[stéréo] arrêt...")
        for name, p in processes:
            p.terminate()

if __name__ == "__main__":
    demarrer_stereo()