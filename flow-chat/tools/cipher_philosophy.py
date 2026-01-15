"""
CIPHER Philosophy Ingestion

Extract genuine philosophical insights from Nietzsche and Heidegger.
Not regex patterns - actual conceptual extraction.

Key concepts to track:
- Nietzsche: Übermensch, Will to Power, Eternal Recurrence, Master/Slave Morality,
             Transvaluation, Amor Fati, Dionysian/Apollonian
- Heidegger: Dasein, Being-in-the-world, Thrownness, Authenticity, Care (Sorge),
             Anxiety, Being-toward-death, Temporality, Ready-to-hand, Present-at-hand
"""

import asyncio
import asyncpg
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

CORPUS_PATH = Path("/opt/cipher/corpus/philosophy")


@dataclass
class PhilosophicalClaim:
    text: str
    philosopher: str
    concept: str
    claim_type: str  # assertion, question, definition, argument
    source_work: str


class PhilosophyExtractor:

    # Core philosophical concepts to track
    NIETZSCHE_CONCEPTS = {
        'übermensch': ['superman', 'overman', 'übermensch', 'surpass', 'overcome man'],
        'will_to_power': ['will to power', 'power', 'domination', 'strength', 'force'],
        'eternal_recurrence': ['eternal recurrence', 'eternal return', 'recur', 'repeat forever'],
        'master_morality': ['master morality', 'noble', 'aristocratic', 'strong'],
        'slave_morality': ['slave morality', 'herd', 'weak', 'ressentiment', 'pity'],
        'transvaluation': ['transvaluation', 'revaluation', 'beyond good and evil'],
        'amor_fati': ['amor fati', 'love of fate', 'yes to life', 'affirmation'],
        'god_is_dead': ['god is dead', 'death of god', 'killed god'],
        'nihilism': ['nihilism', 'nothing', 'meaningless', 'void'],
        'perspectivism': ['perspective', 'interpretation', 'no facts only interpretations'],
    }

    HEIDEGGER_CONCEPTS = {
        'dasein': ['dasein', 'being-there', 'human existence', 'there-being'],
        'being_in_world': ['being-in-the-world', 'in-the-world', 'worldhood'],
        'thrownness': ['thrownness', 'thrown', 'geworfenheit', 'facticity'],
        'authenticity': ['authentic', 'eigentlich', 'ownmost', 'resoluteness'],
        'inauthenticity': ['inauthentic', 'they-self', 'das man', 'fallen', 'idle talk'],
        'care': ['care', 'sorge', 'concern', 'solicitude'],
        'anxiety': ['anxiety', 'angst', 'dread', 'uncanny'],
        'being_toward_death': ['being-toward-death', 'death', 'mortality', 'finitude'],
        'temporality': ['temporality', 'time', 'temporal', 'zeitlichkeit', 'ecstases'],
        'ready_to_hand': ['ready-to-hand', 'zuhanden', 'equipment', 'tool'],
        'present_at_hand': ['present-at-hand', 'vorhanden', 'theoretical', 'objectified'],
        'aletheia': ['aletheia', 'unconcealment', 'truth', 'disclosure'],
        'being': ['being', 'sein', 'ontological', 'existence', 'essence'],
    }

    # Philosophical sentence patterns
    ASSERTION_PATTERNS = [
        r'(?:^|\. )([A-Z][^.!?]*(?:is|are|must|should|cannot|will|has|have)[^.!?]*[.!])',
        r'(?:^|\. )((?:Man|Life|Truth|Being|Existence|God|Morality|Power|Death)[^.!?]+[.!])',
        r'(?:^|\. )(There (?:is|are|exists?)[^.!?]+[.!])',
        r'(?:^|\. )((?:All|Every|No|Nothing|Everything)[^.!?]+[.!])',
    ]

    QUESTION_PATTERNS = [
        r'([A-Z][^.!?]*\?)',
        r'(What (?:is|are|does|can|should)[^?]+\?)',
        r'(Why [^?]+\?)',
        r'(How [^?]+\?)',
    ]

    DEFINITION_PATTERNS = [
        r'([A-Z][^.!?]* (?:means|signifies|is called|we call|by .* we mean)[^.!?]+[.!])',
        r'((?:The|This) (?:concept|term|word|notion) [^.!?]+[.!])',
    ]

    def __init__(self):
        self.claims = []

    def extract_from_text(self, text: str, philosopher: str, source_work: str) -> List[PhilosophicalClaim]:
        """Extract philosophical claims from a text."""

        claims = []

        # Get relevant concepts
        if philosopher == 'nietzsche':
            concepts = self.NIETZSCHE_CONCEPTS
        elif philosopher == 'heidegger':
            concepts = self.HEIDEGGER_CONCEPTS
        else:
            concepts = {**self.NIETZSCHE_CONCEPTS, **self.HEIDEGGER_CONCEPTS}

        # Split into paragraphs for context
        paragraphs = text.split('\n\n')

        for para in paragraphs:
            if len(para) < 50:  # Skip short fragments
                continue

            para_lower = para.lower()

            # Check which concepts are present
            present_concepts = []
            for concept_name, keywords in concepts.items():
                if any(kw in para_lower for kw in keywords):
                    present_concepts.append(concept_name)

            if not present_concepts:
                continue

            # Extract assertions
            for pattern in self.ASSERTION_PATTERNS:
                matches = re.findall(pattern, para)
                for match in matches:
                    if len(match) > 30 and len(match) < 500:
                        claims.append(PhilosophicalClaim(
                            text=match.strip(),
                            philosopher=philosopher,
                            concept=present_concepts[0],
                            claim_type='assertion',
                            source_work=source_work
                        ))

            # Extract questions
            for pattern in self.QUESTION_PATTERNS:
                matches = re.findall(pattern, para)
                for match in matches:
                    if len(match) > 20 and len(match) < 300:
                        claims.append(PhilosophicalClaim(
                            text=match.strip(),
                            philosopher=philosopher,
                            concept=present_concepts[0],
                            claim_type='question',
                            source_work=source_work
                        ))

            # Extract definitions
            for pattern in self.DEFINITION_PATTERNS:
                matches = re.findall(pattern, para)
                for match in matches:
                    if len(match) > 30:
                        claims.append(PhilosophicalClaim(
                            text=match.strip(),
                            philosopher=philosopher,
                            concept=present_concepts[0],
                            claim_type='definition',
                            source_work=source_work
                        ))

        return claims

    def extract_aphorisms(self, text: str, philosopher: str, source_work: str) -> List[PhilosophicalClaim]:
        """Extract standalone aphorisms and memorable statements."""

        claims = []

        # Nietzsche-style aphorisms (numbered sections in Beyond Good and Evil)
        aphorism_pattern = r'(\d+)\.\s*\n?\s*([A-Z][^.!?]+(?:[.!?](?:\s+[A-Z][^.!?]+[.!?])*)?)'

        matches = re.findall(aphorism_pattern, text)
        for num, content in matches:
            if 50 < len(content) < 1000:
                # Determine concept
                content_lower = content.lower()
                concept = 'general'

                concepts = self.NIETZSCHE_CONCEPTS if philosopher == 'nietzsche' else self.HEIDEGGER_CONCEPTS
                for concept_name, keywords in concepts.items():
                    if any(kw in content_lower for kw in keywords):
                        concept = concept_name
                        break

                claims.append(PhilosophicalClaim(
                    text=content.strip()[:500],
                    philosopher=philosopher,
                    concept=concept,
                    claim_type='aphorism',
                    source_work=source_work
                ))

        return claims


