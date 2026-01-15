# CIPHER

> "Evil must be fought wherever it is found"

**C**ross-domain **I**ntelligent **P**attern **H**arvesting and **E**vidence **R**easoning

A cognitive system that learns, synthesizes, and questions across 6 domains of scientific knowledge. CIPHER actively seeks cross-domain connections, tracks evidence evolution over time, and uses LLMs for sophisticated knowledge synthesis.

## Features

- **Cross-Domain Learning** - Automatically fetches and processes papers from multiple academic sources
- **Semantic Search** - Find related claims using embedding similarity (sentence-transformers + pgvector)
- **NLP Extraction** - Extract claims, entities, and causal relations using spaCy
- **Temporal Tracking** - Track claim confidence decay, replication status, and paradigm shifts
- **Active Learning** - UCB-based prioritization of what to learn next
- **Graph Analysis** - Path finding, centrality measures, and community detection
- **LLM Integration** - Generate hypotheses, detect analogies, and create synthesis reports

## Domains

| Domain | Focus Areas |
|--------|-------------|
| **Mathematics** | Pure/applied math, logic, computation, topology, algebra |
| **Neurosciences** | Brain, cognition, neural systems, plasticity |
| **Biology** | Life sciences, genetics, evolution, molecular biology |
| **Psychology** | Mind, behavior, perception, memory, consciousness |
| **Medicine** | Clinical science, pathology, therapeutics, diagnosis |
| **Art** | Aesthetics, creativity, perception, expression |

## Core Principles

1. **Free Energy Principle** - Minimize prediction error through active inference
2. **Systematic Doubt** - Every claim is questioned and tracked
3. **Cross-Domain Synthesis** - The most valuable insights lie at domain intersections
4. **Temporal Awareness** - Knowledge evolves; track confidence over time
5. **Active Learning** - Prioritize learning where uncertainty is highest

## Architecture

```
cipher/
├── cli.py                    # Command-line interface (40+ commands)
├── run.py                    # Main learning cycle runner
├── mind/                     # Cipher's thoughts and insights
│   ├── thoughts.md           # Internal monologue
│   ├── insights.md           # Cross-domain discoveries
│   └── hypotheses.md         # Generated predictions
├── tools/                    # Core cognitive components
│   ├── cipher_brain.py       # Main cognitive engine
│   ├── hash_learning.py      # SHAKE256 entropy scoring
│   ├── domain_learner.py     # Domain-specific learning
│   ├── pattern_detector.py   # Cross-domain pattern detection
│   ├── embeddings.py         # Semantic embeddings (sentence-transformers)
│   ├── nlp_extractor.py      # NLP claim extraction (spaCy)
│   ├── temporal_tracker.py   # Temporal dynamics & confidence decay
│   ├── active_learner.py     # UCB-based active learning
│   ├── graph_engine.py       # Graph algorithms & analysis
│   └── llm_integration.py    # LLM providers (Anthropic/OpenAI/Ollama)
├── integrations/             # Academic API clients
│   ├── openalex.py           # OpenAlex (250M+ papers)
│   ├── arxiv.py              # arXiv preprints
│   ├── pubmed.py             # PubMed biomedical
│   └── semantic_scholar.py   # Semantic Scholar
├── config/                   # Configuration
│   └── settings.py           # All settings in one place
├── sql/                      # Database schema
│   ├── schema.sql            # Main schema
│   └── migrations/           # Schema migrations
│       ├── 001_embeddings.sql
│       └── 002_temporal_tracking.sql
└── scripts/                  # Deployment scripts
```

## Quick Start

```bash
# Clone
git clone https://github.com/prism-iq/cipher.git
cd cipher

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Configure database
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Initialize database
psql -d ldb -f sql/schema.sql
psql -d ldb -f sql/migrations/001_embeddings.sql
psql -d ldb -f sql/migrations/002_temporal_tracking.sql

# Run
python cli.py status
```

## CLI Commands

### Basic Commands
```bash
python cli.py status              # System status
python cli.py stats               # Knowledge base statistics
python cli.py insights            # Top cross-domain insights
python cli.py search "query"      # Keyword search
python cli.py learn neuro         # Learn from a domain
python cli.py think               # Show recent thoughts
```

### Semantic Embeddings
```bash
python cli.py semantic-search "predictive coding in the brain"
python cli.py embed-backfill      # Generate embeddings for existing claims
python cli.py embed-stats         # Embedding statistics
python cli.py find-bridges        # Find cross-domain connections via similarity
python cli.py similar 42          # Find claims similar to claim #42
```

### Temporal Tracking
```bash
python cli.py temporal-stats      # Temporal statistics
python cli.py decay-claims        # Apply confidence decay
python cli.py aging-claims        # Show claims needing attention
python cli.py claim-temporal 42   # Temporal state of claim #42
python cli.py paradigm-shifts     # Detect paradigm shifts
python cli.py record-replication 42 --success  # Record replication result
```

