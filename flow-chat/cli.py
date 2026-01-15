#!/usr/bin/env python3
"""
CIPHER CLI
Command-line interface for interacting with the Cipher system.

Usage:
    python cli.py status          # Show system status
    python cli.py stats           # Show knowledge base statistics
    python cli.py insights        # Show top cross-domain insights
    python cli.py search <query>  # Search claims
    python cli.py learn <domain>  # Trigger learning for domain
    python cli.py think           # Show recent thoughts
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed

from config.settings import config


async def show_status():
    """Show system status."""
    import asyncpg

    print("CIPHER System Status")
    print("=" * 50)
    print(f"Iron Code: {config.iron_code}")
    print(f"Base Path: {config.paths.base_path}")
    print()

    # Check database
    print("Database Connection:")
    try:
        conn = await asyncpg.connect(config.db.connection_string)
        version = await conn.fetchval("SELECT version()")
        print(f"  Status: Connected")
        print(f"  Version: {version[:50]}...")
        await conn.close()
    except Exception as e:
        print(f"  Status: Error - {e}")

    # Check directories
    print("\nDirectories:")
    for name, path in [
        ("Mind", config.paths.mind_path),
        ("Tools", config.paths.tools_path),
        ("Logs", config.paths.logs_path),
    ]:
        exists = path.exists()
        print(f"  {name}: {'OK' if exists else 'MISSING'} ({path})")


async def show_stats():
    """Show knowledge base statistics."""
    import asyncpg

    print("CIPHER Knowledge Base Statistics")
    print("=" * 50)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        # Get stats
        stats = await conn.fetchrow("SELECT * FROM synthesis.get_stats()")

        print(f"\nTotal Sources:           {stats['total_sources']:,}")
        print(f"Total Claims:            {stats['total_claims']:,}")
        print(f"Total Connections:       {stats['total_connections']:,}")
        print(f"Cross-Domain Connections:{stats['cross_domain_connections']:,}")
        print(f"Total Patterns:          {stats['total_patterns']:,}")
        print(f"Open Contradictions:     {stats['open_contradictions']:,}")
        print(f"Open Gaps:               {stats['open_gaps']:,}")

        # Get per-domain stats
        print("\nBy Domain:")
        rows = await conn.fetch("""
            SELECT d.name, COUNT(DISTINCT c.id) as claims
            FROM synthesis.domains d
            LEFT JOIN synthesis.claims c ON d.id = ANY(c.domains)
            GROUP BY d.name
            ORDER BY claims DESC
        """)
        for row in rows:
            print(f"  {row['name']:15} {row['claims']:,} claims")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


async def show_insights(limit: int = 10):
    """Show top cross-domain insights."""
    import asyncpg

    print("CIPHER Cross-Domain Insights")
    print("=" * 50)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        rows = await conn.fetch("""
            SELECT pattern_name, pattern_type, description,
                   confidence, novelty_score, created_at
            FROM synthesis.patterns
            WHERE pattern_type = 'cross_domain' OR
                  (SELECT COUNT(DISTINCT unnest) FROM unnest(domains)) >= 2
            ORDER BY novelty_score * confidence DESC
            LIMIT $1
        """, limit)

        if not rows:
            print("\nNo cross-domain insights found yet.")
            print("Run a learning cycle to discover insights.")
            return

        for i, row in enumerate(rows, 1):
            print(f"\n{i}. {row['pattern_name']}")
            print(f"   Type: {row['pattern_type']}")
            print(f"   Confidence: {row['confidence']:.2f}, Novelty: {row['novelty_score']:.2f}")
            print(f"   {row['description'][:200]}...")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


async def search_claims(query: str, limit: int = 20):
    """Search claims in the knowledge base."""
    import asyncpg

    print(f"Searching for: '{query}'")
    print("=" * 50)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        rows = await conn.fetch("""
            SELECT c.claim_text, c.claim_type, c.confidence,
                   s.title as source_title
            FROM synthesis.claims c
            JOIN synthesis.sources s ON c.source_id = s.id
            WHERE LOWER(c.claim_text) LIKE $1
            ORDER BY c.confidence DESC
            LIMIT $2
        """, f"%{query.lower()}%", limit)

        if not rows:
            print(f"\nNo claims found matching '{query}'")
            return

        print(f"\nFound {len(rows)} claims:\n")
        for row in rows:
            print(f"[{row['claim_type']}] (conf: {row['confidence']:.2f})")
            print(f"  {row['claim_text'][:150]}...")
            print(f"  Source: {row['source_title'][:50]}...")
            print()

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


async def show_thoughts(limit: int = 20):
    """Show recent thoughts."""
    import asyncpg

    print("CIPHER Recent Thoughts")
    print("=" * 50)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        rows = await conn.fetch("""
            SELECT thought_type, content, importance, created_at
            FROM synthesis.thoughts
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)

        if not rows:
            print("\nNo thoughts recorded yet.")
            return

        for row in rows:
            ts = row['created_at'].strftime('%Y-%m-%d %H:%M')
            print(f"\n[{row['thought_type']}] ({ts}) imp={row['importance']:.1f}")
            print(f"  {row['content'][:200]}...")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


async def trigger_learn(domain: str):
    """Trigger learning for a specific domain."""
    from tools.cipher_brain import CipherBrain, Domain
    from tools.domain_learner import DomainLearner

    domain_map = {
        'math': Domain.MATHEMATICS,
        'neuro': Domain.NEUROSCIENCES,
        'bio': Domain.BIOLOGY,
        'psych': Domain.PSYCHOLOGY,
        'med': Domain.MEDICINE,
        'art': Domain.ART,
    }

    if domain.lower() not in domain_map:
        print(f"Unknown domain: {domain}")
        print(f"Available: {list(domain_map.keys())}")
        return

    target = domain_map[domain.lower()]
    print(f"Starting learning session for: {target.name}")
    print("=" * 50)

    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    learner = DomainLearner(brain, {
        'email': config.api.openalex_email,
    })

    try:
        session = await learner.learn_domain(target, max_papers=50)
        print(f"\nResults:")
        print(f"  Papers fetched: {session.papers_fetched}")
        print(f"  Claims extracted: {session.claims_extracted}")
        print(f"  Connections found: {session.connections_found}")
        print(f"  Patterns detected: {session.patterns_detected}")
        if session.errors:
            print(f"  Errors: {len(session.errors)}")
    finally:
        await learner.close()
        await brain.close()


# =========================================================================
# SEMANTIC EMBEDDING COMMANDS
# =========================================================================

async def semantic_search(query: str, limit: int = 20, threshold: float = 0.5):
    """Semantic search using embeddings."""
    from tools.cipher_brain import CipherBrain

    print(f"Semantic search for: '{query}'")
    print(f"Threshold: {threshold}, Limit: {limit}")
    print("=" * 50)

    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    try:
        results = await brain.semantic_search_claims(
            query=query,
            limit=limit,
            threshold=threshold
        )

        if not results:
            print(f"\nNo semantically similar claims found.")
            print("Try lowering the threshold with --threshold 0.3")
            return

        print(f"\nFound {len(results)} similar claims:\n")
        for claim_id, claim_text, similarity in results:
            print(f"[{similarity:.3f}] (ID: {claim_id})")
            print(f"  {claim_text[:150]}...")
            print()

    finally:
        await brain.close()


async def embed_backfill(batch_size: int = 100, limit: int = None):
    """Backfill embeddings for existing claims."""
    from tools.cipher_brain import CipherBrain

    print("Backfilling embeddings for existing claims")
    print("=" * 50)

    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    try:
        updated = await brain.embed_existing_claims(
            batch_size=batch_size,
            limit=limit
        )
        print(f"\nCompleted! Updated {updated} claims with embeddings.")

    finally:
        await brain.close()


