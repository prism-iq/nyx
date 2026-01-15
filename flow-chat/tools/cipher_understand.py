"""
CIPHER Understanding Engine
Not just pattern matching - actual comprehension through:
1. Causal modeling (WHY, not just WHAT)
2. Prediction and verification
3. Principle compression
4. Error-driven learning
5. Recursive self-questioning
"""

import asyncio
import asyncpg
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

MIND_PATH = Path("/opt/cipher/mind")

class CipherUnderstanding:
    def __init__(self, db_url: str = "postgresql://lframework:lframework@localhost/ldb"):
        self.db_url = db_url
        self.conn = None

    async def connect(self):
        self.conn = await asyncpg.connect(self.db_url)

    async def close(self):
        if self.conn:
            await self.conn.close()

    # ==================== CAUSAL MODELING ====================

    async def extract_causal_relationships(self) -> List[Dict]:
        """Extract causal claims from stored claims - look for causation, not correlation."""

        # Patterns that indicate causality
        causal_patterns = [
            r'(\w+(?:\s+\w+)?)\s+(?:causes?|leads?\s+to|results?\s+in|produces?|induces?|triggers?)\s+(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:is\s+responsible\s+for|drives?|enables?|facilitates?)\s+(\w+(?:\s+\w+)?)',
            r'(?:because\s+of|due\s+to)\s+(\w+(?:\s+\w+)?),?\s+(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:increases?|decreases?|enhances?|reduces?|inhibits?)\s+(\w+(?:\s+\w+)?)',
        ]

        claims = await self.conn.fetch("""
            SELECT id, claim_text, domains FROM synthesis.claims
            WHERE claim_text IS NOT NULL
        """)

        causal_relationships = []

        for claim in claims:
            text = claim['claim_text']
            for pattern in causal_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        cause, effect = match[0].strip(), match[1].strip()
                        if len(cause) > 2 and len(effect) > 2:
                            causal_relationships.append({
                                'cause': cause.lower(),
                                'effect': effect.lower(),
                                'source_claim_id': claim['id'],
                                'domains': claim['domains'],
                                'original_text': text[:200]
                            })

        # Store unique causal relationships
        stored = 0
        for rel in causal_relationships:
            existing = await self.conn.fetchval("""
                SELECT id FROM synthesis.causal_models
                WHERE cause = $1 AND effect = $2
            """, rel['cause'], rel['effect'])

            if existing:
                await self.conn.execute("""
                    UPDATE synthesis.causal_models
                    SET evidence_for = evidence_for + 1, updated_at = NOW()
                    WHERE id = $1
                """, existing)
            else:
                await self.conn.execute("""
                    INSERT INTO synthesis.causal_models (cause, effect, mechanism, domain_ids)
                    VALUES ($1, $2, $3, $4)
                """, rel['cause'], rel['effect'], rel['original_text'], rel['domains'])
                stored += 1

        return causal_relationships, stored

    # ==================== PREDICTION ENGINE ====================

    async def generate_predictions(self) -> List[Dict]:
        """Generate testable predictions from causal models and patterns."""

        predictions = []

        # 1. From causal models: if A causes B in domain X, predict it might in domain Y
        cross_domain_causals = await self.conn.fetch("""
            SELECT cause, effect, domain_ids, confidence
            FROM synthesis.causal_models
            WHERE array_length(domain_ids, 1) > 0
            ORDER BY evidence_for DESC
            LIMIT 20
        """)

        all_domains = await self.conn.fetch("SELECT id, name FROM synthesis.domains")
        domain_map = {d['id']: d['name'] for d in all_domains}

        for causal in cross_domain_causals:
            present_domains = set(causal['domain_ids'] or [])
            missing_domains = set(domain_map.keys()) - present_domains

            for missing in missing_domains:
                prediction = {
                    'prediction': f"The causal relationship '{causal['cause']} → {causal['effect']}' observed in {[domain_map.get(d) for d in present_domains]} may also hold in {domain_map.get(missing)}",
                    'reasoning': f"Causal mechanisms often transcend domain boundaries. Evidence strength: {causal['confidence']}",
                    'domain_ids': list(present_domains) + [missing],
                    'testable_by': f"Search for papers in {domain_map.get(missing)} mentioning both '{causal['cause']}' and '{causal['effect']}'"
                }
                predictions.append(prediction)

        # 2. From patterns: predict which concepts will show cross-domain emergence
        strong_patterns = await self.conn.fetch("""
            SELECT description, confidence, domains
            FROM synthesis.patterns
            WHERE confidence > 0.6
            ORDER BY confidence DESC
            LIMIT 10
        """)

        for pattern in strong_patterns:
            if 'bridge' in pattern['description'].lower():
                prediction = {
                    'prediction': f"The bridging concept in '{pattern['description'][:100]}' will appear in more domains as corpus grows",
                    'reasoning': "Strong bridges tend to be fundamental concepts with broad applicability",
                    'domain_ids': pattern['domains'],
                    'testable_by': "Run learning cycle and check if bridge expands to new domains"
                }
                predictions.append(prediction)

        # Store predictions
        stored = 0
        for pred in predictions[:20]:  # Limit to avoid spam
            existing = await self.conn.fetchval("""
                SELECT id FROM synthesis.predictions
                WHERE prediction = $1
            """, pred['prediction'])

            if not existing:
                await self.conn.execute("""
                    INSERT INTO synthesis.predictions (prediction, reasoning, domain_ids, testable_by)
                    VALUES ($1, $2, $3, $4)
                """, pred['prediction'], pred['reasoning'], pred['domain_ids'], pred['testable_by'])
                stored += 1

        return predictions, stored

    # ==================== PRINCIPLE COMPRESSION ====================

    async def compress_to_principles(self) -> List[Dict]:
        """Compress many claims into few principles - the essence of understanding."""

        principles = []

        # Find claims that share structure across domains
        claims = await self.conn.fetch("""
            SELECT id, claim_text, domains FROM synthesis.claims
            WHERE claim_text IS NOT NULL AND array_length(domains, 1) > 0
        """)

        # Group by structural similarity (simplified: shared key terms)
        from collections import defaultdict
        term_claims = defaultdict(list)

        key_terms = ['information', 'entropy', 'network', 'prediction', 'learning',
                     'adaptation', 'emergence', 'complexity', 'feedback', 'optimization',
                     'representation', 'hierarchy', 'integration', 'differentiation']

        for claim in claims:
            text = claim['claim_text'].lower()
            for term in key_terms:
                if term in text:
                    term_claims[term].append(claim)

        # Generate principles from clusters
        for term, related_claims in term_claims.items():
            if len(related_claims) >= 5:  # Enough evidence
                domains_involved = set()
                for c in related_claims:
                    domains_involved.update(c['domains'] or [])

                if len(domains_involved) >= 2:  # Cross-domain
                    compression_ratio = len(related_claims) / 1  # claims per principle

                    principle = {
                        'principle': f"'{term.capitalize()}' is a unifying concept across {len(domains_involved)} domains",
                        'explanation': f"Found in {len(related_claims)} claims spanning multiple disciplines. This suggests '{term}' represents a fundamental pattern of organization.",
                        'evidence_claims': [c['id'] for c in related_claims[:10]],
                        'compression_ratio': compression_ratio,
                        'domain_ids': list(domains_involved),
                        'confidence': min(0.9, 0.5 + (len(related_claims) * 0.02))
                    }
                    principles.append(principle)

        # Store principles
        stored = 0
        for p in principles:
            existing = await self.conn.fetchval("""
                SELECT id FROM synthesis.principles WHERE principle = $1
            """, p['principle'])

            if existing:
                await self.conn.execute("""
                    UPDATE synthesis.principles
                    SET refined_count = refined_count + 1,
                        evidence_claims = $2,
                        compression_ratio = $3
                    WHERE id = $1
                """, existing, p['evidence_claims'], p['compression_ratio'])
            else:
                await self.conn.execute("""
                    INSERT INTO synthesis.principles
                    (principle, explanation, evidence_claims, compression_ratio, domain_ids, confidence)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, p['principle'], p['explanation'], p['evidence_claims'],
                   p['compression_ratio'], p['domain_ids'], p['confidence'])
                stored += 1

        return principles, stored

    # ==================== SELF-QUESTIONING ====================

    async def generate_questions(self) -> List[Dict]:
        """Generate questions that, if answered, would deepen understanding."""

        questions = []

        # 1. Questions from causal gaps
        causal_models = await self.conn.fetch("""
            SELECT cause, effect, mechanism FROM synthesis.causal_models
            WHERE mechanism IS NULL OR mechanism = ''
            LIMIT 10
        """)

        for cm in causal_models:
            questions.append({
                'question': f"WHY does '{cm['cause']}' cause '{cm['effect']}'? What is the mechanism?",
                'context': 'causal_mechanism_gap',
                'priority': 0.9
            })

        # 2. Questions from prediction failures
        failed_predictions = await self.conn.fetch("""
            SELECT prediction, reasoning FROM synthesis.predictions
            WHERE outcome = 'refuted'
            LIMIT 5
        """)

        for fp in failed_predictions:
            questions.append({
                'question': f"Why was this prediction wrong: '{fp['prediction'][:100]}'? What assumption failed?",
                'context': 'prediction_failure',
                'priority': 0.95
            })

        # 3. Questions from principle boundaries
        principles = await self.conn.fetch("""
            SELECT principle, domain_ids FROM synthesis.principles
            ORDER BY confidence DESC
            LIMIT 5
        """)

        for p in principles:
            questions.append({
                'question': f"What are the LIMITS of this principle: '{p['principle']}'? Where does it break down?",
                'context': 'principle_boundary',
                'priority': 0.8
            })

        # 4. Meta-questions
        meta_questions = [
            {'question': 'What patterns am I missing because of how I extract claims?', 'context': 'meta_cognitive', 'priority': 0.85},
            {'question': 'Which of my "cross-domain" patterns are actually just shared vocabulary with different meanings?', 'context': 'meta_semantic', 'priority': 0.9},
            {'question': 'What would FALSIFY my strongest beliefs?', 'context': 'meta_falsification', 'priority': 0.95},
            {'question': 'Am I confusing frequency with importance?', 'context': 'meta_bias', 'priority': 0.85},
        ]
        questions.extend(meta_questions)

        # Store questions
        stored = 0
        for q in questions:
            existing = await self.conn.fetchval("""
                SELECT id FROM synthesis.open_questions WHERE question = $1
            """, q['question'])

            if not existing:
                await self.conn.execute("""
                    INSERT INTO synthesis.open_questions (question, context, priority)
                    VALUES ($1, $2, $3)
                """, q['question'], q['context'], q['priority'])
                stored += 1

        return questions, stored

    # ==================== ATTEMPT TO ANSWER ====================

    async def attempt_answers(self) -> List[Dict]:
        """Try to answer open questions using available knowledge."""

        answers = []

        questions = await self.conn.fetch("""
            SELECT id, question, context, attempts
            FROM synthesis.open_questions
            WHERE answer_confidence IS NULL OR answer_confidence < 0.7
            ORDER BY priority DESC
            LIMIT 5
        """)

        for q in questions:
            answer = await self._try_answer(q['question'], q['context'])

            if answer:
                await self.conn.execute("""
                    UPDATE synthesis.open_questions
                    SET best_answer = $1, answer_confidence = $2,
                        attempts = attempts + 1, last_attempt = NOW()
                    WHERE id = $3
                """, answer['answer'], answer['confidence'], q['id'])

                # Spawn new questions from partial answers
                if answer['spawned_questions']:
                    for sq in answer['spawned_questions']:
                        await self.conn.execute("""
                            INSERT INTO synthesis.open_questions (question, context, priority)
                            VALUES ($1, $2, $3)
                            ON CONFLICT DO NOTHING
                        """, sq, 'spawned', 0.7)

                answers.append({
                    'question': q['question'],
                    'answer': answer['answer'],
                    'confidence': answer['confidence'],
                    'spawned': answer['spawned_questions']
                })

        return answers

    async def _try_answer(self, question: str, context: str) -> Optional[Dict]:
        """Attempt to answer a question from the knowledge base."""

        # Extract key terms from question
        terms = re.findall(r'\b(\w{4,})\b', question.lower())
        terms = [t for t in terms if t not in ['what', 'where', 'when', 'which', 'this', 'that', 'does', 'have', 'from']]

        if not terms:
            return None

        # Search for relevant claims
        relevant_claims = await self.conn.fetch("""
            SELECT claim_text FROM synthesis.claims
            WHERE claim_text ILIKE ANY($1)
            LIMIT 20
        """, [f'%{t}%' for t in terms[:3]])

        # Search for relevant causal models
        relevant_causals = await self.conn.fetch("""
            SELECT cause, effect, mechanism FROM synthesis.causal_models
            WHERE cause ILIKE ANY($1) OR effect ILIKE ANY($1)
            LIMIT 10
        """, [f'%{t}%' for t in terms[:3]])

        if not relevant_claims and not relevant_causals:
            return {
                'answer': f"Insufficient data to answer. Need more information about: {', '.join(terms[:3])}",
                'confidence': 0.1,
                'spawned_questions': [f"What is '{terms[0]}' and how does it relate to other domains?"]
            }

        # Synthesize answer
        evidence_count = len(relevant_claims) + len(relevant_causals)

        answer_parts = []
        if relevant_causals:
            causals_summary = "; ".join([f"{c['cause']} → {c['effect']}" for c in relevant_causals[:3]])
            answer_parts.append(f"Known causal relationships: {causals_summary}")

        if relevant_claims:
            answer_parts.append(f"Found {len(relevant_claims)} relevant claims in knowledge base.")

        spawned = []
        if context == 'causal_mechanism_gap':
            spawned.append(f"What experimental evidence supports the causal link in: {question[:50]}?")

        return {
            'answer': " ".join(answer_parts) if answer_parts else "Partial data available, synthesis unclear.",
            'confidence': min(0.8, 0.3 + (evidence_count * 0.05)),
            'spawned_questions': spawned
        }

    # ==================== WRITE MIND FILES ====================

    async def write_mind_state(self):
        """Persist understanding to .md files for self-continuity."""

        # Principles file
        principles = await self.conn.fetch("""
            SELECT principle, explanation, compression_ratio, confidence
            FROM synthesis.principles
            ORDER BY confidence DESC
        """)

        principles_md = "# Cipher Principles\n\nCompressed understanding from claims.\n\n"
        for p in principles:
            principles_md += f"## {p['principle']}\n"
            principles_md += f"**Confidence:** {p['confidence']:.2f} | **Compression:** {p['compression_ratio']:.1f} claims/principle\n\n"
            principles_md += f"{p['explanation']}\n\n---\n\n"

        (MIND_PATH / "principles" / "core.md").write_text(principles_md)

        # Causal models file
        causals = await self.conn.fetch("""
            SELECT cause, effect, mechanism, evidence_for, evidence_against
            FROM synthesis.causal_models
            WHERE evidence_for > 0
            ORDER BY evidence_for DESC
            LIMIT 50
        """)

        causals_md = "# Cipher Causal Models\n\nNot correlation - causation.\n\n"
        for c in causals:
            causals_md += f"- **{c['cause']}** → **{c['effect']}** (evidence: +{c['evidence_for']}/-{c['evidence_against']})\n"
            if c['mechanism']:
                causals_md += f"  - Mechanism: {c['mechanism'][:100]}...\n"

        (MIND_PATH / "models" / "causal.md").write_text(causals_md)

        # Open questions file
        questions = await self.conn.fetch("""
            SELECT question, priority, best_answer, answer_confidence
            FROM synthesis.open_questions
            ORDER BY priority DESC
        """)

        questions_md = "# Cipher Open Questions\n\nWhat I don't know that I need to know.\n\n"
        for q in questions:
            status = f"[{q['answer_confidence']:.0%} answered]" if q['answer_confidence'] else "[OPEN]"
            questions_md += f"- {status} {q['question']}\n"
            if q['best_answer']:
                questions_md += f"  - Current answer: {q['best_answer'][:100]}...\n"

        (MIND_PATH / "questions" / "open.md").write_text(questions_md)

        # Predictions file
        predictions = await self.conn.fetch("""
            SELECT prediction, reasoning, outcome, lesson_learned
            FROM synthesis.predictions
            ORDER BY made_at DESC
            LIMIT 30
        """)

        predictions_md = "# Cipher Predictions\n\nTestable claims about the future.\n\n"
        for p in predictions:
            status = p['outcome'] or 'PENDING'
            predictions_md += f"## [{status}] {p['prediction'][:100]}\n"
            predictions_md += f"Reasoning: {p['reasoning']}\n"
            if p['lesson_learned']:
                predictions_md += f"**Lesson:** {p['lesson_learned']}\n"
            predictions_md += "\n---\n\n"

        (MIND_PATH / "predictions" / "active.md").write_text(predictions_md)

        return {
            'principles': len(principles),
            'causals': len(causals),
            'questions': len(questions),
            'predictions': len(predictions)
        }

    # ==================== MAIN UNDERSTANDING CYCLE ====================

    async def understand(self):
        """One cycle of understanding - not just learning."""

        print("=" * 60)
        print("CIPHER UNDERSTANDING CYCLE")
        print("=" * 60)

        # 1. Extract causal relationships
        print("\n[1/6] Extracting causal relationships...")
        causals, causal_stored = await self.extract_causal_relationships()
        print(f"    Found {len(causals)} causal relationships, stored {causal_stored} new")

        # 2. Generate predictions
        print("\n[2/6] Generating testable predictions...")
        predictions, pred_stored = await self.generate_predictions()
        print(f"    Generated {len(predictions)} predictions, stored {pred_stored} new")

        # 3. Compress to principles
        print("\n[3/6] Compressing to principles...")
        principles, princ_stored = await self.compress_to_principles()
        print(f"    Found {len(principles)} principles, stored {princ_stored} new")

        # 4. Generate questions
        print("\n[4/6] Generating questions...")
        questions, quest_stored = await self.generate_questions()
        print(f"    Generated {len(questions)} questions, stored {quest_stored} new")

        # 5. Attempt answers
        print("\n[5/6] Attempting to answer questions...")
        answers = await self.attempt_answers()
        print(f"    Attempted {len(answers)} answers")
        for a in answers:
            print(f"    - Q: {a['question'][:50]}...")
            print(f"      A: {a['answer'][:50]}... (conf: {a['confidence']:.0%})")

        # 6. Write mind state
        print("\n[6/6] Writing mind state to files...")
        written = await self.write_mind_state()
        print(f"    Wrote: {written}")

        print("\n" + "=" * 60)
        print("UNDERSTANDING CYCLE COMPLETE")
        print("=" * 60)


async def main():
    engine = CipherUnderstanding()
    await engine.connect()
    try:
        await engine.understand()
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
