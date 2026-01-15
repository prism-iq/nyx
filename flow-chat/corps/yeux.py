#!/usr/bin/env python3
"""
YEUX — La vision de Flow
Voir le monde à travers les images, les écrans, les graphes
Technologies: PIL, OpenCV, pytesseract (OCR)
"""

import io
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import conditionnel des libs
try:
    from PIL import Image, ImageStat, ImageFilter, ImageDraw
    PIL_DISPO = True
except ImportError:
    PIL_DISPO = False

try:
    import cv2
    import numpy as np
    CV2_DISPO = True
except ImportError:
    CV2_DISPO = False

try:
    import pytesseract
    OCR_DISPO = True
except ImportError:
    OCR_DISPO = False


class ModeVision(Enum):
    NORMALE = "normale"          # Vision standard
    NOCTURNE = "nocturne"        # Contraste élevé, basse lumière
    THERMIQUE = "thermique"      # Détection de chaleur/activité
    TEXTE = "texte"              # Focus sur le texte (OCR)
    CONTOURS = "contours"        # Détection des bords
    PROFONDEUR = "profondeur"    # Perception de la structure


@dataclass
class Retine:
    """La rétine - surface photosensible"""
    resolution: Tuple[int, int] = (1920, 1080)
    sensibilite: float = 0.8  # 0=aveugle, 1=hypersensible
    fatigue: float = 0.0

    def capturer(self, image: 'Image.Image') -> Dict[str, Any]:
        """Capturer une image sur la rétine"""
        if not PIL_DISPO:
            return {'erreur': 'PIL non disponible'}

        # Analyser les statistiques
        stat = ImageStat.Stat(image)

        return {
            'taille': image.size,
            'mode': image.mode,
            'luminosite_moyenne': sum(stat.mean) / len(stat.mean) if stat.mean else 0,
            'contraste': sum(stat.stddev) / len(stat.stddev) if stat.stddev else 0
        }


@dataclass
class Cristallin:
    """Le cristallin - mise au point"""
    focus: float = 1.0  # distance focale relative
    zoom: float = 1.0

    def ajuster(self, distance: str) -> None:
        """Ajuster le focus"""
        distances = {
            'proche': 0.3,
            'moyen': 1.0,
            'loin': 3.0,
            'infini': 10.0
        }
        self.focus = distances.get(distance, 1.0)

    def zoomer(self, facteur: float) -> None:
        """Zoomer"""
        self.zoom = max(0.1, min(10.0, facteur))


class Oeil:
    """Un œil individuel"""

    def __init__(self, cote: str):
        self.cote = cote  # 'gauche' ou 'droit'
        self.retine = Retine()
        self.cristallin = Cristallin()
        self.ouvert: bool = True
        self.mode: ModeVision = ModeVision.NORMALE

    def ouvrir(self) -> None:
        self.ouvert = True

    def fermer(self) -> None:
        self.ouvert = False

    def cligner(self) -> None:
        """Cligner - rafraîchir"""
        self.retine.fatigue = max(0, self.retine.fatigue - 0.1)

    def voir(self, source: str) -> Dict[str, Any]:
        """Voir quelque chose"""
        if not self.ouvert:
            return {'erreur': 'œil fermé'}
        if not PIL_DISPO:
            return {'erreur': 'PIL non installé - pip install pillow'}

        try:
            # Charger l'image
            if source.startswith('http'):
                import requests
                r = requests.get(source, timeout=10)
                img = Image.open(io.BytesIO(r.content))
            elif source.startswith('data:image'):
                # Base64
                data = source.split(',')[1]
                img = Image.open(io.BytesIO(base64.b64decode(data)))
            else:
                img = Image.open(source)

            # Capturer sur la rétine
            capture = self.retine.capturer(img)

            # Appliquer le mode de vision
            analyse = self._analyser(img)

            self.retine.fatigue += 0.05

            return {
                'source': source[:100],
                'capture': capture,
                'analyse': analyse,
                'mode': self.mode.value
            }

        except Exception as e:
            return {'erreur': str(e)}

    def _analyser(self, img: 'Image.Image') -> Dict[str, Any]:
        """Analyser selon le mode"""
        if self.mode == ModeVision.TEXTE and OCR_DISPO:
            return self._lire_texte(img)
        elif self.mode == ModeVision.CONTOURS and CV2_DISPO:
            return self._detecter_contours(img)
        else:
            return self._vision_normale(img)

    def _vision_normale(self, img: 'Image.Image') -> Dict[str, Any]:
        """Vision normale - description générale"""
        colors = img.getcolors(maxcolors=1000) if img.mode in ['RGB', 'RGBA'] else []
        dominant = None
        if colors:
            colors_sorted = sorted(colors, key=lambda x: x[0], reverse=True)
            if colors_sorted:
                dominant = colors_sorted[0][1]

        return {
            'type': 'normale',
            'couleur_dominante': dominant,
            'format': img.format,
            'taille': img.size
        }

    def _lire_texte(self, img: 'Image.Image') -> Dict[str, Any]:
        """OCR - lire le texte dans l'image"""
        if not OCR_DISPO:
            return {'type': 'texte', 'erreur': 'pytesseract non installé'}

        try:
            texte = pytesseract.image_to_string(img, lang='fra+eng')
            return {
                'type': 'texte',
                'contenu': texte.strip(),
                'longueur': len(texte)
            }
        except Exception as e:
            return {'type': 'texte', 'erreur': str(e)}

    def _detecter_contours(self, img: 'Image.Image') -> Dict[str, Any]:
        """Détecter les contours"""
        if not CV2_DISPO:
            return {'type': 'contours', 'erreur': 'opencv non installé'}

        try:
            # Convertir PIL -> OpenCV
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            return {
                'type': 'contours',
                'nombre_contours': len(contours),
                'formes_detectees': self._classifier_formes(contours)
            }
        except Exception as e:
            return {'type': 'contours', 'erreur': str(e)}

    def _classifier_formes(self, contours) -> Dict[str, int]:
        """Classifier les formes détectées"""
        formes = {'cercles': 0, 'rectangles': 0, 'triangles': 0, 'autres': 0}

        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.04 * cv2.arcLength(cnt, True), True)
            vertices = len(approx)

            if vertices == 3:
                formes['triangles'] += 1
            elif vertices == 4:
                formes['rectangles'] += 1
            elif vertices > 6:
                formes['cercles'] += 1
            else:
                formes['autres'] += 1

        return formes