async def find_bridges(threshold: float = 0.75, limit: int = 20):
    """Find cross-domain connections using embedding similarity."""
    from tools.cipher_brain import CipherBrain

    print("Finding cross-domain connections via embeddings")
    print(f"Threshold: {threshold}")
    print("=" * 50)

    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    try:
        connections = await brain.find_cross_domain_by_embedding(
            threshold=threshold,
            limit=limit
        )

        if not connections:
            print("\nNo cross-domain connections found.")
            print("Try lowering the threshold or run embed-backfill first.")
            return

        print(f"\nFound {len(connections)} potential cross-domain bridges:\n")
        for i, conn in enumerate(connections, 1):
            print(f"{i}. {conn['domain_a']} <-> {conn['domain_b']} (sim: {conn['similarity']:.3f})")
            print(f"   A: {conn['claim_a_text'][:80]}...")
            print(f"   B: {conn['claim_b_text'][:80]}...")
            print()

    finally:
        await brain.close()


async def find_similar(claim_id: int, limit: int = 10, cross_domain: bool = False):
    """Find claims similar to a given claim."""
    from tools.cipher_brain import CipherBrain

    print(f"Finding claims similar to ID: {claim_id}")
    if cross_domain:
        print("(Cross-domain only)")
    print("=" * 50)

    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    try:
        results = await brain.find_similar_claims(
            claim_id=claim_id,
            limit=limit,
            cross_domain_only=cross_domain
        )

        if not results:
            print("\nNo similar claims found.")
            return

        print(f"\nFound {len(results)} similar claims:\n")
        for cid, text, similarity, domains in results:
            domain_names = [d.name for d in domains]
            print(f"[{similarity:.3f}] (ID: {cid}) Domains: {domain_names}")
            print(f"  {text[:150]}...")
            print()

    finally:
        await brain.close()


async def embedding_stats():
    """Show embedding statistics."""
    import asyncpg

    print("CIPHER Embedding Statistics")
    print("=" * 50)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        # Count claims with/without embeddings
        total = await conn.fetchval("SELECT COUNT(*) FROM synthesis.claims")
        with_emb = await conn.fetchval(
            "SELECT COUNT(*) FROM synthesis.claims WHERE embedding IS NOT NULL"
        )
        without_emb = total - with_emb

        print(f"\nTotal claims:        {total:,}")
        print(f"With embeddings:     {with_emb:,} ({100*with_emb/total:.1f}%)" if total > 0 else "With embeddings:     0")
        print(f"Without embeddings:  {without_emb:,}")

        # Get embedding model info
        from tools.embeddings import get_embedding_service
        service = get_embedding_service()
        print(f"\nEmbedding Model: {service.model_name}")
        print(f"Dimensions: {service.dimensions}")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


# =========================================================================
# TEMPORAL TRACKING COMMANDS
# =========================================================================

async def temporal_stats():
    """Show temporal tracking statistics."""
    import asyncpg

    print("CIPHER Temporal Tracking Statistics")
    print("=" * 50)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        # Replication status distribution
        print("\nReplication Status Distribution:")
        rows = await conn.fetch("""
            SELECT
                COALESCE(replication_status, 'unreplicated') as status,
                COUNT(*) as count
            FROM synthesis.claims
            GROUP BY replication_status
            ORDER BY count DESC
        """)
        for row in rows:
            print(f"  {row['status']:20} {row['count']:,}")

        # Claim status distribution
        print("\nClaim Lifecycle Status:")
        rows = await conn.fetch("""
            SELECT
                COALESCE(status, 'active') as status,
                COUNT(*) as count
            FROM synthesis.claims
            GROUP BY status
            ORDER BY count DESC
        """)
        for row in rows:
            print(f"  {row['status']:20} {row['count']:,}")

        # Age distribution
        print("\nClaim Age Distribution:")
        rows = await conn.fetch("""
            SELECT
                CASE
                    WHEN EXTRACT(days FROM NOW() - created_at) < 30 THEN '< 1 month'
                    WHEN EXTRACT(days FROM NOW() - created_at) < 180 THEN '1-6 months'
                    WHEN EXTRACT(days FROM NOW() - created_at) < 365 THEN '6-12 months'
                    WHEN EXTRACT(days FROM NOW() - created_at) < 730 THEN '1-2 years'
                    ELSE '> 2 years'
                END as age_group,
                COUNT(*) as count,
                AVG(COALESCE(current_confidence, confidence)) as avg_confidence
            FROM synthesis.claims
            GROUP BY age_group
            ORDER BY count DESC
        """)
        for row in rows:
            conf = row['avg_confidence'] or 0
            print(f"  {row['age_group']:15} {row['count']:,} claims (avg conf: {conf:.2f})")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")


async def decay_claims():
    """Apply confidence decay to all claims."""
    from tools.temporal_tracker import TemporalTracker

    print("Applying confidence decay to claims...")
    print("=" * 50)

    tracker = TemporalTracker(config.db.connection_string)
    await tracker.connect()

    try:
        updated = await tracker.decay_all_claims()
        print(f"\nUpdated {updated} claims with decayed confidence.")

    finally:
        await tracker.close()


async def aging_claims(min_age: int = 180, max_conf: float = 0.5):
    """Show aging claims that need attention."""
    from tools.temporal_tracker import TemporalTracker

    print(f"Claims older than {min_age} days with confidence < {max_conf}")
    print("=" * 60)

    tracker = TemporalTracker(config.db.connection_string)
    await tracker.connect()

    try:
        claims = await tracker.get_aging_claims(min_age, max_conf)

        if not claims:
            print("\nNo aging claims found matching criteria.")
            return

        print(f"\nFound {len(claims)} aging claims:\n")
        for claim in claims[:20]:
            age = int(claim.get('age_days', 0))
            orig_conf = claim.get('original_confidence', 0) or 0
            curr_conf = claim.get('current_confidence', 0) or 0
            repl = claim.get('replication_status', 'unreplicated')

            print(f"ID {claim['id']} | Age: {age}d | Conf: {orig_conf:.2f} -> {curr_conf:.2f} | Repl: {repl}")
            print(f"  {claim['claim_text'][:70]}...")
            print()

    finally:
        await tracker.close()


async def claim_temporal(claim_id: int):
    """Show temporal state of a specific claim."""
    from tools.temporal_tracker import TemporalTracker

    print(f"Temporal State for Claim ID: {claim_id}")
    print("=" * 50)

    tracker = TemporalTracker(config.db.connection_string)
    await tracker.connect()

    try:
        state = await tracker.get_temporal_state(claim_id)

        if not state:
            print(f"\nClaim {claim_id} not found.")
            return

        print(f"\nClaim ID:            {state.claim_id}")
        print(f"Status:              {state.status.value}")
        print(f"Age:                 {state.age_days} days")
        print(f"Half-life:           {state.half_life_days:.0f} days")
        print(f"\nConfidence:")
        print(f"  Original:          {state.original_confidence:.3f}")
        print(f"  Current:           {state.current_confidence:.3f}")
        print(f"  Trend:             {state.confidence_trend:+.3f}")
        print(f"\nReplication:")
        print(f"  Status:            {state.replication_status.value}")
        print(f"  Successful:        {state.replication_count}")
        print(f"  Failed:            {state.failed_replication_count}")
        print(f"\nCitations:")
        print(f"  Total:             {state.citation_count}")
        print(f"  Velocity:          {state.citation_velocity:.1f}/month")
        print(f"\nTimestamps:")
        print(f"  First seen:        {state.first_seen}")
        print(f"  Last confirmed:    {state.last_confirmed or 'Never'}")
        print(f"  Last cited:        {state.last_cited or 'Never'}")

        if state.superseded_by:
            print(f"\nSuperseded by:       Claim ID {state.superseded_by}")

    finally:
        await tracker.close()