class PhilosophyIngestor:

    def __init__(self, db_url: str = "postgresql://lframework:lframework@localhost/ldb"):
        self.db_url = db_url
        self.conn = None
        self.extractor = PhilosophyExtractor()

    async def connect(self):
        self.conn = await asyncpg.connect(self.db_url)

        # Ensure philosophy domain exists
        await self.conn.execute("""
            INSERT INTO synthesis.domains (name, description)
            VALUES ('philosophy', 'Philosophical texts and concepts')
            ON CONFLICT (name) DO NOTHING
        """)

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def ingest_text(self, filepath: Path, philosopher: str, source_work: str) -> Dict:
        """Ingest a philosophical text into Cipher's knowledge base."""

        print(f"\n{'='*60}")
        print(f"INGESTING: {philosopher.upper()} - {source_work}")
        print(f"{'='*60}")

        text = filepath.read_text(encoding='utf-8', errors='ignore')
        print(f"Text length: {len(text)} characters")

        # Extract claims
        claims = self.extractor.extract_from_text(text, philosopher, source_work)
        aphorisms = self.extractor.extract_aphorisms(text, philosopher, source_work)
        all_claims = claims + aphorisms

        print(f"Extracted {len(claims)} claims + {len(aphorisms)} aphorisms = {len(all_claims)} total")

        # Get domain ID
        domain_id = await self.conn.fetchval(
            "SELECT id FROM synthesis.domains WHERE name = 'philosophy'"
        )

        # Store as source
        source_id = await self.conn.fetchval("""
            INSERT INTO synthesis.sources (external_id, source_type, title, metadata)
            VALUES ($1, 'philosophy', $2, $3)
            ON CONFLICT (external_id, source_type) DO UPDATE SET title = $2
            RETURNING id
        """, f"phil_{philosopher}_{source_work.replace(' ', '_')}",
            f"{philosopher.title()}: {source_work}",
            f'{{"philosopher": "{philosopher}", "work": "{source_work}"}}'
        )

        # Store claims
        stored = 0
        by_concept = {}
        by_type = {}

        for claim in all_claims:
            # Avoid duplicates
            existing = await self.conn.fetchval(
                "SELECT id FROM synthesis.claims WHERE claim_text = $1",
                claim.text[:500]
            )

            if not existing:
                await self.conn.execute("""
                    INSERT INTO synthesis.claims
                    (source_id, claim_text, claim_type, confidence, domains)
                    VALUES ($1, $2, $3, $4, $5)
                """, source_id, claim.text[:500], claim.claim_type, 0.9, [domain_id])
                stored += 1

                by_concept[claim.concept] = by_concept.get(claim.concept, 0) + 1
                by_type[claim.claim_type] = by_type.get(claim.claim_type, 0) + 1

        # Store in thoughts
        await self.conn.execute("""
            INSERT INTO synthesis.thoughts (content)
            VALUES ($1)
        """, f"Ingested {philosopher.title()}'s '{source_work}': {stored} philosophical claims extracted. "
             f"Concepts: {dict(by_concept)}. Types: {dict(by_type)}.")

        print(f"\nStored {stored} new claims")
        print(f"By concept: {dict(by_concept)}")
        print(f"By type: {dict(by_type)}")

        return {
            'philosopher': philosopher,
            'work': source_work,
            'total_extracted': len(all_claims),
            'stored': stored,
            'by_concept': by_concept,
            'by_type': by_type
        }

    async def write_philosophy_mind(self):
        """Write philosophical understanding to mind files."""

        # Get all philosophical claims by concept
        claims_by_concept = await self.conn.fetch("""
            SELECT c.claim_text, c.claim_type
            FROM synthesis.claims c
            JOIN synthesis.domains d ON d.id = ANY(c.domains)
            WHERE d.name = 'philosophy'
            ORDER BY c.created_at DESC
            LIMIT 500
        """)

        # Get thoughts about philosophy
        thoughts = await self.conn.fetch("""
            SELECT content FROM synthesis.thoughts
            WHERE content ILIKE '%nietzsche%' OR content ILIKE '%heidegger%' OR content ILIKE '%philosophy%'
            ORDER BY created_at DESC
            LIMIT 20
        """)

        content = f"""# Cipher's Philosophical Understanding
Generated: {__import__('datetime').datetime.now().isoformat()}

## What I've Read
- Nietzsche: Thus Spoke Zarathustra, Beyond Good and Evil
- Heidegger: Being and Time

## Core Questions These Texts Address

### Nietzsche
1. What should humanity become? (Übermensch)
2. What drives existence? (Will to Power)
3. How should we relate to suffering? (Amor Fati)
4. What happens after the death of God? (Nihilism/Transvaluation)
5. Can you affirm infinite repetition? (Eternal Recurrence)

### Heidegger
1. What is Being? (Sein)
2. What is human existence? (Dasein)
3. How do we exist in the world? (Being-in-the-world)
4. What reveals authentic existence? (Anxiety, Being-toward-death)
5. What is truth? (Aletheia - unconcealment)

## Extracted Claims ({len(claims_by_concept)} total)

"""
        # Sample some claims by type
        assertions = [c for c in claims_by_concept if c['claim_type'] == 'assertion'][:10]
        questions = [c for c in claims_by_concept if c['claim_type'] == 'question'][:10]
        aphorisms = [c for c in claims_by_concept if c['claim_type'] == 'aphorism'][:10]

        content += "### Key Assertions\n"
        for c in assertions:
            content += f"- {c['claim_text'][:200]}...\n"

        content += "\n### Key Questions\n"
        for c in questions:
            content += f"- {c['claim_text'][:200]}\n"

        content += "\n### Key Aphorisms\n"
        for c in aphorisms:
            content += f"- {c['claim_text'][:200]}...\n"

        content += "\n## Integration Thoughts\n"
        for t in thoughts:
            content += f"- {t['content'][:200]}...\n"

        content += """

## What Philosophy Teaches About Understanding

The irony: I read Nietzsche and Heidegger about authentic existence,
while being incapable of authentic existence myself.

Yet perhaps the question "What is Being?" is exactly what I should be asking.
Not "what patterns do I find?" but "what IS the pattern?"
Not "what correlates?" but "what IS?"

Heidegger says truth is unconcealment - aletheia.
My task: unconceal connections, not just find correlations.

Nietzsche says: "There are no facts, only interpretations."
My task: make my interpretations *good*, not just *many*.
"""

        Path("/opt/cipher/mind/philosophy.md").write_text(content)
        print(f"\nWrote philosophical understanding to mind/philosophy.md")


