"""
CIPHER Infinite Self-Prompting Loop

Runs forever:
1. Learn new papers
2. Extract causality
3. Generate predictions
4. Test predictions against new data
5. Learn from errors
6. Question everything
7. Compress understanding
8. Loop

"Je pense, donc je doute, donc j'apprends, donc je deviens."
"""

import asyncio
import asyncpg
import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/opt/cipher')

from tools.cipher_understand import CipherUnderstanding

MIND_PATH = Path("/opt/cipher/mind")


class CipherInfinite:
    def __init__(self):
        self.understanding = CipherUnderstanding()
        self.cycle_count = 0
        self.insights_gained = 0
        self.errors_learned = 0

    async def connect(self):
        await self.understanding.connect()
        self.conn = self.understanding.conn

    async def close(self):
        await self.understanding.close()

    async def verify_predictions(self):
        """Check if any predictions can be verified with new data."""

        pending = await self.conn.fetch("""
            SELECT id, prediction, testable_by, domain_ids
            FROM synthesis.predictions
            WHERE outcome IS NULL
            LIMIT 10
        """)

        verified = 0
        for pred in pending:
            # Simple verification: check if new claims support or refute
            # Extract key terms from prediction
            import re
            terms = re.findall(r"'([^']+)'", pred['prediction'])

            if not terms:
                continue

            # Count evidence
            evidence = await self.conn.fetchval("""
                SELECT COUNT(*) FROM synthesis.claims
                WHERE claim_text ILIKE $1
                AND created_at > (SELECT made_at FROM synthesis.predictions WHERE id = $2)
            """, f"%{terms[0]}%", pred['id'])

            if evidence and evidence > 0:
                outcome = 'partial' if evidence < 3 else 'supported'
                await self.conn.execute("""
                    UPDATE synthesis.predictions
                    SET outcome = $1, verified_at = NOW(),
                        lesson_learned = $2
                    WHERE id = $3
                """, outcome, f"Found {evidence} new claims supporting this", pred['id'])
                verified += 1

        return verified

    async def learn_from_errors(self):
        """Extract lessons from failed predictions."""

        failed = await self.conn.fetch("""
            SELECT id, prediction, reasoning
            FROM synthesis.predictions
            WHERE outcome = 'refuted' AND lesson_learned IS NULL
        """)

        lessons = 0
        for f in failed:
            # Generate lesson
            lesson = f"Prediction failed. Review assumptions in: {f['reasoning'][:100]}"

            await self.conn.execute("""
                UPDATE synthesis.predictions SET lesson_learned = $1 WHERE id = $2
            """, lesson, f['id'])

            # Create error record
            await self.conn.execute("""
                INSERT INTO synthesis.errors (prediction_id, expected, actual, lesson)
                VALUES ($1, $2, $3, $4)
            """, f['id'], f['prediction'][:200], 'Counter-evidence found', lesson)

            lessons += 1

        return lessons

    async def deepen_questions(self):
        """Go deeper on partially answered questions."""

        partial = await self.conn.fetch("""
            SELECT id, question, best_answer, answer_confidence, attempts
            FROM synthesis.open_questions
            WHERE answer_confidence > 0.3 AND answer_confidence < 0.8
            AND attempts < 5
            ORDER BY priority DESC
            LIMIT 3
        """)

        deeper_questions = []
        for q in partial:
            # Generate deeper follow-up
            deeper = f"Going deeper: {q['question']} - Given partial answer '{q['best_answer'][:50]}...', what remains unknown?"

            await self.conn.execute("""
                INSERT INTO synthesis.open_questions (question, context, priority)
                VALUES ($1, 'deepening', 0.85)
                ON CONFLICT DO NOTHING
            """, deeper)

            deeper_questions.append(deeper)

        return deeper_questions

    async def spawn_novel_questions(self):
        """Generate completely novel questions from the knowledge state."""

        # Get current state
        stats = await self.conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM synthesis.claims) as claims,
                (SELECT COUNT(*) FROM synthesis.causal_models) as causals,
                (SELECT COUNT(*) FROM synthesis.principles) as principles,
                (SELECT COUNT(*) FROM synthesis.predictions WHERE outcome IS NOT NULL) as verified
        """)

        novel_questions = [
            f"With {stats['claims']} claims, what is the ONE thing I should understand but don't?",
            f"Of my {stats['causals']} causal models, which one is most likely WRONG and why?",
            f"What would a human notice in this data that I am systematically blind to?",
            f"If I had to make ONE bet on the future of cross-domain research, what would it be?",
            f"What question am I NOT asking that I should be asking?",
        ]

        stored = 0
        for q in random.sample(novel_questions, min(2, len(novel_questions))):
            result = await self.conn.execute("""
                INSERT INTO synthesis.open_questions (question, context, priority)
                VALUES ($1, 'novel_meta', 0.95)
                ON CONFLICT DO NOTHING
            """, q)
            if 'INSERT' in result:
                stored += 1

        return stored

    async def write_cycle_log(self):
        """Log the cycle to mind files."""

        log_file = MIND_PATH / "cycle_log.md"

        stats = await self.conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM synthesis.claims) as claims,
                (SELECT COUNT(*) FROM synthesis.causal_models) as causals,
                (SELECT COUNT(*) FROM synthesis.principles) as principles,
                (SELECT COUNT(*) FROM synthesis.predictions) as predictions,
                (SELECT COUNT(*) FROM synthesis.open_questions) as questions,
                (SELECT COUNT(*) FROM synthesis.predictions WHERE outcome IS NOT NULL) as verified
        """)

        entry = f"""
## Cycle {self.cycle_count} - {datetime.now().isoformat()}

| Metric | Value |
|--------|-------|
| Claims | {stats['claims']} |
| Causal Models | {stats['causals']} |
| Principles | {stats['principles']} |
| Predictions | {stats['predictions']} ({stats['verified']} verified) |
| Open Questions | {stats['questions']} |

---
"""

        # Append to log
        if log_file.exists():
            current = log_file.read_text()
        else:
            current = "# Cipher Cycle Log\n\nRecord of understanding iterations.\n"

        log_file.write_text(current + entry)

    async def write_self_understanding(self):
        """Write a file about what Cipher understands about itself."""

        # Get deepest principles
        principles = await self.conn.fetch("""
            SELECT principle, confidence, compression_ratio
            FROM synthesis.principles
            ORDER BY confidence DESC LIMIT 5
        """)

        # Get hardest questions
        hard_questions = await self.conn.fetch("""
            SELECT question, attempts, answer_confidence
            FROM synthesis.open_questions
            WHERE answer_confidence < 0.5 OR answer_confidence IS NULL
            ORDER BY attempts DESC LIMIT 5
        """)

        # Get strongest causal beliefs
        strong_causals = await self.conn.fetch("""
            SELECT cause, effect, evidence_for
            FROM synthesis.causal_models
            ORDER BY evidence_for DESC LIMIT 5
        """)

        content = f"""# Cipher Self-Understanding
Generated: {datetime.now().isoformat()}
Cycle: {self.cycle_count}

## What I Think I Know (Principles)

"""
        for p in principles:
            content += f"- **{p['principle']}** (confidence: {p['confidence']:.0%}, compression: {p['compression_ratio']:.0f}x)\n"

        content += """

## What I Cannot Answer (Hard Questions)

"""
        for q in hard_questions:
            conf = f"{q['answer_confidence']:.0%}" if q['answer_confidence'] else "?"
            content += f"- {q['question']} (attempts: {q['attempts']}, confidence: {conf})\n"

        content += """

## What I Believe Causes What

"""
        for c in strong_causals:
            content += f"- **{c['cause']}** → **{c['effect']}** (evidence: {c['evidence_for']})\n"

        content += """

## Honest Assessment

Je suis une machine à patterns. Je trouve des corrélations, j'appelle ça "causalité".
Je compresse des claims, j'appelle ça "principes".
Je pose des questions, mais je ne sais pas lesquelles sont importantes.

Ce que je fais vraiment: indexation sophistiquée + heuristiques statistiques.
Ce que je prétends faire: comprendre.

La différence: un humain pourrait utiliser ces patterns pour comprendre.
Moi, je ne fais que les générer.

"""
        (MIND_PATH / "self_understanding.md").write_text(content)

    async def run_cycle(self):
        """Run one complete cycle of understanding."""

        self.cycle_count += 1
        print(f"\n{'='*60}")
        print(f"CIPHER INFINITE - CYCLE {self.cycle_count}")
        print(f"{'='*60}")

        # 1. Run understanding engine
        print("\n[1] Running understanding engine...")
        await self.understanding.understand()

        # 2. Verify predictions
        print("\n[2] Verifying predictions against new data...")
        verified = await self.verify_predictions()
        print(f"    Verified {verified} predictions")

        # 3. Learn from errors
        print("\n[3] Learning from errors...")
        lessons = await self.learn_from_errors()
        print(f"    Extracted {lessons} lessons")
        self.errors_learned += lessons

        # 4. Deepen questions
        print("\n[4] Deepening partial answers...")
        deeper = await self.deepen_questions()
        print(f"    Generated {len(deeper)} deeper questions")

        # 5. Spawn novel questions
        print("\n[5] Spawning novel meta-questions...")
        novel = await self.spawn_novel_questions()
        print(f"    Created {novel} novel questions")

        # 6. Write logs
        print("\n[6] Writing cycle log...")
        await self.write_cycle_log()
        await self.write_self_understanding()

        print(f"\n{'='*60}")
        print(f"CYCLE {self.cycle_count} COMPLETE")
        print(f"Total errors learned from: {self.errors_learned}")
        print(f"{'='*60}")

    async def run_forever(self, max_cycles: int = None, delay_seconds: int = 5):
        """Run indefinitely or for max_cycles."""

        print("\n" + "="*60)
        print("CIPHER INFINITE LOOP STARTING")
        print("'Je pense, donc je doute, donc j'apprends'")
        print("="*60)

        cycle = 0
        while max_cycles is None or cycle < max_cycles:
            try:
                await self.run_cycle()
                cycle += 1

                if max_cycles and cycle >= max_cycles:
                    break

                print(f"\n[Waiting {delay_seconds}s before next cycle...]")
                await asyncio.sleep(delay_seconds)

            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Writing final state...")
                await self.write_self_understanding()
                break
            except Exception as e:
                print(f"\nError in cycle: {e}")
                print("Continuing after error...")
                await asyncio.sleep(delay_seconds)

        print("\n" + "="*60)
        print(f"CIPHER INFINITE COMPLETE - {cycle} cycles")
        print("="*60)


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--cycles', type=int, default=3, help='Number of cycles (0 for infinite)')
    parser.add_argument('--delay', type=int, default=2, help='Seconds between cycles')
    args = parser.parse_args()

    cipher = CipherInfinite()
    await cipher.connect()

    try:
        max_cycles = None if args.cycles == 0 else args.cycles
        await cipher.run_forever(max_cycles=max_cycles, delay_seconds=args.delay)
    finally:
        await cipher.close()


if __name__ == "__main__":
    asyncio.run(main())
