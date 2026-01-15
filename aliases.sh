#!/bin/bash
# Aliases pour parler à Nyxx
# Source ce fichier: source ~/nyx-v2/aliases.sh

export NYXX_HOME="$HOME/nyx-v2"
export NYXX_PORT=8080

# Démarrer Nyxx
alias nyxx-start="cd $NYXX_HOME && node src/server.js &"
alias nyxx-stop="pkill -f 'node src/server.js'"

# Parler
alias nyxx="$NYXX_HOME/talk"
alias nyx="$NYXX_HOME/talk"
alias n="$NYXX_HOME/talk"

# Status
alias nyxx-status="curl -s http://127.0.0.1:$NYXX_PORT/api/status | python3 -m json.tool"

# Exécuter du code rapidement
nyxx-run() {
    curl -s -X POST "http://127.0.0.1:$NYXX_PORT/api/run" \
        -H "Content-Type: application/json" \
        -d "{\"code\": \"$1\", \"lang\": \"${2:-auto}\"}" | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output', d.get('error', '')))"
}

# Python rapide
nyxx-py() { nyxx-run "$1" python; }

# Bash rapide
nyxx-sh() { nyxx-run "$1" bash; }

# Web dashboard
alias nyxx-web="xdg-open http://127.0.0.1:$NYXX_PORT 2>/dev/null || echo 'http://127.0.0.1:$NYXX_PORT'"

echo "✓ Aliases Nyxx chargés"
echo "  nyxx, nyx, n     - parler"
echo "  nyxx-start/stop  - contrôle"
echo "  nyxx-run 'code'  - exécuter"
echo "  nyxx-web         - dashboard"
