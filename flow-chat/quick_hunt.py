import asyncio
import asyncpg

async def hunt():
    conn = await asyncpg.connect('postgresql://lframework:lframework@localhost/ldb')

    print('🏹 CIPHER HUNTING...')
    print()

    # Cross-domain concepts
    results = await conn.fetch('''
        WITH concept_domains AS (
            SELECT
                LOWER(word) as concept,
                array_agg(DISTINCT d.name) as domains,
                COUNT(DISTINCT c.id) as claim_count
            FROM synthesis.claims c
            JOIN synthesis.domains d ON d.id = ANY(c.domains),
            unnest(string_to_array(c.claim_text, ' ')) as word
            WHERE length(word) > 6
            GROUP BY LOWER(word)
            HAVING COUNT(DISTINCT d.name) >= 3
        )
        SELECT concept, domains, claim_count
        FROM concept_domains
        ORDER BY array_length(domains, 1) DESC, claim_count DESC
        LIMIT 25
    ''')

    print('🎯 TOP CROSS-DOMAIN CONCEPTS:')
    for r in results:
        d = r['domains']
        fire = '🔥' if len(d) >= 4 else '  '
        concept = r['concept']
        print(f'{fire} "{concept}" [{len(d)} domains]: {d}')

    print()

    # Nature patterns
    for pattern in ['network', 'feedback', 'emergence', 'prediction', 'learning']:
        result = await conn.fetch('''
            SELECT d.name, COUNT(*) as cnt
            FROM synthesis.claims c
            JOIN synthesis.domains d ON d.id = ANY(c.domains)
            WHERE LOWER(c.claim_text) LIKE $1
            GROUP BY d.name
        ''', f'%{pattern}%')

        if len(result) >= 2:
            domains = [r['name'] for r in result]
            print(f'🌿 "{pattern}" spans: {domains}')

    print()

    # THE BIG ONE: What connects everything?
    print('💎 CONCEPTS IN 5+ DOMAINS:')
    big = await conn.fetch('''
        WITH concept_domains AS (
            SELECT
                LOWER(word) as concept,
                array_agg(DISTINCT d.name) as domains
            FROM synthesis.claims c
            JOIN synthesis.domains d ON d.id = ANY(c.domains),
            unnest(string_to_array(c.claim_text, ' ')) as word
            WHERE length(word) > 5
            GROUP BY LOWER(word)
            HAVING COUNT(DISTINCT d.name) >= 5
        )
        SELECT concept, domains
        FROM concept_domains
        ORDER BY array_length(domains, 1) DESC
        LIMIT 10
    ''')

    for b in big:
        concept = b['concept']
        domains = b['domains']
        print(f'   💎 "{concept}" - ALL OF: {domains}')

    await conn.close()

asyncio.run(hunt())