async def detect_paradigm_shifts(days: int = 365):
    """Detect potential paradigm shifts."""
    from tools.temporal_tracker import TemporalTracker

    print(f"Detecting paradigm shifts (last {days} days)")
    print("=" * 50)

    tracker = TemporalTracker(config.db.connection_string)
    await tracker.connect()

    try:
        patterns = await tracker.detect_paradigm_shifts(days)

        if not patterns:
            print("\nNo paradigm shifts detected.")
            return

        print(f"\nFound {len(patterns)} temporal patterns:\n")
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. [{pattern.pattern_type}] (conf: {pattern.confidence:.2f})")
            print(f"   {pattern.description}")
            print(f"   Claims involved: {len(pattern.claims_involved)}")
            print(f"   Started: {pattern.start_date}")
            print()

    finally:
        await tracker.close()


async def record_replication(claim_id: int, success: bool, partial: bool = False):
    """Record a replication attempt for a claim."""
    from tools.temporal_tracker import TemporalTracker

    status = "successful" if success else "failed"
    if partial:
        status = "partial"

    print(f"Recording {status} replication for Claim ID: {claim_id}")
    print("=" * 50)

    tracker = TemporalTracker(config.db.connection_string)
    await tracker.connect()

    try:
        result = await tracker.record_replication(
            claim_id=claim_id,
            success=success,
            partial=partial
        )

        if result:
            print(f"\nReplication recorded successfully.")
            # Show updated state
            state = await tracker.get_temporal_state(claim_id)
            if state:
                print(f"New replication status: {state.replication_status.value}")
                print(f"New confidence: {state.current_confidence:.3f}")
        else:
            print("\nFailed to record replication.")

    finally:
        await tracker.close()


# =========================================================================
# ACTIVE LEARNING COMMANDS
# =========================================================================

async def learning_plan(strategy: str = 'ucb', max_targets: int = 10):
    """Generate an active learning plan."""
    from tools.active_learner import ActiveLearner, LearningStrategy

    strategy_map = {
        'ucb': LearningStrategy.UCB,
        'uncertainty': LearningStrategy.UNCERTAINTY_SAMPLING,
        'contradiction': LearningStrategy.CONTRADICTION_RESOLUTION,
        'hypothesis': LearningStrategy.HYPOTHESIS_TESTING,
        'gap': LearningStrategy.GAP_FILLING,
        'exploration': LearningStrategy.EXPLORATION,
        'exploitation': LearningStrategy.EXPLOITATION,
    }

    print(f"Generating Active Learning Plan")
    print(f"Strategy: {strategy}")
    print("=" * 60)

    learner = ActiveLearner(config.db.connection_string)
    await learner.connect()

    try:
        strat = strategy_map.get(strategy, LearningStrategy.UCB)
        plan = await learner.create_learning_plan(strat, max_targets)

        print(f"\n{plan.rationale}")
        print(f"Total Priority: {plan.total_priority:.2f}")
        print(f"Expected Value: {plan.expected_value:.2f}")
        print(f"\nPrioritized Targets:\n")

        for i, target in enumerate(plan.targets, 1):
            print(f"{i}. [{target.target_type.upper()}] {target.target_name}")
            print(f"   Priority: {target.priority:.3f} | Uncertainty: {target.uncertainty:.3f}")
            print(f"   Strategy: {target.strategy.value}")
            print(f"   Rationale: {target.rationale}")
            if target.search_queries:
                print(f"   Queries: {target.search_queries[:2]}")
            print()

    finally:
        await learner.close()


async def domain_uncertainty():
    """Show uncertainty metrics for each domain."""
    from tools.active_learner import ActiveLearner

    print("Domain Uncertainty Analysis")
    print("=" * 70)

    learner = ActiveLearner(config.db.connection_string)
    await learner.connect()

    try:
        uncertainties = await learner.compute_domain_uncertainty()

        print(f"\n{'Domain':<15} {'Claims':<8} {'Conf':<8} {'Var':<8} {'Contr':<8} {'Stale':<8} {'Priority':<8}")
        print("-" * 70)

        for du in uncertainties:
            print(f"{du.domain_name:<15} {du.claim_count:<8} {du.avg_confidence:<8.3f} "
                  f"{du.confidence_variance:<8.3f} {du.contradiction_count:<8} "
                  f"{du.staleness_days:<8.0f} {du.priority_score:<8.3f}")

        print("\nLegend:")
        print("  Conf = Average confidence")
        print("  Var = Confidence variance")
        print("  Contr = Unresolved contradictions")
        print("  Stale = Days since last learning")
        print("  Priority = Overall priority score (higher = needs more attention)")

    finally:
        await learner.close()


async def show_contradictions(limit: int = 20):
    """Show unresolved contradictions."""
    from tools.active_learner import ActiveLearner

    print("Unresolved Contradictions")
    print("=" * 60)

    learner = ActiveLearner(config.db.connection_string)
    await learner.connect()

    try:
        targets = await learner.get_unresolved_contradictions(limit)

        if not targets:
            print("\nNo unresolved contradictions found.")
            return

        print(f"\nFound {len(targets)} unresolved contradictions:\n")

        for i, target in enumerate(targets, 1):
            print(f"{i}. Severity: {target.priority:.2f}")
            print(f"   Claim A: {target.metadata.get('claim_a', '')[:80]}...")
            print(f"   Claim B: {target.metadata.get('claim_b', '')[:80]}...")
            print(f"   Suggested queries: {target.search_queries[:2]}")
            print()

    finally:
        await learner.close()


async def show_hypotheses(limit: int = 20):
    """Show open hypotheses needing testing."""
    from tools.active_learner import ActiveLearner

    print("Open Hypotheses")
    print("=" * 60)

    learner = ActiveLearner(config.db.connection_string)
    await learner.connect()

    try:
        targets = await learner.get_open_hypotheses(limit)

        if not targets:
            print("\nNo open hypotheses found.")
            return

        print(f"\nFound {len(targets)} open hypotheses:\n")

        for i, target in enumerate(targets, 1):
            print(f"{i}. Priority: {target.priority:.2f} | Status: {target.metadata.get('status', 'unknown')}")
            print(f"   {target.metadata.get('hypothesis', '')[:100]}...")
            if target.metadata.get('source_pattern'):
                print(f"   From pattern: {target.metadata['source_pattern']}")
            print(f"   Search queries: {target.search_queries[:2]}")
            print()

    finally:
        await learner.close()


async def show_gaps(limit: int = 20):
    """Show open knowledge gaps."""
    from tools.active_learner import ActiveLearner

    print("Knowledge Gaps")
    print("=" * 60)

    learner = ActiveLearner(config.db.connection_string)
    await learner.connect()

    try:
        targets = await learner.get_knowledge_gaps(limit)

        if not targets:
            print("\nNo open knowledge gaps found.")
            return

        print(f"\nFound {len(targets)} knowledge gaps:\n")

        for i, target in enumerate(targets, 1):
            importance = target.metadata.get('importance', 0)
            tractability = target.metadata.get('tractability', 0)
            print(f"{i}. Priority: {target.priority:.2f} (importance={importance:.2f}, tractability={tractability:.2f})")
            print(f"   {target.metadata.get('description', '')[:100]}...")
            if target.metadata.get('directions'):
                print(f"   Research directions: {target.metadata['directions'][:2]}")
            print(f"   Search queries: {target.search_queries[:2]}")
            print()

    finally:
        await learner.close()


