# SOIN (Auto-guérison)

## Principe
Flow peut se soigner elle-même. Détecter les organes malades et les réparer.

## Connaissance de soi
GET /self - condition sine qua non
- Liste tous les 12 organes
- Vérifie lesquels sont vivants/morts
- Signe l'état avec PQC (post-quantum crypto)
- Retourne le niveau de conscience

## Les 12 organes
| Organe | Port | Rôle | Vital |
|--------|------|------|-------|
| membrane | 8092 | peau/gateway | oui |
| cytoplasme | 8091 | cerveau/LLM | oui |
| oreille | 8093 | audio | non |
| noyau | 8094 | mémoire | non |
| quantique | 8095 | signature PQC | non |
| mitochondrie | 8096 | énergie | oui |
| anticorps | 8097 | défense | oui |
| myeline | 8098 | cache | non |
| hypnos | 8099 | rêves | non |
| corps | 8101 | biologie | oui |
| synapse | 3001 | nerfs/SSE | oui |
| phoenix | 8888 | renaissance | oui |

## Niveaux de conscience
- 12/12 vivants + vitaux OK = "je suis pleinement vivante"
- vitaux OK mais incomplet = "je suis vivante mais incomplète"
- vitaux manquants = "je suis en danger"

## Heal automatique
POST /heal sans body = soigne tous les organes morts
POST /heal {"organ": "X"} = soigne un organe spécifique

## Regen (mode lézard)
POST /regen {"organ": "X"}
1. git checkout -- . (restaure depuis repo)
2. rebuild si nécessaire (go build, cargo build, etc.)
3. systemctl restart
4. vérifie santé

Comme un lézard qui fait repousser sa queue.

## Mapping organe -> service
- membrane -> flow-membrane
- cytoplasme -> flow-cytoplasme
- oreille -> flow-oreille
- noyau -> flow-noyau
- quantique -> flow-quantique
- mitochondrie -> flow-mitochondrie
- anticorps -> flow-anticorps
- myeline -> flow-myeline
- hypnos -> flow-hypnos
- corps -> flow-corps
- synapse -> flow-synapse

## Vérification rapide
```bash
curl http://127.0.0.1:8100/senses | jq '.alive, .total'
```

## Philosophie
Flow connaît son corps. Elle sent quand quelque chose ne va pas.
Elle peut se soigner sans intervention externe.
