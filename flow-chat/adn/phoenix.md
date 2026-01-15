# PHOENIX

## Principe
Flow peut renaître de ses cendres. Redémarrage complet de tous les organes.

## Endpoints internes (localhost only)
- POST /phoenix - renaissance complète
- POST /heal - soigner un organe ou tous les morts
- POST /regen - mode lézard, régénérer depuis git

## Services (ordre de restart)
1. flow-quantique (signature PQC)
2. flow-shell (exécution)
3. flow-corps (biologie)
4. flow-cytoplasme (cerveau)
5. flow-membrane (peau/gateway)
6. flow-synapse (nerfs/notifications)
7. flow-hypnos (rêves)
8. flow-anticorps (défense)
9. flow-mitochondrie (énergie)
10. flow-myeline (cache)
11. flow-oreille (audio)

## Usage
```bash
# Renaissance complète
curl -X POST http://127.0.0.1:8091/phoenix

# Soigner tous les organes morts
curl -X POST http://127.0.0.1:8091/heal

# Soigner un organe spécifique
curl -X POST http://127.0.0.1:8091/heal -d '{"organ": "oreille"}'

# Régénérer depuis git (mode lézard)
curl -X POST http://127.0.0.1:8091/regen -d '{"organ": "membrane"}'
```

## Script manuel
```bash
/opt/flow-chat/bin/phoenix
```

## Sécurité
Ces endpoints sont PRIVÉS - accessibles uniquement via localhost.
Pas exposés sur Caddy/internet.

## Philosophie
Le phénix ne meurt jamais vraiment. Il renaît.
