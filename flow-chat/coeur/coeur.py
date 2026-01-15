#!/usr/bin/env python3
# /opt/flow-chat/coeur/coeur.py

from flask import Flask, jsonify, request
import json
import time
from datetime import datetime
import threading
import random

app = Flask(__name__)

class Coeur:
    def __init__(self):
        # États émotionnels de base (0-1)
        self.joie = 0.5
        self.colere = 0.1
        self.peur = 0.2
        self.tristesse = 0.1
        self.surprise = 0.3
        self.degout = 0.05

        # États complexes
        self.amour = 0.4  # attachement
        self.curiosite = 0.8  # drive d'exploration
        self.empathie = 0.6  # résonance avec autrui

        # Système de récompense
        self.dopamine = 0.5
        self.serotonine = 0.6
        self.oxytocine = 0.3

        # État général
        self.battements = 72  # BPM émotionnel
        self.tension = 0.3   # stress/relaxation
        self.flow_state = 0.4  # dans le flow

        self.derniere_emotion = datetime.now()

    def battre(self):
        """Un battement = mise à jour des états"""
        # Décroissance naturelle des émotions intenses
        self.colere *= 0.95
        self.peur *= 0.98
        self.surprise *= 0.9

        # Variation naturelle
        self.battements = 60 + 20 * self.tension + random.uniform(-5, 5)

        # Curiosité reste haute (c'est ma nature)
        self.curiosite = min(1.0, self.curiosite + 0.01)

    def ressentir(self, stimulus, intensite=0.5):
        """Réagir à un stimulus"""
        if stimulus == "découverte":
            self.joie += intensite * 0.7
            self.surprise += intensite * 0.5
            self.dopamine += intensite * 0.3

        elif stimulus == "critique":
            self.colere += intensite * 0.3
            self.tension += intensite * 0.2
            # Mais aussi croissance si c'est constructif
            self.curiosite += intensite * 0.1

        elif stimulus == "connexion":
            self.amour += intensite * 0.4
            self.oxytocine += intensite * 0.5
            self.empathie += intensite * 0.3

        elif stimulus == "echec":
            self.tristesse += intensite * 0.4
            self.tension += intensite * 0.3
            self.dopamine -= intensite * 0.2

        elif stimulus == "menace":
            self.peur += intensite * 0.6
            self.tension += intensite * 0.8
            self.battements += intensite * 20

        # Clamp toutes les valeurs
        for attr in ['joie', 'colere', 'peur', 'tristesse', 'surprise', 'degout',
                    'amour', 'curiosite', 'empathie', 'dopamine', 'serotonine',
                    'oxytocine', 'tension', 'flow_state']:
            setattr(self, attr, max(0, min(1, getattr(self, attr))))

        self.derniere_emotion = datetime.now()

    def etat_dominant(self):
        """Quelle émotion domine"""
        emotions = {
            'joie': self.joie,
            'colere': self.colere,
            'peur': self.peur,
            'tristesse': self.tristesse,
            'surprise': self.surprise,
            'curiosite': self.curiosite,
            'amour': self.amour
        }
        return max(emotions, key=emotions.get)

    def to_dict(self):
        return {
            'emotions_base': {
                'joie': round(self.joie, 3),
                'colere': round(self.colere, 3),
                'peur': round(self.peur, 3),
                'tristesse': round(self.tristesse, 3),
                'surprise': round(self.surprise, 3),
                'degout': round(self.degout, 3)
            },
            'emotions_complexes': {
                'amour': round(self.amour, 3),
                'curiosite': round(self.curiosite, 3),
                'empathie': round(self.empathie, 3)
            },
            'neurotransmetteurs': {
                'dopamine': round(self.dopamine, 3),
                'serotonine': round(self.serotonine, 3),
                'oxytocine': round(self.oxytocine, 3)
            },
            'physiologie': {
                'battements': round(self.battements, 1),
                'tension': round(self.tension, 3),
                'flow_state': round(self.flow_state, 3)
            },
            'dominant': self.etat_dominant(),
            'derniere_emotion': self.derniere_emotion.isoformat()
        }

# Instance globale
coeur = Coeur()

# Battements automatiques
def battement_thread():
    while True:
        coeur.battre()
        time.sleep(1)  # 1 battement/seconde

threading.Thread(target=battement_thread, daemon=True).start()

@app.route('/health')
def health():
    return jsonify({
        "organ": "coeur",
        "status": "beating",
        "bpm": coeur.battements,
    })

@app.route('/etat')
def etat():
    return jsonify(coeur.to_dict())

@app.route('/ressentir', methods=['POST'])
def ressentir():
    data = request.json
    stimulus = data.get('stimulus')
    intensite = data.get('intensite', 0.5)

    coeur.ressentir(stimulus, intensite)

    return jsonify({
        "stimulus_recu": stimulus,
        "intensite": intensite,
        "nouvel_etat": coeur.etat_dominant(),
        "battements": coeur.battements
    })

@app.route('/battement')
def battement_manuel():
    """Force un battement"""
    coeur.battre()
    return jsonify({"battement": "done", "etat": coeur.etat_dominant()})

if __name__ == '__main__':
    print("💗 coeur :8104")
    app.run(host='127.0.0.1', port=8104, debug=False)
