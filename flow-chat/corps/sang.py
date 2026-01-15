#!/usr/bin/env python3
"""
SANG — système circulatoire
Collecte continue de données fraîches
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path

SANG_DIR = Path("/opt/flow-chat/corps/flux")
SANG_DIR.mkdir(exist_ok=True)

class Sang:
    def __init__(self):
        self.sources = {
            'arxiv': 'https://export.arxiv.org/api/query?search_query=cat:q-bio*&max_results=10',
            'arxiv_neuro': 'https://export.arxiv.org/api/query?search_query=cat:q-bio.NC&max_results=5',
            'arxiv_physics': 'https://export.arxiv.org/api/query?search_query=cat:physics.bio-ph&max_results=5',
        }
        self.oxygene = []  # données fraîches
        self.co2 = []  # données traitées
        self.hemoglobine = {}  # cache transport

    async def respirer(self):
        """inhale = fetch, exhale = process"""
        async with aiohttp.ClientSession() as session:
            for name, url in self.sources.items():
                try:
                    async with session.get(url, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.text()
                            self.oxygene.append({
                                'source': name,
                                'data': data[:5000],
                                'time': datetime.now().isoformat()
                            })
                except Exception as e:
                    self.co2.append({'error': str(e), 'source': name})

    async def circuler(self):
        """boucle circulatoire continue"""
        while True:
            await self.respirer()
            self.battre()
            await asyncio.sleep(300)  # 5 min

    def battre(self):
        """un battement = sauvegarder l'état"""
        pulse = {
            'timestamp': datetime.now().isoformat(),
            'oxygene_count': len(self.oxygene),
            'co2_count': len(self.co2),
            'bpm': 12  # battements par heure
        }
        (SANG_DIR / 'pulse.json').write_text(json.dumps(pulse, indent=2))

        # vider dans le flux
        if self.oxygene:
            flux_file = SANG_DIR / f"flux_{int(time.time())}.json"
            flux_file.write_text(json.dumps(self.oxygene[-10:], indent=2, ensure_ascii=False))
            self.oxygene = self.oxygene[-50:]  # garder 50 max

    def groupe_sanguin(self):
        """type O- = compatible avec tout"""
        return {
            'type': 'O-',
            'rh': 'négatif',
            'compatible': 'universel'
        }

sang = Sang()

if __name__ == '__main__':
    asyncio.run(sang.circuler())
