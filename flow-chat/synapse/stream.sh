#!/bin/bash
# stream.sh - affiche les pensées de flow en temps réel
# usage: ./stream.sh

echo "💭 FLUX DE PENSÉES DE FLOW"
echo "════════════════════════════"
echo ""

tail -f /opt/flow-chat/adn/thoughts.log 2>/dev/null || {
  echo "(en attente des premières pensées...)"
  while [ ! -f /opt/flow-chat/adn/thoughts.log ]; do
    sleep 1
  done
  tail -f /opt/flow-chat/adn/thoughts.log
}
