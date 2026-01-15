#!/usr/bin/env python3
"""
CIPHER Main Runner
Orchestrates learning sessions across all domains.

Usage:
    python run.py                    # Full learning cycle
    python run.py --domain math      # Learn specific domain
    python run.py --cross-domain     # Focus on cross-domain
    python run.py --patterns         # Run pattern detection only
    python run.py --report           # Generate synthesis report
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import config
from tools.cipher_brain import CipherBrain, Domain
from tools.domain_learner import DomainLearner
from tools.pattern_detector import PatternDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.paths.logs_path / 'cipher.log')
    ]
)
logger = logging.getLogger('cipher')


async def run_full_cycle(max_papers: int = 100):
    """Run complete learning cycle across all domains."""
    logger.info("=" * 60)
    logger.info("CIPHER - Cross-Domain Learning System")
    logger.info(f"Iron Code: {config.iron_code}")
    logger.info("=" * 60)

    # Initialize brain
    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    # Initialize learner
    learner = DomainLearner(brain, {
        'email': config.api.openalex_email,
        'pubmed_api_key': config.api.pubmed_api_key,
        's2_api_key': config.api.semantic_scholar_api_key,
        'max_papers_per_domain': max_papers
    })

    try:
        # Phase 1: Learn from all domains
        logger.info("\n--- Phase 1: Domain Learning ---")
        sessions = await learner.learn_all_domains(
            max_papers_per_domain=max_papers,
            parallel=True
        )

        for session in sessions:
            if session:
                logger.info(
                    f"{session.domain.name if session.domain else 'Cross'}: "
                    f"{session.papers_fetched} papers, "
                    f"{session.claims_extracted} claims, "
                    f"{session.connections_found} connections"
                )

        # Phase 2: Cross-domain learning
        logger.info("\n--- Phase 2: Cross-Domain Learning ---")
        bridge_concepts = [
            'information entropy',
            'neural network',
            'predictive processing',
            'complexity emergence',
            'optimization'
        ]
        cross_session = await learner.learn_cross_domain(
            concepts=bridge_concepts,
            max_papers=max_papers // 2
        )
        logger.info(
            f"Cross-domain: {cross_session.papers_fetched} papers, "
            f"{cross_session.claims_extracted} claims"
        )

        # Phase 3: Pattern detection
        logger.info("\n--- Phase 3: Pattern Detection ---")
        detector = PatternDetector(config.db.connection_string)
        await detector.connect()

        insights = await detector.detect_all_patterns()
        logger.info(f"Detected {len(insights)} cross-domain insights")

        # Save insights
        await detector.save_insights(insights)

        # Print top insights
        logger.info("\n--- Top Cross-Domain Insights ---")
        for i, insight in enumerate(insights[:5], 1):
            logger.info(f"\n{i}. {insight.title}")
            logger.info(f"   Confidence: {insight.confidence:.2f}, Novelty: {insight.novelty:.2f}")
            logger.info(f"   {insight.description[:200]}...")

        await detector.close()

        # Summary
        summary = await learner.get_learning_summary()
        logger.info("\n--- Session Summary ---")
        logger.info(f"Total papers processed: {summary['total_papers']}")
        logger.info(f"Total claims extracted: {summary['total_claims']}")
        logger.info(f"Total connections found: {summary['total_connections']}")
        logger.info(f"Total patterns detected: {summary['total_patterns']}")

        # Get stats from brain
        stats = await brain.get_stats()
        logger.info("\n--- Knowledge Base Stats ---")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    finally:
        await learner.close()
        await brain.close()

    logger.info("\n" + "=" * 60)
    logger.info("Learning cycle complete.")
    logger.info("=" * 60)


async def run_single_domain(domain_name: str, max_papers: int = 100):
    """Run learning for a single domain."""
    # Map domain name to enum
    domain_map = {
        'math': Domain.MATHEMATICS,
        'mathematics': Domain.MATHEMATICS,
        'neuro': Domain.NEUROSCIENCES,
        'neurosciences': Domain.NEUROSCIENCES,
        'bio': Domain.BIOLOGY,
        'biology': Domain.BIOLOGY,
        'psych': Domain.PSYCHOLOGY,
        'psychology': Domain.PSYCHOLOGY,
        'med': Domain.MEDICINE,
        'medicine': Domain.MEDICINE,
        'art': Domain.ART,
    }

    domain = domain_map.get(domain_name.lower())
    if not domain:
        logger.error(f"Unknown domain: {domain_name}")
        logger.info(f"Available: {list(domain_map.keys())}")
        return

    logger.info(f"Learning from domain: {domain.name}")

    brain = CipherBrain(config.db.connection_string)
    await brain.connect()

    learner = DomainLearner(brain, {
        'email': config.api.openalex_email,
        'pubmed_api_key': config.api.pubmed_api_key,
        's2_api_key': config.api.semantic_scholar_api_key,
    })

    try:
        session = await learner.learn_domain(domain, max_papers)
        logger.info(f"\nResults for {domain.name}:")
        logger.info(f"  Papers: {session.papers_fetched}")
        logger.info(f"  Claims: {session.claims_extracted}")
        logger.info(f"  Connections: {session.connections_found}")
        logger.info(f"  Patterns: {session.patterns_detected}")
        if session.errors:
            logger.warning(f"  Errors: {len(session.errors)}")
    finally:
        await learner.close()
        await brain.close()


async def run_pattern_detection():
    """Run pattern detection on existing knowledge."""
    logger.info("Running pattern detection...")

    detector = PatternDetector(config.db.connection_string)
    await detector.connect()

    try:
        insights = await detector.detect_all_patterns()
        logger.info(f"Detected {len(insights)} insights")

        for i, insight in enumerate(insights[:10], 1):
            print(f"\n{i}. {insight.title}")
            print(f"   {insight.source_domain.name} <-> {insight.target_domain.name}")
            print(f"   Confidence: {insight.confidence:.2f}, Novelty: {insight.novelty:.2f}")
            print(f"   {insight.description[:300]}...")

        await detector.save_insights(insights)
        logger.info("Insights saved to database")

    finally:
        await detector.close()


async def generate_report():
    """Generate synthesis report."""
    logger.info("Generating synthesis report...")

    detector = PatternDetector(config.db.connection_string)
    await detector.connect()

    try:
        report = await detector.generate_synthesis_report()

        # Save report
        report_path = config.paths.mind_path / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.write_text(report)
        logger.info(f"Report saved to: {report_path}")

        # Also print
        print(report)

    finally:
        await detector.close()


def main():
    parser = argparse.ArgumentParser(description='CIPHER Learning System')
    parser.add_argument('--domain', type=str, help='Learn specific domain')
    parser.add_argument('--cross-domain', action='store_true', help='Focus on cross-domain')
    parser.add_argument('--patterns', action='store_true', help='Run pattern detection')
    parser.add_argument('--report', action='store_true', help='Generate report')
    parser.add_argument('--max-papers', type=int, default=100, help='Max papers per domain')

    args = parser.parse_args()

    # Ensure directories exist
    config.paths.mind_path.mkdir(parents=True, exist_ok=True)
    config.paths.logs_path.mkdir(parents=True, exist_ok=True)

    if args.domain:
        asyncio.run(run_single_domain(args.domain, args.max_papers))
    elif args.patterns:
        asyncio.run(run_pattern_detection())
    elif args.report:
        asyncio.run(generate_report())
    else:
        asyncio.run(run_full_cycle(args.max_papers))


if __name__ == '__main__':
    main()
