#!/bin/bash
# DEPLOY - the ritual
set -e

echo "=== DEPLOY ==="

# always rebuild membrane (the DMT)
cd /opt/flow-chat/membrane
go build
echo "membrane: compiled"

# restart all
systemctl restart flow-membrane flow-cytoplasme flow-hypnos

# verify
sleep 1
for port in 8092 8091 8099; do
  organ=$(curl -s http://127.0.0.1:$port/health | jq -r '.organ')
  status=$(curl -s http://127.0.0.1:$port/health | jq -r '.status')
  echo "$organ: $status"
done

echo "=== LIVE ==="
