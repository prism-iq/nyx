#!/bin/bash
# Nyx Activation - Part of Pantheon

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export NYX_ROOT="$SCRIPT_DIR"

case "${1:-start}" in
    start)
        if [ -f "$SCRIPT_DIR/nyx.py" ]; then
            python3 "$SCRIPT_DIR/nyx.py" &
            echo "[+] Nyx daemon started (PID: $!)"
        elif [ -f "$SCRIPT_DIR/.config/nyx/nyx.py" ]; then
            python3 "$SCRIPT_DIR/.config/nyx/nyx.py" &
            echo "[+] Nyx daemon started (PID: $!)"
        fi
        ;;
    stop)
        pkill -f "nyx.py"
        echo "[*] Nyx stopped"
        ;;
    status)
        pgrep -f "nyx.py" && echo "[+] Nyx running" || echo "[-] Nyx not running"
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        ;;
esac