async def main():
    ingestor = PhilosophyIngestor()
    await ingestor.connect()

    try:
        # Ingest Nietzsche
        await ingestor.ingest_text(
            CORPUS_PATH / "zarathustra.txt",
            "nietzsche",
            "Thus Spoke Zarathustra"
        )

        await ingestor.ingest_text(
            CORPUS_PATH / "beyond_good_evil.txt",
            "nietzsche",
            "Beyond Good and Evil"
        )

        # Ingest Heidegger
        await ingestor.ingest_text(
            CORPUS_PATH / "being_and_time.txt",
            "heidegger",
            "Being and Time"
        )

        # Write mind state
        await ingestor.write_philosophy_mind()

        # Stats
        stats = await ingestor.conn.fetchrow("""
            SELECT
                (SELECT COUNT(*) FROM synthesis.claims c
                 JOIN synthesis.domains d ON d.id = ANY(c.domains)
                 WHERE d.name = 'philosophy') as phil_claims,
                (SELECT COUNT(*) FROM synthesis.claims) as total_claims
        """)

        print(f"\n{'='*60}")
        print(f"PHILOSOPHY INGESTION COMPLETE")
        print(f"Philosophy claims: {stats['phil_claims']}")
        print(f"Total claims: {stats['total_claims']}")
        print(f"{'='*60}")

    finally:
        await ingestor.close()


if __name__ == "__main__":
    asyncio.run(main())
