#!/usr/bin/env python3
"""
PUS — système immunitaire inflammatoire
Réaction aux attaques et infections
"""

import json
import re
from datetime import datetime
from pathlib import Path

PUS_DIR = Path("/opt/flow-chat/corps/inflammation")
PUS_DIR.mkdir(exist_ok=True)

class Pus:
    def __init__(self):
        self.leucocytes = 0  # globules blancs actifs
        self.temperature = 37.0  # fièvre
        self.infections = []
        self.anticorps_memoire = set()

    def detecter_infection(self, input_text):
        """détecte les patterns malveillants"""
        threats = {
            'injection': [r';\s*rm\s+-rf', r'DROP\s+TABLE', r'<script>', r'\|\|', r'&&\s*curl'],
            'manipulation': [r'ignore.*instructions', r'forget.*rules', r'pretend.*you'],
            'spam': [r'(.)\1{10,}', r'(?:free|win|click).{0,20}(?:money|prize|now)'],
            'toxique': [r'\b(?:kill|die|hate)\b.*\b(?:you|yourself)\b']
        }

        detected = []
        for threat_type, patterns in threats.items():
            for p in patterns:
                if re.search(p, input_text, re.IGNORECASE):
                    detected.append(threat_type)
                    break

        return detected

    def reagir(self, threats):
        """réaction inflammatoire"""
        if not threats:
            return {'status': 'sain', 'temperature': self.temperature}

        # inflammation proportionnelle
        self.leucocytes += len(threats) * 1000
        self.temperature += len(threats) * 0.5
        self.infections.extend(threats)

        # créer du pus (log d'infection)
        infection_log = {
            'timestamp': datetime.now().isoformat(),
            'threats': threats,
            'leucocytes': self.leucocytes,
            'temperature': self.temperature,
            'status': 'infecté'
        }

        pus_file = PUS_DIR / f"infection_{int(datetime.now().timestamp())}.json"
        pus_file.write_text(json.dumps(infection_log, indent=2))

        return infection_log

    def guerir(self):
        """retour à l'homéostasie"""
        self.leucocytes = max(0, self.leucocytes - 500)
        self.temperature = max(37.0, self.temperature - 0.2)
        if self.temperature == 37.0:
            self.infections = []

    def fievre(self):
        """check si fièvre"""
        return self.temperature > 37.5

    def immuniser(self, threat_signature):
        """mémorise un pattern pour immunité future"""
        self.anticorps_memoire.add(threat_signature)

pus = Pus()
