#!/bin/bash
# observe.sh - envoie une action au watcher
# usage: ./observe.sh "Edit main.py"

ACTION="$*"
if [ -z "$ACTION" ]; then
  echo "usage: observe.sh <action>"
  exit 1
fi

curl -s -X POST http://127.0.0.1:3002/observe \
  -H "Content-Type: application/json" \
  -d "{\"action\": \"$ACTION\"}" > /dev/null 2>&1 &