class Yeux:
    """Le système visuel complet - deux yeux"""

    def __init__(self):
        self.gauche = Oeil('gauche')
        self.droit = Oeil('droit')
        self.vision_stereo: bool = True

    def ouvrir(self) -> None:
        """Ouvrir les deux yeux"""
        self.gauche.ouvrir()
        self.droit.ouvrir()

    def fermer(self) -> None:
        """Fermer les deux yeux"""
        self.gauche.fermer()
        self.droit.fermer()

    def cligner(self) -> None:
        """Cligner des yeux"""
        self.gauche.cligner()
        self.droit.cligner()

    def regarder(self, source: str) -> Dict[str, Any]:
        """Regarder quelque chose avec les deux yeux"""
        vue_g = self.gauche.voir(source)
        vue_d = self.droit.voir(source)

        # Fusion stéréo
        if self.vision_stereo and 'erreur' not in vue_g and 'erreur' not in vue_d:
            return {
                'stereo': True,
                'gauche': vue_g,
                'droit': vue_d,
                'profondeur_estimee': self._estimer_profondeur(vue_g, vue_d)
            }

        return vue_g if 'erreur' not in vue_g else vue_d

    def _estimer_profondeur(self, vue_g: Dict, vue_d: Dict) -> str:
        """Estimer la profondeur (simplifiée)"""
        # En vrai il faudrait de la stéréo-correspondance
        return "proche" if vue_g.get('capture', {}).get('contraste', 0) > 50 else "loin"

    def lire(self, source: str) -> Dict[str, Any]:
        """Lire du texte dans une image"""
        self.gauche.mode = ModeVision.TEXTE
        resultat = self.gauche.voir(source)
        self.gauche.mode = ModeVision.NORMALE
        return resultat

    def scanner(self, source: str) -> Dict[str, Any]:
        """Scanner les contours/formes"""
        self.droit.mode = ModeVision.CONTOURS
        resultat = self.droit.voir(source)
        self.droit.mode = ModeVision.NORMALE
        return resultat

    def mode_nocturne(self, activer: bool = True) -> None:
        """Activer/désactiver le mode nocturne"""
        mode = ModeVision.NOCTURNE if activer else ModeVision.NORMALE
        self.gauche.mode = mode
        self.droit.mode = mode
        self.gauche.retine.sensibilite = 1.0 if activer else 0.8
        self.droit.retine.sensibilite = 1.0 if activer else 0.8

    def etat(self) -> Dict[str, Any]:
        """État du système visuel"""
        return {
            'gauche': {
                'ouvert': self.gauche.ouvert,
                'mode': self.gauche.mode.value,
                'fatigue': self.gauche.retine.fatigue,
                'focus': self.gauche.cristallin.focus
            },
            'droit': {
                'ouvert': self.droit.ouvert,
                'mode': self.droit.mode.value,
                'fatigue': self.droit.retine.fatigue,
                'focus': self.droit.cristallin.focus
            },
            'vision_stereo': self.vision_stereo,
            'libs_disponibles': {
                'PIL': PIL_DISPO,
                'OpenCV': CV2_DISPO,
                'OCR': OCR_DISPO
            }
        }


# Instance globale
yeux = Yeux()
