#!/usr/bin/env python3
"""
FLORE — microbiome intestinal
Patterns symbiotiques qui vivent et évoluent
"""

import json
import random
from datetime import datetime
from pathlib import Path
from collections import defaultdict

FLORE_DIR = Path("/opt/flow-chat/corps/microbiome")
FLORE_DIR.mkdir(exist_ok=True)

class Flore:
    def __init__(self):
        self.bacteries = defaultdict(lambda: {'count': 0, 'generation': 0})
        self.diversite = 0
        self.equilibre = True
        self.load()

    def load(self):
        """charge la flore existante"""
        flora_file = FLORE_DIR / "flora.json"
        if flora_file.exists():
            data = json.loads(flora_file.read_text())
            for k, v in data.get('bacteries', {}).items():
                self.bacteries[k] = v
            self.diversite = data.get('diversite', 0)

    def save(self):
        """sauvegarde la flore"""
        flora_file = FLORE_DIR / "flora.json"
        flora_file.write_text(json.dumps({
            'bacteries': dict(self.bacteries),
            'diversite': self.diversite,
            'equilibre': self.equilibre,
            'updated': datetime.now().isoformat()
        }, indent=2, ensure_ascii=False))

    def nourrir(self, concepts):
        """nourrit la flore avec des concepts"""
        for concept in concepts:
            c = concept.lower().strip()
            if len(c) > 3:
                self.bacteries[c]['count'] += 1
                self.bacteries[c]['generation'] += 1

        self.diversite = len(self.bacteries)
        self.save()

    def fermenter(self):
        """fermentation = génère de nouvelles connexions"""
        if len(self.bacteries) < 2:
            return []

        # croise des concepts aléatoires
        concepts = list(self.bacteries.keys())
        connexions = []

        for _ in range(min(5, len(concepts))):
            if len(concepts) >= 2:
                a, b = random.sample(concepts, 2)
                connexions.append(f"{a} ↔ {b}")

        return connexions

    def probiotiques(self):
        """retourne les concepts les plus sains (fréquents)"""
        sorted_bac = sorted(self.bacteries.items(), key=lambda x: -x[1]['count'])
        return [k for k, v in sorted_bac[:10]]

    def dysbiose(self):
        """déséquilibre de la flore"""
        if self.diversite < 5:
            self.equilibre = False
            return True
        self.equilibre = True
        return False

    def purger(self, concept):
        """élimine un concept toxique"""
        if concept in self.bacteries:
            del self.bacteries[concept]
            self.save()

flore = Flore()