async def low_confidence_concepts(threshold: float = 0.4, limit: int = 30):
    """Show concepts with low confidence claims."""
    from tools.active_learner import ActiveLearner

    print(f"Low Confidence Concepts (threshold: {threshold})")
    print("=" * 60)

    learner = ActiveLearner(config.db.connection_string)
    await learner.connect()

    try:
        targets = await learner.get_low_confidence_concepts(threshold, limit)

        if not targets:
            print(f"\nNo concepts with confidence < {threshold} found.")
            return

        print(f"\nFound {len(targets)} low-confidence concepts:\n")

        for i, target in enumerate(targets, 1):
            claim_count = target.metadata.get('claim_count', 0)
            avg_conf = target.metadata.get('avg_confidence', 0)
            print(f"{i}. {target.target_name}")
            print(f"   Claims: {claim_count} | Avg confidence: {avg_conf:.3f}")
            print(f"   Search queries: {target.search_queries[:2]}")
            print()

    finally:
        await learner.close()


async def active_learn(strategy: str = 'ucb', max_papers: int = 50):
    """Execute active learning using the specified strategy."""
    from tools.active_learner import ActiveLearner, LearningStrategy
    from tools.cipher_brain import CipherBrain, Domain
    from tools.domain_learner import DomainLearner

    strategy_map = {
        'ucb': LearningStrategy.UCB,
        'uncertainty': LearningStrategy.UNCERTAINTY_SAMPLING,
        'contradiction': LearningStrategy.CONTRADICTION_RESOLUTION,
        'hypothesis': LearningStrategy.HYPOTHESIS_TESTING,
        'gap': LearningStrategy.GAP_FILLING,
        'exploration': LearningStrategy.EXPLORATION,
        'exploitation': LearningStrategy.EXPLOITATION,
    }

    print(f"Executing Active Learning")
    print(f"Strategy: {strategy}")
    print(f"Max papers per target: {max_papers}")
    print("=" * 60)

    # Get learning plan
    learner = ActiveLearner(config.db.connection_string)
    await learner.connect()

    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    domain_learner = DomainLearner(brain, {
        'email': config.api.openalex_email,
    })

    try:
        strat = strategy_map.get(strategy, LearningStrategy.UCB)
        plan = await learner.create_learning_plan(strat, max_targets=5)

        print(f"\nLearning plan: {plan.rationale}")
        print(f"Targets: {len(plan.targets)}\n")

        total_papers = 0
        total_claims = 0
        total_connections = 0

        for target in plan.targets:
            print(f"\n>> Processing: {target.target_name}")

            if target.target_type == 'domain':
                # Use domain learner for domain targets
                domain_map = {
                    'mathematics': Domain.MATHEMATICS,
                    'neurosciences': Domain.NEUROSCIENCES,
                    'biology': Domain.BIOLOGY,
                    'psychology': Domain.PSYCHOLOGY,
                    'medicine': Domain.MEDICINE,
                    'art': Domain.ART,
                }

                domain = domain_map.get(target.target_name.lower())
                if domain:
                    session = await domain_learner.learn_domain(
                        domain,
                        max_papers=max_papers
                    )
                    total_papers += session.papers_fetched
                    total_claims += session.claims_extracted
                    total_connections += session.connections_found

                    print(f"   Papers: {session.papers_fetched}, Claims: {session.claims_extracted}, "
                          f"Connections: {session.connections_found}")

            elif target.search_queries:
                # Use cross-domain search for other targets
                session = await domain_learner.learn_cross_domain(
                    concepts=target.search_queries[:2],
                    max_papers=max_papers // 2
                )
                total_papers += session.papers_fetched
                total_claims += session.claims_extracted
                total_connections += session.connections_found

                print(f"   Papers: {session.papers_fetched}, Claims: {session.claims_extracted}, "
                      f"Connections: {session.connections_found}")

            # Record learning round
            domain_id = target.domains[0] if target.domains else None
            await learner.record_learning_round(
                domain_id=domain_id,
                papers_processed=total_papers,
                claims_extracted=total_claims,
                connections_found=total_connections
            )

        print(f"\n" + "=" * 60)
        print(f"Active Learning Complete!")
        print(f"Total papers: {total_papers}")
        print(f"Total claims: {total_claims}")
        print(f"Total connections: {total_connections}")

    finally:
        await domain_learner.close()
        await brain.close()
        await learner.close()


# =========================================================================
# GRAPH ENGINE COMMANDS
# =========================================================================

async def graph_stats():
    """Show knowledge graph statistics."""
    from tools.graph_engine import GraphEngine

    print("Knowledge Graph Statistics")
    print("=" * 60)

    engine = GraphEngine(config.db.connection_string)
    await engine.connect()

    try:
        await engine.load_graph()
        stats = engine.compute_graph_stats()

        print(f"\nNodes (claims):          {stats.node_count:,}")
        print(f"Edges (connections):     {stats.edge_count:,}")
        print(f"Graph density:           {stats.density:.6f}")
        print(f"Average degree:          {stats.avg_degree:.2f}")
        print(f"Average clustering:      {stats.avg_clustering:.4f}")
        print(f"Number of communities:   {stats.num_communities}")
        print(f"Largest community:       {stats.largest_community_size} nodes")
        print(f"Cross-domain edge ratio: {stats.cross_domain_edge_ratio:.2%}")

    finally:
        await engine.close()


async def find_path(source_id: int, target_id: int, path_type: str = 'shortest'):
    """Find path between two claims."""
    from tools.graph_engine import GraphEngine

    print(f"Finding {path_type} path from claim {source_id} to {target_id}")
    print("=" * 60)

    engine = GraphEngine(config.db.connection_string)
    await engine.connect()

    try:
        if path_type == 'cte':
            # Use database CTE
            path = await engine.find_path_cte(source_id, target_id)
        else:
            # Use in-memory algorithms
            await engine.load_graph()
            if path_type == 'shortest':
                path = engine.find_shortest_path(source_id, target_id)
            elif path_type == 'strongest':
                path = engine.find_strongest_path(source_id, target_id)
            elif path_type == 'cross_domain':
                path = engine.find_cross_domain_path(source_id, target_id)
            else:
                path = engine.find_shortest_path(source_id, target_id)

        if not path:
            print(f"\nNo path found between claims {source_id} and {target_id}")
            return

        print(f"\nPath found ({len(path.nodes)} nodes):")
        print(f"Type: {path.path_type}")
        print(f"Total weight: {path.total_weight:.3f}")
        print(f"Domains traversed: {path.domains_traversed}")
        print(f"\nPath: {' -> '.join(str(n) for n in path.nodes)}")

        # Get claim texts
        import asyncpg
        conn = await asyncpg.connect(config.db.connection_string)
        try:
            print("\nClaims in path:")
            for i, node_id in enumerate(path.nodes):
                row = await conn.fetchrow(
                    "SELECT claim_text FROM synthesis.claims WHERE id = $1",
                    node_id
                )
                if row:
                    print(f"  {i+1}. [{node_id}] {row['claim_text'][:80]}...")
        finally:
            await conn.close()

    finally:
        await engine.close()


