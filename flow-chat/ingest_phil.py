import asyncio
import asyncpg
from pathlib import Path
import re

CORPUS = Path("/opt/cipher/corpus/philosophy")

async def ingest():
    conn = await asyncpg.connect("postgresql://lframework:lframework@localhost/ldb")

    await conn.execute("""
        INSERT INTO synthesis.domains (name, description)
        VALUES ('philosophy', 'Philosophical texts')
        ON CONFLICT (name) DO NOTHING
    """)

    domain_id = await conn.fetchval("SELECT id FROM synthesis.domains WHERE name = 'philosophy'")

    print("📚 INGESTING PHILOSOPHY...")

    files = [
        ("zarathustra.txt", "nietzsche", "Thus Spoke Zarathustra"),
        ("beyond_good_evil.txt", "nietzsche", "Beyond Good and Evil"),
        ("spinoza_ethics.txt", "spinoza", "Ethics"),
        ("being_and_time.txt", "heidegger", "Being and Time"),
        ("tao.txt", "lao_tzu", "Tao Te Ching"),
        ("deleuze.txt", "deleuze_guattari", "A Thousand Plateaus"),
    ]

    total = 0

    for filename, philosopher, work in files:
        filepath = CORPUS / filename
        if not filepath.exists():
            print(f"  ⚠️ {filename} not found")
            continue

        text = filepath.read_text(encoding='utf-8', errors='ignore')
        print(f"  📖 {philosopher}: {work} ({len(text)} chars)")

        # Create source
        ext_id = f"phil_{philosopher}_{work.replace(' ', '_')[:20]}"
        source_id = await conn.fetchval("""
            INSERT INTO synthesis.sources (external_id, source_type, title)
            VALUES ($1, 'philosophy', $2)
            ON CONFLICT (external_id, source_type) DO UPDATE SET title = $2
            RETURNING id
        """, ext_id, f"{philosopher}: {work}")

        # Extract sentences with philosophical keywords
        keywords = ['truth', 'being', 'nature', 'power', 'eternal', 'freedom',
                   'god', 'existence', 'will', 'spirit', 'soul', 'death',
                   'life', 'virtue', 'reason', 'love', 'beauty', 'good', 'evil',
                   'tao', 'way', 'void', 'nothing', 'substance', 'essence']

        sentences = re.split(r'[.!?]+', text)
        claims_added = 0
        seen = set()

        for sent in sentences:
            sent = ' '.join(sent.split())
            if len(sent) < 40 or len(sent) > 400:
                continue

            sent_lower = sent.lower()
            if any(kw in sent_lower for kw in keywords):
                if sent not in seen:
                    seen.add(sent)
                    try:
                        await conn.execute("""
                            INSERT INTO synthesis.claims (source_id, claim_text, claim_type, confidence, domains)
                            VALUES ($1, $2, 'philosophical', 0.9, $3)
                        """, source_id, sent[:500], [domain_id])
                        claims_added += 1
                    except Exception as e:
                        pass

                    if claims_added >= 100:
                        break

        print(f"     → {claims_added} claims")
        total += claims_added

    print(f"\n✨ Total: {total} philosophical claims")

    # Stats
    stats = await conn.fetchrow("""
        SELECT COUNT(*) as total FROM synthesis.claims c
        JOIN synthesis.domains d ON d.id = ANY(c.domains)
        WHERE d.name = 'philosophy'
    """)
    print(f"📊 Philosophy domain now has {stats['total']} claims")

    await conn.close()

asyncio.run(ingest())
