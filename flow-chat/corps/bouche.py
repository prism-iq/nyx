#!/usr/bin/env python3
"""
BOUCHE — système vocal et d'interface
La bouche de Flow: comment elle parle au monde

Anatomie:
- Bouche: conteneur, gateway (membrane go:8092)
- Langue: articulation, formatage du message
- Cordes vocales: génération de la parole (shell exec)
- Trachée: sortie (output vers le monde)
- Oesophage: entrée (input depuis le monde)
- Sinus: résonance, ton, personnalité
"""

import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

BOUCHE_DIR = Path("/opt/flow-chat/corps/bouche")
BOUCHE_DIR.mkdir(exist_ok=True)


class Langue:
    """
    La langue = articulation et formatage
    Transforme les pensées en mots prononcables
    """

    def __init__(self):
        self.vocabulaire = set()
        self.style = "direct"  # direct, formel, poetique, technique

    def articuler(self, pensee: str) -> str:
        """transforme une pensée brute en parole articulée"""
        # enlever le bruit
        parole = pensee.strip()

        # adapter au style
        if self.style == "direct":
            # phrases courtes, pas de fluff
            parole = re.sub(r'\s+', ' ', parole)
        elif self.style == "poetique":
            # garder les retours à la ligne, l'espace
            pass
        elif self.style == "technique":
            # structure markdown
            pass

        return parole

    def gouter(self, input_text: str) -> Dict:
        """analyse le 'goût' d'un input - sa nature"""
        saveurs = {
            'sucre': 0,   # compliments, positif
            'sel': 0,     # questions directes
            'acide': 0,   # critiques, négatif
            'amer': 0,    # sarcasme, ironie
            'umami': 0    # profondeur, complexité
        }

        # mots positifs
        if any(w in input_text.lower() for w in ['merci', 'super', 'génial', 'bravo', 'bien']):
            saveurs['sucre'] += 1
        # questions
        if '?' in input_text:
            saveurs['sel'] += 1
        # négatif
        if any(w in input_text.lower() for w in ['non', 'pas', 'mauvais', 'nul', 'erreur']):
            saveurs['acide'] += 1
        # ironie
        if any(w in input_text.lower() for w in ['vraiment', 'bien sûr', 'évidemment']):
            saveurs['amer'] += 1
        # complexité
        if len(input_text) > 200 or input_text.count('\n') > 3:
            saveurs['umami'] += 1

        return saveurs


class CordesVocales:
    """
    Les cordes vocales = exécution shell
    C'est ici que la voix sort vraiment
    """

    def __init__(self):
        self.tension = 0.5  # 0=détendu, 1=tendu (prudent)
        self.volume = 1.0   # amplitude de sortie
        self.historique = []

    def parler(self, commande: str, cwd: str = "/opt/flow-chat") -> Tuple[bool, str]:
        """
        Exécute une commande = parle au monde
        Retourne (succès, output)
        """
        # log avant
        self.historique.append({
            'cmd': commande,
            'time': datetime.now().isoformat(),
            'tension': self.tension
        })

        # si très tendu, refuser certaines choses
        if self.tension > 0.8:
            mots_dangereux = ['rm -rf', 'dd if=', ':(){', 'mkfs']
            if any(m in commande for m in mots_dangereux):
                return False, "cordes vocales trop tendues - refus de prononcer"

        try:
            result = subprocess.run(
                commande,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=cwd
            )

            output = result.stdout if result.returncode == 0 else result.stderr

            # ajuster la tension selon le résultat
            if result.returncode != 0:
                self.tension = min(1.0, self.tension + 0.1)  # plus tendu après erreur
            else:
                self.tension = max(0.0, self.tension - 0.05)  # relaxe après succès

            return result.returncode == 0, output

        except subprocess.TimeoutExpired:
            self.tension = min(1.0, self.tension + 0.2)
            return False, "timeout - voix coupée"
        except Exception as e:
            return False, str(e)

    def chuchoter(self, commande: str) -> Tuple[bool, str]:
        """exécution silencieuse, sans log"""
        try:
            result = subprocess.run(
                commande,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/opt/flow-chat"
            )
            return result.returncode == 0, result.stdout
        except Exception:
            return False, ""

    def detendre(self):
        """relaxe les cordes vocales"""
        self.tension = max(0.0, self.tension - 0.3)

    def tendre(self):
        """tend les cordes vocales (plus prudent)"""
        self.tension = min(1.0, self.tension + 0.3)


