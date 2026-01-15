# FLOW - Architecture Biologique Polyglotte

## Concept
Corps cellulaire IA avec crypto post-quantique. Chaque organe = un langage optimisé pour sa fonction.

## Organes

| Organe | Port | Langage | Fonction |
|--------|------|---------|----------|
| membrane | 8092 | Go | Gateway I/O, routing |
| cytoplasme | 8091 | Python | LLM, cache, mémoire |
| quantique | 8095 | Rust | Crypto PQC (Kyber+Dilithium) |
| synapse | 3001 | Node.js | Events, connexions async |
| mitochondrie | 8096 | C++ | Métriques, énergie |
| anticorps | 8097 | Nim | Sécurité, validation |
| myeline | 8098 | Zig | Cache ultra-rapide |
| ribosome | lib | Rust | Synthèse (shared lib) |
| arn | - | Lua | Scripts dynamiques |
| adn | - | Prolog/Py | Knowledge base |
| noyau | - | Python | Logique pure |
| hypnos | 8099 | Python | Sommeil, rêves, consolidation |
| corps | 8101 | Python | Métabolisme (sang, bile, pus, flore, lymphe) |

## Corps - Systèmes Biologiques

| Système | Module | Fonction |
|---------|--------|----------|
| sang | corps/sang.py | Circulation, fetch données fraîches (arXiv) |
| bile | corps/bile.py | Digestion, décompose en nutriments |
| pus | corps/pus.py | Système immunitaire, inflammation |
| flore | corps/flore.py | Microbiome, patterns symbiotiques |
| lymphe | corps/lymphe.py | Garbage collection, détoxification |

**Endpoints:**
- `GET /corps/health` - État vital complet
- `POST /corps/digest` - Digérer des données
- `POST /corps/flore/nourrir` - Nourrir la flore avec des concepts
- `GET /corps/flore/fermenter` - Générer des connexions
- `POST /corps/immune/scan` - Scan immunitaire
- `POST /corps/lymphe/detox` - Cycle de détoxification

## Sécurité
- **Kyber1024**: Encapsulation post-quantique
- **Dilithium5**: Signatures post-quantiques
- **SHA3-256**: Hash de chaque message in/out
- **Vérification d'intégrité**: Continue sur l'état

## Flux
```
Client → Caddy → membrane:8092 → cytoplasme:8091 → Claude API
                      ↓
                quantique:8095 (sign/verify)
                      ↓
                mitochondrie:8096 (metrics)
```

## Philosophie CIPHER
- 7 domaines: math, neuro, bio, psycho, med, art, philo
- Concepts unificateurs: network, learning, entropy, emergence, prediction
- Iron Code: "evil must be fought wherever it is found"