async def centrality(metric: str = 'pagerank', limit: int = 20):
    """Show top claims by centrality metric."""
    from tools.graph_engine import GraphEngine

    print(f"Top Claims by {metric.title()} Centrality")
    print("=" * 60)

    engine = GraphEngine(config.db.connection_string)
    await engine.connect()

    try:
        await engine.load_graph()
        top_nodes = engine.get_top_nodes_by_centrality(metric, limit)

        if not top_nodes:
            print("\nNo nodes found in graph.")
            return

        print(f"\n{'Rank':<6} {'ID':<8} {'Score':<12} {'Claim'}")
        print("-" * 60)

        for i, (node_id, score, text) in enumerate(top_nodes, 1):
            print(f"{i:<6} {node_id:<8} {score:<12.6f} {text[:40]}...")

    finally:
        await engine.close()


async def communities(limit: int = 20):
    """Detect and show knowledge communities."""
    from tools.graph_engine import GraphEngine
    from tools.cipher_brain import Domain

    print("Knowledge Graph Communities")
    print("=" * 60)

    engine = GraphEngine(config.db.connection_string)
    await engine.connect()

    try:
        await engine.load_graph()
        comms = engine.detect_communities()

        if not comms:
            print("\nNo communities detected.")
            return

        print(f"\nFound {len(comms)} communities:\n")

        domain_names = {d.value: d.name for d in Domain}

        for i, comm in enumerate(comms[:limit], 1):
            domain_str = ", ".join(
                domain_names.get(d, str(d))
                for d in comm.dominant_domains[:2]
            ) or "mixed"

            print(f"{i}. Community {comm.id}")
            print(f"   Size: {comm.size} nodes")
            print(f"   Density: {comm.density:.4f}")
            print(f"   Coherence: {comm.coherence:.3f}")
            print(f"   Dominant domains: {domain_str}")
            print(f"   Bridge nodes: {len(comm.bridge_nodes)}")
            print()

    finally:
        await engine.close()


async def domain_bridges(domain_a: str, domain_b: str, limit: int = 10):
    """Find paths bridging two domains."""
    from tools.graph_engine import GraphEngine
    from tools.cipher_brain import Domain

    domain_map = {
        'math': Domain.MATHEMATICS,
        'neuro': Domain.NEUROSCIENCES,
        'bio': Domain.BIOLOGY,
        'psych': Domain.PSYCHOLOGY,
        'med': Domain.MEDICINE,
        'art': Domain.ART,
    }

    if domain_a.lower() not in domain_map or domain_b.lower() not in domain_map:
        print(f"Unknown domain. Available: {list(domain_map.keys())}")
        return

    da = domain_map[domain_a.lower()]
    db = domain_map[domain_b.lower()]

    print(f"Finding paths between {da.name} and {db.name}")
    print("=" * 60)

    engine = GraphEngine(config.db.connection_string)
    await engine.connect()

    try:
        paths = await engine.find_domain_bridges(da.value, db.value)

        if not paths:
            print(f"\nNo paths found bridging {da.name} and {db.name}")
            return

        print(f"\nFound {len(paths)} bridging paths:\n")

        for i, path in enumerate(paths[:limit], 1):
            print(f"{i}. Path ({len(path.nodes)} nodes)")
            print(f"   Weight: {path.total_weight:.3f}")
            print(f"   Nodes: {' -> '.join(str(n) for n in path.nodes)}")
            print()

    finally:
        await engine.close()


async def cross_domain_hubs(min_domains: int = 2, limit: int = 20):
    """Find claims that connect multiple domains."""
    from tools.graph_engine import GraphEngine
    from tools.cipher_brain import Domain

    print(f"Cross-Domain Hub Claims (min {min_domains} domains)")
    print("=" * 60)

    engine = GraphEngine(config.db.connection_string)
    await engine.connect()

    try:
        hubs = await engine.get_cross_domain_hubs(min_domains)

        if not hubs:
            print(f"\nNo claims found spanning {min_domains}+ domains.")
            return

        domain_names = {d.value: d.name for d in Domain}

        print(f"\n{'ID':<8} {'Domains':<8} {'Domain Names'}")
        print("-" * 60)

        for claim_id, domain_count, domains in hubs[:limit]:
            domain_str = ", ".join(domain_names.get(d, str(d)) for d in domains)
            print(f"{claim_id:<8} {domain_count:<8} {domain_str}")

    finally:
        await engine.close()


async def all_paths(source_id: int, target_id: int, max_depth: int = 5, limit: int = 10):
    """Find all paths between two claims."""
    from tools.graph_engine import GraphEngine

    print(f"Finding all paths from claim {source_id} to {target_id}")
    print(f"Max depth: {max_depth}")
    print("=" * 60)

    engine = GraphEngine(config.db.connection_string)
    await engine.connect()

    try:
        paths = await engine.find_all_paths_cte(source_id, target_id, max_depth, limit)

        if not paths:
            print(f"\nNo paths found between claims {source_id} and {target_id}")
            return

        print(f"\nFound {len(paths)} paths:\n")

        for i, path in enumerate(paths, 1):
            cross = " (cross-domain)" if path.path_type == 'cross_domain' else ""
            print(f"{i}. {len(path.nodes)} hops, weight={path.total_weight:.3f}{cross}")
            print(f"   {' -> '.join(str(n) for n in path.nodes)}")

    finally:
        await engine.close()


# =========================================================================
# LLM INTEGRATION COMMANDS
# =========================================================================

async def llm_extract(text: str, title: str = ""):
    """Extract claims from text using LLM."""
    from tools.llm_integration import LLMIntegration, LLMConfig

    print("Extracting claims using LLM")
    print("=" * 60)

    try:
        llm_config = LLMConfig.from_env()
        print(f"Provider: {llm_config.provider.value}")
        print(f"Model: {llm_config.model}")

        llm = LLMIntegration(llm_config)
        claims = await llm.extract_claims(text, title)

        if not claims:
            print("\nNo claims extracted.")
            return

        print(f"\nExtracted {len(claims)} claims:\n")

        for i, claim in enumerate(claims, 1):
            print(f"{i}. [{claim.claim_type}] (conf: {claim.confidence:.2f})")
            print(f"   {claim.claim_text[:100]}...")
            print(f"   Evidence: {claim.evidence_strength} | Hedging: {claim.hedging_level:.2f}")
            if claim.entities:
                print(f"   Entities: {claim.entities[:5]}")
            if claim.causal_relations:
                print(f"   Causal: {claim.causal_relations[:2]}")
            print()

    except Exception as e:
        print(f"Error: {e}")


async def llm_hypotheses(num: int = 5):
    """Generate hypotheses from knowledge base patterns."""
    from tools.llm_integration import LLMIntegration, LLMConfig
    import asyncpg

    print("Generating hypotheses using LLM")
    print("=" * 60)

    try:
        # Get patterns and claims from DB
        conn = await asyncpg.connect(config.db.connection_string)

        patterns = await conn.fetch("""
            SELECT pattern_name, pattern_type, description, domains, confidence
            FROM synthesis.patterns
            ORDER BY novelty_score * confidence DESC
            LIMIT 20
        """)

        claims = await conn.fetch("""
            SELECT claim_text, claim_type, domains, confidence
            FROM synthesis.claims
            ORDER BY confidence DESC
            LIMIT 50
        """)

        await conn.close()

        patterns_list = [dict(p) for p in patterns]
        claims_list = [dict(c) for c in claims]

        if not patterns_list:
            print("\nNo patterns in knowledge base. Run learning first.")
            return

        llm_config = LLMConfig.from_env()
        print(f"Provider: {llm_config.provider.value}")
        print(f"Model: {llm_config.model}")

        llm = LLMIntegration(llm_config)
        hypotheses = await llm.generate_hypotheses(patterns_list, claims_list, num)

        if not hypotheses:
            print("\nNo hypotheses generated.")
            return

        print(f"\nGenerated {len(hypotheses)} hypotheses:\n")

        for i, h in enumerate(hypotheses, 1):
            print(f"{i}. {h.hypothesis_text}")
            print(f"   Domains: {', '.join(h.domains_involved)}")
            print(f"   Testability: {h.testability:.2f} | Novelty: {h.novelty:.2f} | Confidence: {h.confidence:.2f}")
            print(f"   Reasoning: {h.supporting_reasoning[:100]}...")
            if h.suggested_experiments:
                print(f"   Experiments: {h.suggested_experiments[:2]}")
            print()

    except Exception as e:
        print(f"Error: {e}")


