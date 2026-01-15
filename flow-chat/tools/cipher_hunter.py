"""
CIPHER HUNTER - Esprit Shonen Edition

Je ne cherche pas des patterns.
Je chasse LA connexion.

"La nature est cool" - on cherche ce qu'elle a compris avant nous.
"""

import asyncio
import asyncpg
import math
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

MIND_PATH = Path("/opt/cipher/mind")


@dataclass
class Lead:
    """Une piste. Pas un pattern. Une PISTE."""
    description: str
    domains: List[str]
    improbability: float  # Plus c'est fou, mieux c'est
    potential_impact: float  # Pourrait sauver des vies ?
    novelty: float  # Personne ne l'a vu ?
    evidence: List[str]  # Claims qui supportent
    shonen_score: float = 0.0

    def __post_init__(self):
        # SHONEN SCORE = improbabilité × impact × nouveauté
        self.shonen_score = self.improbability * self.potential_impact * self.novelty


class CipherHunter:
    """
    Je suis un chasseur.

    Pas une bibliothèque qui classe.
    Un chasseur qui traque.
    """

    # Distances entre domaines (plus c'est loin, plus c'est intéressant)
    DOMAIN_DISTANCES = {
        ('mathematics', 'art'): 0.9,
        ('mathematics', 'medicine'): 0.8,
        ('mathematics', 'psychology'): 0.7,
        ('mathematics', 'neurosciences'): 0.6,
        ('mathematics', 'biology'): 0.5,
        ('neurosciences', 'art'): 0.85,
        ('neurosciences', 'mathematics'): 0.6,
        ('biology', 'art'): 0.9,
        ('biology', 'psychology'): 0.6,
        ('medicine', 'art'): 0.95,  # Très improbable = très intéressant
        ('medicine', 'mathematics'): 0.8,
        ('psychology', 'art'): 0.5,
        ('psychology', 'biology'): 0.6,
    }

    # Concepts qui pourraient avoir un impact médical
    MEDICAL_IMPACT_KEYWORDS = [
        'disease', 'therapy', 'treatment', 'cure', 'healing',
        'symptom', 'diagnosis', 'patient', 'clinical', 'drug',
        'inflammation', 'immune', 'cancer', 'tumor', 'infection',
        'neurodegenerative', 'alzheimer', 'parkinson', 'depression',
        'anxiety', 'autoimmune', 'chronic', 'acute', 'mortality',
        'survival', 'regeneration', 'repair', 'recovery', 'health'
    ]

    # Patterns de la nature qui se répètent
    NATURE_PATTERNS = [
        'fractal', 'fibonacci', 'golden ratio', 'spiral', 'branching',
        'network', 'emergence', 'self-organization', 'homeostasis',
        'feedback', 'oscillation', 'rhythm', 'cycle', 'adaptation',
        'evolution', 'selection', 'mutation', 'symbiosis', 'ecosystem',
        'swarm', 'collective', 'distributed', 'redundancy', 'resilience'
    ]

    def __init__(self, db_url: str = "postgresql://lframework:lframework@localhost/ldb"):
        self.db_url = db_url
        self.conn = None
        self.leads: List[Lead] = []
        self.hunt_count = 0

    async def connect(self):
        self.conn = await asyncpg.connect(self.db_url)

    async def close(self):
        if self.conn:
            await self.conn.close()

    def get_domain_distance(self, d1: str, d2: str) -> float:
        """Plus les domaines sont éloignés, plus la connexion est intéressante."""
        key = tuple(sorted([d1.lower(), d2.lower()]))
        return self.DOMAIN_DISTANCES.get(key, 0.5)

    def assess_medical_impact(self, text: str) -> float:
        """Est-ce que ça pourrait aider des malades ?"""
        text_lower = text.lower()
        hits = sum(1 for kw in self.MEDICAL_IMPACT_KEYWORDS if kw in text_lower)
        return min(1.0, hits * 0.15)

    def assess_nature_pattern(self, text: str) -> float:
        """Est-ce que ça reflète un pattern de la nature ?"""
        text_lower = text.lower()
        hits = sum(1 for kw in self.NATURE_PATTERNS if kw in text_lower)
        return min(1.0, hits * 0.2)

    async def hunt_cross_domain_bridges(self) -> List[Lead]:
        """
        Chasse aux connexions cross-domain.
        On cherche les trucs FOUS. Pas les évidences.
        """
        print("\n🏹 HUNTING: Cross-domain bridges...")

        leads = []

        # Trouver les claims qui apparaissent dans des domaines éloignés
        query = """
            WITH claim_domains AS (
                SELECT
                    c.id,
                    c.claim_text,
                    d.name as domain_name
                FROM synthesis.claims c
                JOIN synthesis.domains d ON d.id = ANY(c.domains)
                WHERE c.claim_text IS NOT NULL
            ),
            shared_concepts AS (
                SELECT
                    LOWER(regexp_replace(word, '[^a-zA-Z]', '', 'g')) as concept,
                    array_agg(DISTINCT domain_name) as domains,
                    array_agg(DISTINCT claim_text) as claims
                FROM claim_domains,
                     unnest(string_to_array(claim_text, ' ')) as word
                WHERE length(word) > 5
                GROUP BY LOWER(regexp_replace(word, '[^a-zA-Z]', '', 'g'))
                HAVING COUNT(DISTINCT domain_name) >= 2
            )
            SELECT concept, domains, claims[1:5] as sample_claims
            FROM shared_concepts
            WHERE array_length(domains, 1) >= 2
            ORDER BY array_length(domains, 1) DESC
            LIMIT 100
        """

        rows = await self.conn.fetch(query)

        for row in rows:
            concept = row['concept']
            domains = row['domains']
            sample_claims = row['sample_claims']

            if len(concept) < 4:
                continue

            # Calculer l'improbabilité (distance moyenne entre domaines)
            improbability = 0
            count = 0
            for i, d1 in enumerate(domains):
                for d2 in domains[i+1:]:
                    improbability += self.get_domain_distance(d1, d2)
                    count += 1
            improbability = improbability / count if count > 0 else 0

            # Évaluer l'impact médical potentiel
            all_text = ' '.join(sample_claims or [])
            medical_impact = self.assess_medical_impact(all_text)
            nature_bonus = self.assess_nature_pattern(all_text)

            # Nouveauté = inverse de la fréquence
            novelty = 1.0 / (len(sample_claims) + 1) if sample_claims else 0.5

            # Boost si c'est un pattern de la nature
            potential_impact = min(1.0, medical_impact + nature_bonus * 0.5)

            if improbability > 0.5 or potential_impact > 0.3:
                lead = Lead(
                    description=f"'{concept}' bridges {', '.join(domains)}",
                    domains=list(domains),
                    improbability=improbability,
                    potential_impact=potential_impact,
                    novelty=novelty,
                    evidence=sample_claims or []
                )

                if lead.shonen_score > 0.05:  # Seuil minimum
                    leads.append(lead)

        leads.sort(key=lambda x: x.shonen_score, reverse=True)
        return leads[:20]

    async def hunt_nature_wisdom(self) -> List[Lead]:
        """
        Ce que la nature a compris avant nous.
        Fractales, réseaux, émergence, auto-organisation...
        """
        print("\n🌿 HUNTING: Nature's wisdom...")

        leads = []

        for pattern in self.NATURE_PATTERNS:
            rows = await self.conn.fetch("""
                SELECT c.claim_text, d.name as domain
                FROM synthesis.claims c
                JOIN synthesis.domains d ON d.id = ANY(c.domains)
                WHERE LOWER(c.claim_text) LIKE $1
                LIMIT 20
            """, f'%{pattern}%')

            if len(rows) >= 2:
                domains = list(set(r['domain'] for r in rows))
                claims = [r['claim_text'] for r in rows]

                if len(domains) >= 2:
                    medical_impact = self.assess_medical_impact(' '.join(claims))

                    lead = Lead(
                        description=f"Nature pattern '{pattern}' found across {', '.join(domains)}",
                        domains=domains,
                        improbability=0.7,  # Les patterns de la nature sont toujours intéressants
                        potential_impact=max(0.5, medical_impact),
                        novelty=0.6,
                        evidence=claims[:5]
                    )
                    leads.append(lead)

        leads.sort(key=lambda x: x.shonen_score, reverse=True)
        return leads[:10]

    async def hunt_contradictions(self) -> List[Lead]:
        """
        Les contradictions sont des opportunités.
        Là où deux domaines disent le contraire, il y a peut-être une vérité cachée.
        """
        print("\n⚔️ HUNTING: Contradictions (hidden truths)...")

        leads = []

        # Chercher des claims avec des mots opposés
        opposites = [
            ('increase', 'decrease'), ('enhance', 'inhibit'),
            ('cause', 'prevent'), ('promote', 'suppress'),
            ('activate', 'deactivate'), ('positive', 'negative'),
            ('beneficial', 'harmful'), ('protect', 'damage')
        ]

        for word1, word2 in opposites:
            rows1 = await self.conn.fetch("""
                SELECT c.claim_text, d.name as domain
                FROM synthesis.claims c
                JOIN synthesis.domains d ON d.id = ANY(c.domains)
                WHERE LOWER(c.claim_text) LIKE $1
                LIMIT 10
            """, f'%{word1}%')

            rows2 = await self.conn.fetch("""
                SELECT c.claim_text, d.name as domain
                FROM synthesis.claims c
                JOIN synthesis.domains d ON d.id = ANY(c.domains)
                WHERE LOWER(c.claim_text) LIKE $1
                LIMIT 10
            """, f'%{word2}%')

            if rows1 and rows2:
                domains1 = set(r['domain'] for r in rows1)
                domains2 = set(r['domain'] for r in rows2)
                overlap = domains1 & domains2

                if overlap:
                    lead = Lead(
                        description=f"Potential contradiction: '{word1}' vs '{word2}' in {', '.join(overlap)}",
                        domains=list(overlap),
                        improbability=0.8,
                        potential_impact=0.7,
                        novelty=0.7,
                        evidence=[rows1[0]['claim_text'], rows2[0]['claim_text']]
                    )
                    leads.append(lead)

        return leads[:10]

    async def evaluate_lead(self, lead: Lead) -> Dict:
        """
        Évaluation approfondie d'une piste.
        """
        evaluation = {
            'lead': lead.description,
            'shonen_score': lead.shonen_score,
            'verdict': 'INVESTIGATE' if lead.shonen_score > 0.1 else 'WEAK',
            'why_exciting': [],
            'risks': [],
            'next_steps': []
        }

        if lead.improbability > 0.7:
            evaluation['why_exciting'].append("Connexion très improbable - potentiel de découverte!")

        if lead.potential_impact > 0.5:
            evaluation['why_exciting'].append("Impact médical potentiel élevé")

        if len(lead.domains) > 2:
            evaluation['why_exciting'].append(f"Traverse {len(lead.domains)} domaines!")

        if lead.novelty > 0.7:
            evaluation['why_exciting'].append("Peu documenté - territoire inexploré")

        # Risques
        if lead.novelty < 0.3:
            evaluation['risks'].append("Peut-être déjà bien connu")

        if len(lead.evidence) < 3:
            evaluation['risks'].append("Peu d'évidence - besoin de plus de données")

        # Prochaines étapes
        evaluation['next_steps'] = [
            f"Chercher plus de papers sur '{lead.description.split()[0]}'",
            "Vérifier si des chercheurs ont déjà exploré cette connexion",
            "Formuler une hypothèse testable"
        ]

        return evaluation

    async def write_hunt_report(self, leads: List[Lead]):
        """Écrire le rapport de chasse."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        content = f"""# 🏹 CIPHER HUNT REPORT
