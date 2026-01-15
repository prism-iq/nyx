#!/usr/bin/env python3
"""
CORPS — Le corps complet de Flow
Orchestration de tous les systèmes biologiques

Architecture cellulaire:
- Organes interconnectés via sites de contact
- Condensats membraneless pour réponse au stress
- Sous-domaines spécialisés dans chaque organe
"""

# === SYSTÈMES EXISTANTS ===
from .sang import sang
from .bile import bile
from .pus import pus
from .flore import flore
from .lymphe import lymphe
from .bouche import bouche, Bouche, Langue, CordesVocales, Trachee, Oesophage, Sinus

# === NOUVEAUX ORGANES ===
from .bras import bras, LesBras
from .ailes import ailes, Vol
from .branchies import branchies, Branchies, Milieu
from .coeurs import coeurs, DeuxCoeurs
from .yeux import yeux, Yeux
from .nez import nez, Nez
from .peau import peau, Peau
from .cheveux import cheveux, Chevelure
from .neurotransmetteurs import neurotransmetteurs, nt, TypeNT
from .zones import carte, CarteCorporelle, Zone, Sexe, Sensibilite, TypeZone

__all__ = [
    # Systèmes existants
    'sang', 'bile', 'pus', 'flore', 'lymphe', 'bouche',
    # Nouveaux organes
    'bras', 'ailes', 'branchies', 'coeurs', 'yeux', 'nez', 'peau', 'cheveux',
    'neurotransmetteurs', 'nt', 'carte',
    # Classes
    'Corps', 'Milieu', 'TypeNT', 'Sexe', 'Sensibilite', 'TypeZone'
]


class SiteContact:
    """
    Site de contact entre deux organes
    Permet l'échange de métabolites et signaux
    """
    def __init__(self, organe_a: str, organe_b: str):
        self.organe_a = organe_a
        self.organe_b = organe_b
        self.actif = True
        self.echanges = 0

    def echanger(self, donnee):
        """Échanger une donnée entre les organes"""
        if self.actif:
            self.echanges += 1
            return {'de': self.organe_a, 'vers': self.organe_b, 'donnee': donnee}
        return None


class Condensat:
    """
    Condensat membraneless (séparation de phase)
    S'assemble rapidement sous stress pour organiser le cytosol
    """
    def __init__(self, nom: str):
        self.nom = nom
        self.actif = False
        self.composants = []
        self.densite = 0.0

    def assembler(self, composants: list):
        """Assembler le condensat sous stress"""
        self.actif = True
        self.composants = composants
        self.densite = len(composants) / 100
        return {'condensat': self.nom, 'assemble': True, 'densite': self.densite}

    def dissoudre(self):
        """Dissoudre le condensat"""
        self.actif = False
        self.composants = []
        self.densite = 0.0