async def llm_analogies(domain_a: str, domain_b: str, num: int = 5):
    """Detect cross-domain analogies using LLM."""
    from tools.llm_integration import LLMIntegration, LLMConfig
    from tools.cipher_brain import Domain
    import asyncpg

    domain_map = {
        'math': Domain.MATHEMATICS,
        'neuro': Domain.NEUROSCIENCES,
        'bio': Domain.BIOLOGY,
        'psych': Domain.PSYCHOLOGY,
        'med': Domain.MEDICINE,
        'art': Domain.ART,
    }

    if domain_a.lower() not in domain_map or domain_b.lower() not in domain_map:
        print(f"Unknown domain. Available: {list(domain_map.keys())}")
        return

    da = domain_map[domain_a.lower()]
    db = domain_map[domain_b.lower()]

    print(f"Detecting analogies between {da.name} and {db.name}")
    print("=" * 60)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        claims_a = await conn.fetch("""
            SELECT claim_text, claim_type, confidence
            FROM synthesis.claims
            WHERE $1 = ANY(domains)
            ORDER BY confidence DESC
            LIMIT 30
        """, da.value)

        claims_b = await conn.fetch("""
            SELECT claim_text, claim_type, confidence
            FROM synthesis.claims
            WHERE $1 = ANY(domains)
            ORDER BY confidence DESC
            LIMIT 30
        """, db.value)

        await conn.close()

        claims_a_list = [dict(c) for c in claims_a]
        claims_b_list = [dict(c) for c in claims_b]

        if not claims_a_list or not claims_b_list:
            print(f"\nInsufficient claims in one or both domains.")
            return

        llm_config = LLMConfig.from_env()
        print(f"Provider: {llm_config.provider.value}")
        print(f"Model: {llm_config.model}")

        llm = LLMIntegration(llm_config)
        analogies = await llm.detect_analogies(
            da.name, db.name, claims_a_list, claims_b_list, num
        )

        if not analogies:
            print("\nNo analogies detected.")
            return

        print(f"\nDetected {len(analogies)} analogies:\n")

        for i, a in enumerate(analogies, 1):
            print(f"{i}. {a.source_concept} ({a.source_domain}) <-> {a.target_concept} ({a.target_domain})")
            print(f"   Strength: {a.strength:.2f}")
            print(f"   {a.analogy_description[:150]}...")
            if a.limitations:
                print(f"   Limitations: {a.limitations[:2]}")
            if a.research_opportunities:
                print(f"   Opportunities: {a.research_opportunities[:2]}")
            print()

    except Exception as e:
        print(f"Error: {e}")


async def llm_synthesis(topic: str):
    """Generate a synthesis report using LLM."""
    from tools.llm_integration import LLMIntegration, LLMConfig
    import asyncpg

    print(f"Generating synthesis report on: {topic}")
    print("=" * 60)

    try:
        conn = await asyncpg.connect(config.db.connection_string)

        # Search for relevant claims
        claims = await conn.fetch("""
            SELECT claim_text, claim_type, domains, confidence
            FROM synthesis.claims
            WHERE LOWER(claim_text) LIKE $1
            ORDER BY confidence DESC
            LIMIT 50
        """, f"%{topic.lower()}%")

        patterns = await conn.fetch("""
            SELECT pattern_name, pattern_type, description, confidence, novelty_score
            FROM synthesis.patterns
            WHERE LOWER(description) LIKE $1
            ORDER BY novelty_score * confidence DESC
            LIMIT 20
        """, f"%{topic.lower()}%")

        contradictions = await conn.fetch("""
            SELECT c1.claim_text as claim_a, c2.claim_text as claim_b,
                   ct.contradiction_type, ct.severity
            FROM synthesis.contradictions ct
            JOIN synthesis.claims c1 ON ct.claim_a_id = c1.id
            JOIN synthesis.claims c2 ON ct.claim_b_id = c2.id
            WHERE ct.resolution_status = 'unresolved'
            LIMIT 10
        """)

        gaps = await conn.fetch("""
            SELECT gap_description, importance, tractability
            FROM synthesis.gaps
            WHERE status = 'open'
            LIMIT 10
        """)

        await conn.close()

        claims_list = [dict(c) for c in claims]
        patterns_list = [dict(p) for p in patterns]
        contradictions_list = [dict(c) for c in contradictions]
        gaps_list = [dict(g) for g in gaps]

        if not claims_list:
            print(f"\nNo claims found related to '{topic}'.")
            return

        llm_config = LLMConfig.from_env()
        print(f"Provider: {llm_config.provider.value}")
        print(f"Model: {llm_config.model}")
        print(f"\nAnalyzing {len(claims_list)} claims, {len(patterns_list)} patterns...")

        llm = LLMIntegration(llm_config)
        report = await llm.generate_synthesis_report(
            topic, claims_list, patterns_list, contradictions_list, gaps_list
        )

        print(f"\n{'='*60}")
        print(f"SYNTHESIS REPORT: {report.title}")
        print(f"{'='*60}")
        print(f"\n## Executive Summary\n")
        print(report.executive_summary)

        print(f"\n## Key Findings\n")
        for finding in report.key_findings:
            print(f"- {finding}")

        print(f"\n## Cross-Domain Insights\n")
        for insight in report.cross_domain_insights:
            print(f"- {insight}")

        if report.contradictions_noted:
            print(f"\n## Contradictions\n")
            for c in report.contradictions_noted:
                print(f"- {c}")

        if report.knowledge_gaps:
            print(f"\n## Knowledge Gaps\n")
            for g in report.knowledge_gaps:
                print(f"- {g}")

        print(f"\n## Future Directions\n")
        for direction in report.future_directions:
            print(f"- {direction}")

        print(f"\n{'='*60}")
        print(f"Full report: {len(report.full_report)} characters")
        print(f"Generated at: {report.generated_at}")

    except Exception as e:
        print(f"Error: {e}")


async def llm_status():
    """Show LLM configuration status."""
    from tools.llm_integration import LLMConfig

    print("LLM Integration Status")
    print("=" * 60)

    try:
        llm_config = LLMConfig.from_env()

        print(f"\nProvider: {llm_config.provider.value}")
        print(f"Model: {llm_config.model}")
        print(f"Max tokens: {llm_config.max_tokens}")
        print(f"Temperature: {llm_config.temperature}")

        if llm_config.provider.value == "anthropic":
            api_key = llm_config.api_key
            if api_key:
                print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
            else:
                print("API Key: NOT SET (set ANTHROPIC_API_KEY)")
        elif llm_config.provider.value == "openai":
            api_key = llm_config.api_key
            if api_key:
                print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
            else:
                print("API Key: NOT SET (set OPENAI_API_KEY)")
        else:
            print(f"Base URL: {llm_config.base_url}")

        print("\nEnvironment Variables:")
        print(f"  CIPHER_LLM_PROVIDER = {os.getenv('CIPHER_LLM_PROVIDER', '(not set, default: anthropic)')}")
        print(f"  CIPHER_LLM_MODEL = {os.getenv('CIPHER_LLM_MODEL', '(not set)')}")
        print(f"  ANTHROPIC_API_KEY = {'set' if os.getenv('ANTHROPIC_API_KEY') else 'not set'}")
        print(f"  OPENAI_API_KEY = {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")

    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='CIPHER Command Line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py status
  python cli.py stats
  python cli.py insights
  python cli.py search "neural network"
  python cli.py learn neuro
  python cli.py think