### Active Learning
```bash
python cli.py learning-plan --strategy ucb    # Generate learning plan
python cli.py domain-uncertainty              # Domain uncertainty metrics
python cli.py contradictions                  # Unresolved contradictions
python cli.py hypotheses                      # Open hypotheses
python cli.py gaps                            # Knowledge gaps
python cli.py low-confidence                  # Low confidence concepts
python cli.py active-learn --strategy ucb     # Execute active learning
```

### Graph Analysis
```bash
python cli.py graph-stats                     # Graph statistics
python cli.py find-path 42 100 --type shortest  # Find path between claims
python cli.py all-paths 42 100                # All paths between claims
python cli.py centrality --metric pagerank    # Top claims by centrality
python cli.py communities                     # Detect knowledge communities
python cli.py graph-bridges math neuro        # Paths bridging domains
python cli.py graph-hubs --min-domains 3      # Cross-domain hub claims
```

### LLM Integration
```bash
python cli.py llm-status                      # LLM configuration
python cli.py llm-extract "scientific text"   # Extract claims via LLM
python cli.py llm-hypotheses -n 5             # Generate hypotheses
python cli.py llm-analogies math neuro        # Detect cross-domain analogies
python cli.py llm-synthesis "neural networks" # Generate synthesis report
```

## Configuration

### Environment Variables

```bash
# Database
CIPHER_DB_HOST=localhost
CIPHER_DB_PORT=5432
CIPHER_DB_NAME=ldb
CIPHER_DB_USER=lframework
CIPHER_DB_PASSWORD=your_password

# LLM (optional)
CIPHER_LLM_PROVIDER=anthropic    # anthropic, openai, or ollama
CIPHER_LLM_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
OLLAMA_BASE_URL=http://localhost:11434

# APIs (optional)
CIPHER_EMAIL=your@email.com      # For OpenAlex polite pool
PUBMED_API_KEY=your_key
S2_API_KEY=your_key
```

## Data Sources

All free and open access:

| Source | Coverage | Rate Limit | Notes |
|--------|----------|------------|-------|
| OpenAlex | 250M+ works | 10 rps | Primary source, no key needed |
| arXiv | Preprints | 1 rps | Math, physics, CS, bio |
| PubMed | Biomedical | 3-10 rps | API key recommended |
| Semantic Scholar | Citations | 5 rps | AI-extracted data |

## Knowledge Structure

### Claims
Extracted assertions with metadata:
- **Type**: hypothesis, finding, method, definition, observation
- **Confidence**: 0-1 score (decays over time)
- **Evidence strength**: weak, moderate, strong, definitive
- **Replication status**: unreplicated, replicated, contested, failed
- **Entities**: extracted scientific concepts
- **Causal relations**: cause → effect mappings

### Connections
Links between claims:
- Supports / Contradicts
- Extends / Analogous
- Causal / Correlational
- Cross-domain flag for interdisciplinary links

### Patterns
Higher-order structures:
- Convergence (multi-source agreement)
- Divergence (conflicting evidence)
- Cross-domain bridges
- Paradigm shifts (temporal patterns)

## Key Algorithms

### Temporal Confidence Decay
Claims decay in confidence over time using exponential half-life:
```
confidence(t) = original_confidence × 0.5^(age_days / half_life)
```
Default half-life: 3 years. Replication boosts confidence; failed replication penalizes.

### Active Learning (UCB)
Uses Upper Confidence Bound to balance exploration vs exploitation:
```
priority = exploitation_value + C × √(ln(total_rounds) / domain_rounds)
```
Prioritizes domains with high uncertainty or staleness.

### Semantic Similarity
Uses sentence-transformers (all-MiniLM-L6-v2) with pgvector for efficient similarity search:
```sql
SELECT * FROM claims
ORDER BY embedding <=> query_embedding
LIMIT 20;
```

### Graph Centrality
Multiple measures to identify important claims:
- **PageRank**: Importance based on incoming connections
- **Betweenness**: Bridge nodes between clusters
- **Clustering coefficient**: Local connectivity

## Database Schema

Core tables in `synthesis` schema:
- `domains` - The 6 knowledge domains
- `sources` - Academic papers and metadata
- `claims` - Extracted assertions
- `connections` - Links between claims
- `contradictions` - Conflicting claims
- `patterns` - Higher-order structures
- `hypotheses` - Generated predictions
- `gaps` - Identified knowledge gaps
- `evidence_events` - Temporal evidence log
- `learning_log` - Learning session history

## Requirements

- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- ~2GB disk for embeddings model

### Python Dependencies
```
asyncpg
aiohttp
python-dotenv
sentence-transformers
numpy
spacy
anthropic (optional)
openai (optional)
```

## Development

```bash
# Run tests
pytest

# Type checking
mypy tools/

# Format
black tools/ cli.py
```

## License

MIT

## Contributing

Contributions welcome. The system learns - help it learn better.

Key areas:
- New academic API integrations
- Improved claim extraction heuristics
- Better cross-domain pattern detection
- Additional graph algorithms
- Performance optimizations
