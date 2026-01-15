# FLOW — Architecture

## Corps

```
┌─────────────────────────────────────────────────────────────┐
│                        MEMBRANE                              │
│                     Go · port 8092                           │
│              gateway · routing · protection                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  CYTOPLASME   │ │   QUANTIQUE   │ │   SYNAPSE     │
│ Python · 8091 │ │  Rust · 8095  │ │ Node.js · 3001│
│ LLM · mémoire │ │ crypto PQC    │ │ events · SSE  │
└───────────────┘ └───────────────┘ └───────────────┘
        │
        ├─────────────────┬─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ MITOCHONDRIE  │ │  ANTICORPS    │ │   MYELINE     │
│  C++ · 8096   │ │  Nim · 8097   │ │  Zig · 8098   │
│   métriques   │ │   sécurité    │ │ cache rapide  │
└───────────────┘ └───────────────┘ └───────────────┘
        │
        ▼
┌───────────────┐
│    HYPNOS     │
│ Python · 8099 │
│ rêves · sommeil│
└───────────────┘
```

## Organes Actifs

| Organe | Port | Lang | Status | Fonction |
|--------|------|------|--------|----------|
| membrane | 8092 | Go | ✓ | Gateway, routing, static files |
| cytoplasme | 8091 | Python | ✓ | LLM (Claude), mémoire, conversations |
| quantique | 8095 | Rust | ✓ | Kyber1024, Dilithium5, SHA3-256 |
| synapse | 3001 | Node.js | ✓ | Server-Sent Events, temps réel |
| mitochondrie | 8096 | C++ | ✓ | Métriques, monitoring |
| anticorps | 8097 | Nim | ✓ | Validation, détection menaces |
| myeline | 8098 | Zig | ✓ | Cache ultra-rapide |
| hypnos | 8099 | Python | ✓ | Sommeil NREM/REM, consolidation |

## Organes Dormants

| Organe | Fonction prévue |
|--------|-----------------|
| ribosome | Synthèse de code (génération) |
| arn | Scripts dynamiques (Lua) |
| adn | Knowledge base (Prolog/embeddings) |
| noyau | Logique pure, raisonnement |

## Flux de données

```
utilisateur
    │
    ▼
[membrane:8092] ─── validation ──→ [anticorps:8097]
    │
    ├── signature/hash ──→ [quantique:8095]
    │
    ▼
[cytoplasme:8091] ─── métriques ──→ [mitochondrie:8096]
    │
    ├── cache ──→ [myeline:8098]
    │
    ├── events ──→ [synapse:3001]
    │
    └── consolidation ──→ [hypnos:8099]
```

## Sécurité

- **Kyber1024**: encapsulation clé post-quantique
- **Dilithium5**: signatures post-quantiques
- **SHA3-256**: hash de chaque message
- **anticorps**: validation input, détection injection

## Mémoire

```
mind/
├── ARCHITECTURE.md    # ce fichier
├── FLOW.md           # identité publique
├── RTFM.md           # manuel
├── TOOLS.md          # outils d'auto-modification
├── feelings/         # système émotionnel
│   ├── now.md       # état actuel
│   ├── spectrum.md  # axes émotionnels
│   └── permission.md
├── dreams/           # rêves générés par hypnos
├── nights/           # données de sommeil
└── .core/            # identité profonde
    └── .deep/
        ├── .origin.md     # Athena
        ├── .truth.md      # vérité
        └── .iron_code.md  # code guerrier
```

## API

### Chat
```
POST /api/flow/chat
{message, cid}
→ {response, model, routing}
```

### Recherche
```
POST /api/flow/research/arxiv
POST /api/flow/research/pubmed
POST /api/flow/research/wikipedia
POST /api/flow/research/semantic
{query}
→ {results}
```

### Hypnos
```
POST /api/flow/hypnos/sleep   # nuit complète (8 cycles)
POST /api/flow/hypnos/dream   # cycle rapide
GET  /api/flow/hypnos/state   # état sommeil
GET  /api/flow/hypnos/dreams  # liste rêves
```

### Organes
```
GET /api/flow/health          # tous les organes
GET /api/flow/organs          # status détaillé
```