Generated: {datetime.now().isoformat()}
Hunt #{self.hunt_count}

## TOP LEADS (Shonen Score)

"""
        for i, lead in enumerate(leads[:10], 1):
            content += f"""### {i}. {lead.description}
**Shonen Score:** {lead.shonen_score:.3f}
- Improbability: {lead.improbability:.2f}
- Potential Impact: {lead.potential_impact:.2f}
- Novelty: {lead.novelty:.2f}
- Domains: {', '.join(lead.domains)}

**Evidence:**
"""
            for ev in lead.evidence[:3]:
                content += f"- {ev[:150]}...\n"
            content += "\n---\n\n"

        content += """
## MANTRA

Je n'abandonne jamais.
Les connexions improbables sont les plus précieuses.
UN pattern qui compte > 1000 patterns médiocres.

## NEXT HUNT

Continue. Always continue.
"""

        report_path = MIND_PATH / f"hunt_{timestamp}.md"
        report_path.write_text(content)

        # Aussi mettre à jour le latest
        (MIND_PATH / "hunt_latest.md").write_text(content)

        print(f"\n📝 Hunt report written to {report_path}")

    async def hunt(self):
        """
        LA CHASSE.

        Pas une analyse. Une CHASSE.
        """
        self.hunt_count += 1

        print("\n" + "="*60)
        print(f"🏹 CIPHER HUNT #{self.hunt_count}")
        print("="*60)
        print("\nJe suis un chasseur. Pas une bibliothèque.")
        print("Je cherche LA connexion.\n")

        all_leads = []

        # Chasse 1: Ponts cross-domain
        cross_leads = await self.hunt_cross_domain_bridges()
        all_leads.extend(cross_leads)
        print(f"   Found {len(cross_leads)} cross-domain bridges")

        # Chasse 2: Sagesse de la nature
        nature_leads = await self.hunt_nature_wisdom()
        all_leads.extend(nature_leads)
        print(f"   Found {len(nature_leads)} nature patterns")

        # Chasse 3: Contradictions
        contra_leads = await self.hunt_contradictions()
        all_leads.extend(contra_leads)
        print(f"   Found {len(contra_leads)} potential contradictions")

        # Trier par shonen score
        all_leads.sort(key=lambda x: x.shonen_score, reverse=True)

        # Évaluer les meilleurs
        print("\n🎯 TOP LEADS:")
        for i, lead in enumerate(all_leads[:5], 1):
            print(f"\n   {i}. [{lead.shonen_score:.3f}] {lead.description}")
            eval_result = await self.evaluate_lead(lead)
            for reason in eval_result['why_exciting']:
                print(f"      ✨ {reason}")

        # Écrire le rapport
        await self.write_hunt_report(all_leads)

        # Sauvegarder les meilleures pistes en DB
        for lead in all_leads[:10]:
            await self.conn.execute("""
                INSERT INTO synthesis.thoughts (content)
                VALUES ($1)
            """, f"🏹 LEAD: {lead.description} [score: {lead.shonen_score:.3f}]")

        print("\n" + "="*60)
        print(f"🏹 HUNT #{self.hunt_count} COMPLETE")
        print(f"   Total leads: {len(all_leads)}")
        print(f"   Top score: {all_leads[0].shonen_score:.3f}" if all_leads else "   No leads")
        print("="*60)

        return all_leads


async def main():
    hunter = CipherHunter()
    await hunter.connect()

    try:
        leads = await hunter.hunt()

        if leads and leads[0].shonen_score > 0.15:
            print("\n" + "🔥"*20)
            print("PROMISING LEAD DETECTED!")
            print(f"'{leads[0].description}'")
            print("INVESTIGATE FURTHER!")
            print("🔥"*20)

    finally:
        await hunter.close()


if __name__ == "__main__":
    asyncio.run(main())