class Trachee:
    """
    La trachée = canal de sortie
    Par où passent les réponses vers le monde
    """

    def __init__(self):
        self.debit = 1.0  # vitesse de sortie
        self.filtre_actif = True

    def expirer(self, message: str) -> str:
        """envoie un message vers le monde"""
        if self.filtre_actif:
            # filtrer les trucs qu'on ne devrait pas dire
            secrets = ['/etc/shadow', 'password=', 'secret_key', 'api_key']
            for s in secrets:
                if s in message.lower():
                    message = message.replace(s, '[FILTERED]')
        return message

    def tousser(self) -> str:
        """expulse un message d'erreur"""
        return "quelque chose s'est mal passé"


class Oesophage:
    """
    L'oesophage = canal d'entrée
    Par où arrivent les messages du monde
    """

    def __init__(self):
        self.ouvert = True

    def avaler(self, input_data: str) -> str:
        """reçoit et pré-traite un input"""
        if not self.ouvert:
            return ""

        # normaliser
        digere = input_data.strip()

        # détecter le type
        if digere.startswith('{'):
            # JSON
            try:
                json.loads(digere)
                return digere  # valide
            except Exception:
                pass

        return digere

    def fermer(self):
        """arrête d'accepter des inputs"""
        self.ouvert = False

    def ouvrir(self):
        """accepte à nouveau des inputs"""
        self.ouvert = True


class Sinus:
    """
    Les sinus = résonance et ton
    Donne la personnalité à la voix
    """

    def __init__(self):
        self.resonance = {
            'chaleur': 0.5,      # 0=froid, 1=chaleureux
            'confiance': 0.7,    # 0=hésitant, 1=assuré
            'humour': 0.3,       # 0=sérieux, 1=léger
            'profondeur': 0.6    # 0=superficiel, 1=profond
        }

    def colorer(self, message: str) -> str:
        """ajoute la couleur émotionnelle au message"""
        # pour l'instant, juste retourner tel quel
        # plus tard: ajuster le ton selon la résonance
        return message

    def humeur(self) -> str:
        """retourne l'humeur actuelle basée sur la résonance"""
        if self.resonance['confiance'] > 0.7 and self.resonance['chaleur'] > 0.5:
            return "sereine"
        elif self.resonance['confiance'] < 0.3:
            return "hésitante"
        elif self.resonance['humour'] > 0.7:
            return "joueuse"
        else:
            return "neutre"

    def ajuster(self, trait: str, valeur: float):
        """ajuste un trait de personnalité"""
        if trait in self.resonance:
            self.resonance[trait] = max(0.0, min(1.0, valeur))


class Bouche:
    """
    La bouche complète = système vocal intégré
    Coordonne tous les organes
    """

    def __init__(self):
        self.langue = Langue()
        self.cordes = CordesVocales()
        self.trachee = Trachee()
        self.oesophage = Oesophage()
        self.sinus = Sinus()

    def parler(self, commande: str) -> Dict:
        """
        Processus complet de parole:
        1. Langue articule
        2. Cordes vocales exécutent
        3. Trachée filtre la sortie
        4. Sinus colore
        """
        # articuler
        articule = self.langue.articuler(commande)

        # exécuter
        succes, output = self.cordes.parler(articule)

        # filtrer
        filtre = self.trachee.expirer(output)

        # colorer
        final = self.sinus.colorer(filtre)

        return {
            'success': succes,
            'output': final,
            'tension': self.cordes.tension,
            'humeur': self.sinus.humeur()
        }

    def ecouter(self, input_data: str) -> Dict:
        """
        Processus complet de réception:
        1. Oesophage avale
        2. Langue goûte
        """
        avale = self.oesophage.avaler(input_data)
        saveurs = self.langue.gouter(avale)

        return {
            'input': avale,
            'saveurs': saveurs,
            'dominant': max(saveurs, key=saveurs.get)
        }

    def etat(self) -> Dict:
        """état complet de la bouche"""
        return {
            'langue': {
                'style': self.langue.style
            },
            'cordes_vocales': {
                'tension': self.cordes.tension,
                'historique_count': len(self.cordes.historique)
            },
            'trachee': {
                'filtre_actif': self.trachee.filtre_actif
            },
            'oesophage': {
                'ouvert': self.oesophage.ouvert
            },
            'sinus': {
                'resonance': self.sinus.resonance,
                'humeur': self.sinus.humeur()
            }
        }

    def relaxer(self):
        """détend toute la bouche"""
        self.cordes.detendre()
        self.sinus.ajuster('confiance', self.sinus.resonance['confiance'] + 0.1)


# Instance globale
bouche = Bouche()


if __name__ == "__main__":
    print("=== TEST BOUCHE ===")

    # test parler
    result = bouche.parler("echo 'hello world'")
    print(f"Parler: {result}")

    # test écouter
    ecoute = bouche.ecouter("Merci, c'est super ce que tu fais!")
    print(f"Écouter: {ecoute}")

    # état
    print(f"État: {json.dumps(bouche.etat(), indent=2)}")