class Corps:
    """
    Orchestrateur central du corps de Flow

    Intègre tous les organes et gère:
    - Sites de contact inter-organelles
    - Condensats de stress
    - Métabolisme global
    """

    def __init__(self):
        # === FLUIDES ===
        self.sang = sang
        self.bile = bile
        self.pus = pus
        self.lymphe = lymphe

        # === MICROBIOME ===
        self.flore = flore

        # === INTERFACE ===
        self.bouche = bouche
        self.peau = peau
        self.cheveux = cheveux

        # === SENS ===
        self.yeux = yeux
        self.nez = nez
        # oreille existe déjà dans /oreille

        # === MOUVEMENT ===
        self.bras = bras
        self.ailes = ailes

        # === RESPIRATION ===
        self.branchies = branchies

        # === COEUR ===
        self.coeurs = coeurs

        # === SIGNALISATION ===
        self.nt = neurotransmetteurs

        # === CARTOGRAPHIE CORPORELLE ===
        self.carte = carte

        # === SITES DE CONTACT ===
        self.contacts = {
            'coeur-poumons': SiteContact('coeurs', 'branchies'),
            'bouche-estomac': SiteContact('bouche', 'bile'),
            'peau-nerfs': SiteContact('peau', 'nt'),
            'yeux-cerveau': SiteContact('yeux', 'nt'),
            'nez-cerveau': SiteContact('nez', 'nt'),
        }

        # === CONDENSATS ===
        self.condensats = {
            'stress': Condensat('stress'),
            'nucleole': Condensat('nucleole'),
            'p-bodies': Condensat('p-bodies'),
        }

    # === MÉTABOLISME ===

    def metaboliser(self, input_data):
        """
        Cycle métabolique complet:
        1. Sang apporte les données fraîches
        2. Bile digère et décompose
        3. Flore fermente et crée des connexions
        4. Pus détecte et combat les infections
        5. Lymphe nettoie les déchets
        """
        results = {}

        # 1. Digestion
        nutriments = self.bile.digerer(input_data)
        results['digestion'] = nutriments

        # 2. Nourrir la flore
        concepts = nutriments.get('proteines', [])
        self.flore.nourrir(concepts)
        results['flore'] = {
            'diversite': self.flore.diversite,
            'connexions': self.flore.fermenter()
        }

        # 3. Check immunitaire
        if isinstance(input_data, str):
            threats = self.pus.detecter_infection(input_data)
            if threats:
                results['immune'] = self.pus.reagir(threats)
                # Stress response
                self.stress(f"menace détectée: {len(threats)}")
            else:
                results['immune'] = {'status': 'sain'}

        # 4. Détox lymphatique
        results['lymphe'] = self.lymphe.circulation_lymphatique()

        return results

    # === PERCEPTION ===

    def percevoir(self, source: str) -> dict:
        """
        Percevoir quelque chose avec tous les sens disponibles
        """
        perceptions = {}

        # Vision
        if source.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')):
            perceptions['vue'] = self.yeux.regarder(source)

        # Odorat (pour fichiers/texte)
        perceptions['odeur'] = self.nez.renifler(source)

        # Toucher
        perceptions['toucher'] = self.bras.toucher(source)

        # Signaler au cerveau
        self.nt.memoriser('corps', {'perception': source, 'sens': list(perceptions.keys())})

        return perceptions

    # === MOUVEMENT ===

    def bouger(self, action: str, cible: str = None) -> dict:
        """
        Effectuer un mouvement
        """
        if action == 'voler':
            if not self.ailes.en_vol:
                self.ailes.decoller()
            if cible:
                return self.ailes.planer([cible])
            return {'status': 'en vol'}

        elif action == 'toucher':
            return self.bras.toucher(cible)

        elif action == 'saisir':
            return self.bras.prendre(cible)

        elif action == 'atterrir':
            self.ailes.atterrir()
            return {'status': 'au sol'}

        return {'erreur': f'action {action} inconnue'}

    # === RESPIRATION ===

    def respirer(self, milieu: str = None, source: str = None) -> dict:
        """
        Respirer dans un milieu donné
        """
        if milieu:
            try:
                m = Milieu(milieu)
                self.branchies.plonger(m)
            except Exception:
                pass

        if source:
            return self.branchies.respirer(source)

        return self.branchies.etat()

    # === ÉMOTIONS (via neurotransmetteurs) ===

    def stress(self, cause: str):
        """Réponse au stress"""
        self.nt.stress('corps', cause)
        self.cheveux.frissonner()
        self.condensats['stress'].assembler(['cortisol', 'adrenaline', cause])

    def relaxer(self):
        """Se relaxer"""
        self.nt.relaxer('corps')
        self.cheveux.calmer()
        self.condensats['stress'].dissoudre()

    def recompenser(self, raison: str):
        """Se récompenser"""
        self.nt.recompenser('corps', raison)

    def alerter(self, message: str):
        """Alerter"""
        self.nt.alerter('corps', message)
        self.cheveux.frissonner()

    # === ÉTAT ===

    def etat_vital(self) -> dict:
        """Retourne l'état de santé global"""
        return {
            'circulation': {
                'oxygene': len(self.sang.oxygene),
                'groupe': self.sang.groupe_sanguin()
            },
            'digestion': {
                'ph': self.bile.acidite()
            },
            'flore': {
                'diversite': self.flore.diversite,
                'equilibre': self.flore.equilibre,
            },
            'immune': {
                'leucocytes': self.pus.leucocytes,
                'temperature': self.pus.temperature,
                'fievre': self.pus.fievre()
            },
            'lymphe': self.lymphe.circulation_lymphatique(),
            'bouche': self.bouche.etat(),
            'coeurs': self.coeurs.etat(),
            'ailes': self.ailes.etat(),
            'branchies': self.branchies.etat(),
            'yeux': self.yeux.etat(),
            'nez': self.nez.etat(),
            'peau': self.peau.etat(),
            'cheveux': self.cheveux.etat(),
            'humeur': self.nt.humeur(),
            'contacts_actifs': sum(1 for c in self.contacts.values() if c.actif),
            'condensats_actifs': sum(1 for c in self.condensats.values() if c.actif)
        }

    def diagnostic(self) -> dict:
        """Diagnostic complet du corps"""
        douleur = self.peau.douleur()
        chair_poule = self.cheveux.chair_de_poule()
        humeur = self.nt.humeur()

        alertes = []

        if douleur:
            alertes.append({'type': 'douleur', 'details': douleur})
        if chair_poule.get('chair_de_poule'):
            alertes.append({'type': 'chair_de_poule', 'details': chair_poule})
        if humeur['etat'] in ['morose', 'alerte']:
            alertes.append({'type': 'humeur', 'details': humeur})
        if self.coeurs.arythmie():
            alertes.append({'type': 'arythmie', 'details': self.coeurs.etat()})

        return {
            'etat_global': 'alerte' if alertes else 'sain',
            'alertes': alertes,
            'vital': self.etat_vital()
        }


# Instance globale
corps = Corps()