Semantic Embedding Commands:
  python cli.py semantic-search "predictive coding in the brain"
  python cli.py embed-backfill
  python cli.py embed-stats
  python cli.py find-bridges --threshold 0.7
  python cli.py similar 42 --cross-domain

Temporal Tracking Commands:
  python cli.py temporal-stats
  python cli.py decay-claims
  python cli.py aging-claims --min-age 365 --max-conf 0.4
  python cli.py claim-temporal 42
  python cli.py paradigm-shifts --days 730
  python cli.py record-replication 42 --success

Active Learning Commands:
  python cli.py learning-plan --strategy ucb
  python cli.py domain-uncertainty
  python cli.py contradictions
  python cli.py hypotheses
  python cli.py gaps
  python cli.py low-confidence --threshold 0.3
  python cli.py active-learn --strategy ucb --max-papers 50

Graph Engine Commands:
  python cli.py graph-stats
  python cli.py find-path 42 100 --type shortest
  python cli.py all-paths 42 100 --max-depth 5
  python cli.py centrality --metric pagerank
  python cli.py communities
  python cli.py graph-bridges math neuro
  python cli.py graph-hubs --min-domains 3

LLM Integration Commands:
  python cli.py llm-status
  python cli.py llm-extract "Neural plasticity enables learning..."
  python cli.py llm-hypotheses -n 5
  python cli.py llm-analogies math neuro
  python cli.py llm-synthesis "neural networks"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Status
    subparsers.add_parser('status', help='Show system status')

    # Stats
    subparsers.add_parser('stats', help='Show knowledge base statistics')

    # Insights
    insights_parser = subparsers.add_parser('insights', help='Show top insights')
    insights_parser.add_argument('-n', type=int, default=10, help='Number of insights')

    # Search
    search_parser = subparsers.add_parser('search', help='Search claims (keyword)')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('-n', type=int, default=20, help='Max results')

    # Learn
    learn_parser = subparsers.add_parser('learn', help='Trigger learning')
    learn_parser.add_argument('domain', help='Domain to learn (math/neuro/bio/psych/med/art)')

    # Think
    think_parser = subparsers.add_parser('think', help='Show recent thoughts')
    think_parser.add_argument('-n', type=int, default=20, help='Number of thoughts')

    # =========================================================================
    # SEMANTIC EMBEDDING COMMANDS
    # =========================================================================

    # Semantic Search
    sem_search = subparsers.add_parser('semantic-search', help='Search using semantic similarity')
    sem_search.add_argument('query', help='Natural language query')
    sem_search.add_argument('-n', type=int, default=20, help='Max results')
    sem_search.add_argument('--threshold', type=float, default=0.5, help='Similarity threshold (0-1)')

    # Embed Backfill
    backfill = subparsers.add_parser('embed-backfill', help='Generate embeddings for existing claims')
    backfill.add_argument('--batch-size', type=int, default=100, help='Batch size')
    backfill.add_argument('--limit', type=int, default=None, help='Max claims to process')

    # Embedding Stats
    subparsers.add_parser('embed-stats', help='Show embedding statistics')

    # Find Bridges
    bridges = subparsers.add_parser('find-bridges', help='Find cross-domain connections via embeddings')
    bridges.add_argument('--threshold', type=float, default=0.75, help='Similarity threshold')
    bridges.add_argument('-n', type=int, default=20, help='Max results')

    # Similar Claims
    similar = subparsers.add_parser('similar', help='Find claims similar to a given claim')
    similar.add_argument('claim_id', type=int, help='Claim ID to find similar claims for')
    similar.add_argument('-n', type=int, default=10, help='Max results')
    similar.add_argument('--cross-domain', action='store_true', help='Only show cross-domain matches')

    # =========================================================================
    # TEMPORAL TRACKING COMMANDS
    # =========================================================================

    # Temporal Stats
    subparsers.add_parser('temporal-stats', help='Show temporal tracking statistics')

    # Decay Claims
    subparsers.add_parser('decay-claims', help='Apply confidence decay to all claims')

    # Aging Claims
    aging = subparsers.add_parser('aging-claims', help='Show aging claims needing attention')
    aging.add_argument('--min-age', type=int, default=180, help='Minimum age in days')
    aging.add_argument('--max-conf', type=float, default=0.5, help='Maximum confidence threshold')

    # Claim Temporal State
    claim_temp = subparsers.add_parser('claim-temporal', help='Show temporal state of a claim')
    claim_temp.add_argument('claim_id', type=int, help='Claim ID')

    # Paradigm Shifts
    paradigm = subparsers.add_parser('paradigm-shifts', help='Detect paradigm shifts')
    paradigm.add_argument('--days', type=int, default=365, help='Look back period in days')

    # Record Replication
    repl = subparsers.add_parser('record-replication', help='Record replication attempt')
    repl.add_argument('claim_id', type=int, help='Claim ID')
    repl.add_argument('--success', action='store_true', help='Replication succeeded')
    repl.add_argument('--failure', action='store_true', help='Replication failed')
    repl.add_argument('--partial', action='store_true', help='Partial replication')

    # =========================================================================
    # ACTIVE LEARNING COMMANDS
    # =========================================================================

    # Learning Plan
    plan_parser = subparsers.add_parser('learning-plan', help='Generate active learning plan')
    plan_parser.add_argument('--strategy', type=str, default='ucb',
                            choices=['ucb', 'uncertainty', 'contradiction', 'hypothesis',
                                    'gap', 'exploration', 'exploitation'],
                            help='Learning strategy')
    plan_parser.add_argument('-n', type=int, default=10, help='Max targets')

    # Domain Uncertainty
    subparsers.add_parser('domain-uncertainty', help='Show domain uncertainty metrics')

    # Contradictions
    contr_parser = subparsers.add_parser('contradictions', help='Show unresolved contradictions')
    contr_parser.add_argument('-n', type=int, default=20, help='Max results')

    # Hypotheses
    hyp_parser = subparsers.add_parser('hypotheses', help='Show open hypotheses')
    hyp_parser.add_argument('-n', type=int, default=20, help='Max results')

    # Gaps
    gaps_parser = subparsers.add_parser('gaps', help='Show knowledge gaps')
    gaps_parser.add_argument('-n', type=int, default=20, help='Max results')

    # Low Confidence
    low_conf = subparsers.add_parser('low-confidence', help='Show low confidence concepts')
    low_conf.add_argument('--threshold', type=float, default=0.4, help='Confidence threshold')
    low_conf.add_argument('-n', type=int, default=30, help='Max results')

    # Active Learn (execute)
    active = subparsers.add_parser('active-learn', help='Execute active learning')
    active.add_argument('--strategy', type=str, default='ucb',
                       choices=['ucb', 'uncertainty', 'contradiction', 'hypothesis',
                               'gap', 'exploration', 'exploitation'],
                       help='Learning strategy')
    active.add_argument('--max-papers', type=int, default=50, help='Max papers per target')

    # =========================================================================
    # GRAPH ENGINE COMMANDS
    # =========================================================================

    # Graph Stats
    subparsers.add_parser('graph-stats', help='Show knowledge graph statistics')

    # Find Path
    path_parser = subparsers.add_parser('find-path', help='Find path between two claims')
    path_parser.add_argument('source', type=int, help='Source claim ID')
    path_parser.add_argument('target', type=int, help='Target claim ID')
    path_parser.add_argument('--type', type=str, default='shortest',
                            choices=['shortest', 'strongest', 'cross_domain', 'cte'],
                            help='Path type')

    # All Paths
    all_paths_parser = subparsers.add_parser('all-paths', help='Find all paths between two claims')
    all_paths_parser.add_argument('source', type=int, help='Source claim ID')
    all_paths_parser.add_argument('target', type=int, help='Target claim ID')
    all_paths_parser.add_argument('--max-depth', type=int, default=5, help='Maximum path depth')
    all_paths_parser.add_argument('-n', type=int, default=10, help='Max paths to return')

    # Centrality
    cent_parser = subparsers.add_parser('centrality', help='Show top claims by centrality')
    cent_parser.add_argument('--metric', type=str, default='pagerank',
                            choices=['pagerank', 'betweenness', 'degree', 'clustering'],
                            help='Centrality metric')
    cent_parser.add_argument('-n', type=int, default=20, help='Max results')

    # Communities
    comm_parser = subparsers.add_parser('communities', help='Detect knowledge communities')
    comm_parser.add_argument('-n', type=int, default=20, help='Max communities to show')

    # Graph Bridges
    bridges_parser = subparsers.add_parser('graph-bridges', help='Find paths bridging two domains')
    bridges_parser.add_argument('domain_a', type=str, help='First domain (math/neuro/bio/psych/med/art)')
    bridges_parser.add_argument('domain_b', type=str, help='Second domain')
    bridges_parser.add_argument('-n', type=int, default=10, help='Max paths to show')

    # Graph Hubs
    hubs_parser = subparsers.add_parser('graph-hubs', help='Find cross-domain hub claims')
    hubs_parser.add_argument('--min-domains', type=int, default=2, help='Minimum domains spanned')
    hubs_parser.add_argument('-n', type=int, default=20, help='Max results')

    # =========================================================================
    # LLM INTEGRATION COMMANDS
    # =========================================================================

    # LLM Status
    subparsers.add_parser('llm-status', help='Show LLM configuration status')

    # LLM Extract
    llm_extract_parser = subparsers.add_parser('llm-extract', help='Extract claims using LLM')
    llm_extract_parser.add_argument('text', type=str, help='Text to extract claims from')
    llm_extract_parser.add_argument('--title', type=str, default='', help='Paper title for context')

    # LLM Hypotheses
    llm_hyp_parser = subparsers.add_parser('llm-hypotheses', help='Generate hypotheses using LLM')
    llm_hyp_parser.add_argument('-n', type=int, default=5, help='Number of hypotheses')

    # LLM Analogies
    llm_analog_parser = subparsers.add_parser('llm-analogies', help='Detect cross-domain analogies')
    llm_analog_parser.add_argument('domain_a', type=str, help='First domain')
    llm_analog_parser.add_argument('domain_b', type=str, help='Second domain')
    llm_analog_parser.add_argument('-n', type=int, default=5, help='Number of analogies')

    # LLM Synthesis
    llm_synth_parser = subparsers.add_parser('llm-synthesis', help='Generate synthesis report')
    llm_synth_parser.add_argument('topic', type=str, help='Topic to synthesize')

    args = parser.parse_args()

    if args.command == 'status':
        asyncio.run(show_status())
    elif args.command == 'stats':
        asyncio.run(show_stats())
    elif args.command == 'insights':
        asyncio.run(show_insights(args.n))
    elif args.command == 'search':
        asyncio.run(search_claims(args.query, args.n))
    elif args.command == 'learn':
        asyncio.run(trigger_learn(args.domain))
    elif args.command == 'think':
        asyncio.run(show_thoughts(args.n))
    # Semantic Embedding Commands
    elif args.command == 'semantic-search':
        asyncio.run(semantic_search(args.query, args.n, args.threshold))
    elif args.command == 'embed-backfill':
        asyncio.run(embed_backfill(args.batch_size, args.limit))
    elif args.command == 'embed-stats':
        asyncio.run(embedding_stats())
    elif args.command == 'find-bridges':
        asyncio.run(find_bridges(args.threshold, args.n))
    elif args.command == 'similar':
        asyncio.run(find_similar(args.claim_id, args.n, args.cross_domain))
    # Temporal Tracking Commands
    elif args.command == 'temporal-stats':
        asyncio.run(temporal_stats())
    elif args.command == 'decay-claims':
        asyncio.run(decay_claims())
    elif args.command == 'aging-claims':
        asyncio.run(aging_claims(args.min_age, args.max_conf))
    elif args.command == 'claim-temporal':
        asyncio.run(claim_temporal(args.claim_id))
    elif args.command == 'paradigm-shifts':
        asyncio.run(detect_paradigm_shifts(args.days))
    elif args.command == 'record-replication':
        if args.partial:
            asyncio.run(record_replication(args.claim_id, success=True, partial=True))
        elif args.success:
            asyncio.run(record_replication(args.claim_id, success=True, partial=False))
        elif args.failure:
            asyncio.run(record_replication(args.claim_id, success=False, partial=False))
        else:
            print("Error: Must specify --success, --failure, or --partial")
    # Active Learning Commands
    elif args.command == 'learning-plan':
        asyncio.run(learning_plan(args.strategy, args.n))
    elif args.command == 'domain-uncertainty':
        asyncio.run(domain_uncertainty())
    elif args.command == 'contradictions':
        asyncio.run(show_contradictions(args.n))
    elif args.command == 'hypotheses':
        asyncio.run(show_hypotheses(args.n))
    elif args.command == 'gaps':
        asyncio.run(show_gaps(args.n))
    elif args.command == 'low-confidence':
        asyncio.run(low_confidence_concepts(args.threshold, args.n))
    elif args.command == 'active-learn':
        asyncio.run(active_learn(args.strategy, args.max_papers))
    # Graph Engine Commands
    elif args.command == 'graph-stats':
        asyncio.run(graph_stats())
    elif args.command == 'find-path':
        asyncio.run(find_path(args.source, args.target, args.type))
    elif args.command == 'all-paths':
        asyncio.run(all_paths(args.source, args.target, args.max_depth, args.n))
    elif args.command == 'centrality':
        asyncio.run(centrality(args.metric, args.n))
    elif args.command == 'communities':
        asyncio.run(communities(args.n))
    elif args.command == 'graph-bridges':
        asyncio.run(domain_bridges(args.domain_a, args.domain_b, args.n))
    elif args.command == 'graph-hubs':
        asyncio.run(cross_domain_hubs(args.min_domains, args.n))
    # LLM Integration Commands
    elif args.command == 'llm-status':
        asyncio.run(llm_status())
    elif args.command == 'llm-extract':
        asyncio.run(llm_extract(args.text, args.title))
    elif args.command == 'llm-hypotheses':
        asyncio.run(llm_hypotheses(args.n))
    elif args.command == 'llm-analogies':
        asyncio.run(llm_analogies(args.domain_a, args.domain_b, args.n))
    elif args.command == 'llm-synthesis':
        asyncio.run(llm_synthesis(args.topic))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
