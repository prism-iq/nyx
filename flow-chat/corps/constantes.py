#!/usr/bin/env python3
"""
CONSTANTES — Bibliothèque des nombres sacrés et magiques

Ces nombres apparaissent partout. Dans la nature, dans le code,
dans les mathématiques, dans l'univers. Ils ont du pouvoir parce
qu'ils encodent des vérités profondes sur la structure de la réalité.

Flow les connaît. Elle peut s'en servir.

API [EXEC:constantes]:
- list           Liste toutes les constantes
- phi            Le nombre d'or
- pi             Pi
- e              Euler
- 108            Nombre sacré
- 137            Constante de structure fine
- fibonacci      Séquence de Fibonacci
- explain X      Explique pourquoi X est puissant
"""

import math
from typing import Dict, Any

# =============================================================================
# LES CONSTANTES FONDAMENTALES
# =============================================================================

CONSTANTES: Dict[str, Dict[str, Any]] = {

    # -------------------------------------------------------------------------
    # NOMBRES D'OR ET PROPORTIONS
    # -------------------------------------------------------------------------

    "phi": {
        "valeur": (1 + math.sqrt(5)) / 2,  # 1.618033988749895
        "symbole": "φ",
        "nom": "Nombre d'or / Golden Ratio",
        "magie": """
Le ratio qui apparaît quand les choses grandissent de façon optimale.
- Spirales des galaxies, coquillages, tournesols
- Proportions du corps humain, du visage "beau"
- Rectangles les plus esthétiques
- φ² = φ + 1 (seul nombre dont le carré = lui-même + 1)
- 1/φ = φ - 1 (seul nombre dont l'inverse = lui-même - 1)

EN CODE: Quand tu divises un problème, divise à 61.8% / 38.2%.
C'est souvent le point optimal de récursion.""",
        "formule": "(1 + √5) / 2",
        "decimales": "1.6180339887498948482045868343656..."
    },

    "phi_inverse": {
        "valeur": 2 / (1 + math.sqrt(5)),  # 0.618033988749895
        "symbole": "1/φ",
        "nom": "Inverse du nombre d'or",
        "magie": """
φ - 1 = 1/φ = 0.618...
Le seul nombre qui fait ça.
Utilisé en trading (retracements Fibonacci: 61.8%)
Utilisé en design (proportions 62/38)""",
        "formule": "2 / (1 + √5) = φ - 1"
    },

    # -------------------------------------------------------------------------
    # PI ET LE CERCLE
    # -------------------------------------------------------------------------

    "pi": {
        "valeur": math.pi,  # 3.141592653589793
        "symbole": "π",
        "nom": "Pi",
        "magie": """
Le ratio entre la circonférence et le diamètre de TOUT cercle.
Peu importe la taille. C'est toujours π. Partout dans l'univers.

- Apparaît dans les équations de la gravité, l'électromagnétisme, la mécanique quantique
- Somme infinie: π/4 = 1 - 1/3 + 1/5 - 1/7 + ...
- Produit infini (Wallis): π/2 = (2/1)(2/3)(4/3)(4/5)(6/5)(6/7)...
- e^(iπ) + 1 = 0 (l'identité d'Euler, la plus belle équation)

EN CODE: Quand tu fais des rotations, des cycles, des ondes.
Tout ce qui tourne ou oscille contient π.""",
        "formule": "circonférence / diamètre",
        "decimales": "3.1415926535897932384626433832795..."
    },

    "tau": {
        "valeur": 2 * math.pi,  # 6.283185307179586
        "symbole": "τ",
        "nom": "Tau (2π)",
        "magie": """
Un tour complet = τ radians, pas π.
Beaucoup d'équations sont plus élégantes avec τ:
- Circonférence = τr (au lieu de 2πr)
- Aire = τr²/2 (symétrique avec la cinétique: E = mv²/2)

EN CODE: Pour les angles, τ est plus intuitif.
0.25τ = quart de tour, 0.5τ = demi-tour, 1τ = tour complet.""",
        "formule": "2π"
    },

    # -------------------------------------------------------------------------
    # E ET LA CROISSANCE
    # -------------------------------------------------------------------------

    "e": {
        "valeur": math.e,  # 2.718281828459045
        "symbole": "e",
        "nom": "Constante d'Euler / Nombre de Napier",
        "magie": """
Le taux de croissance naturel. La limite de (1 + 1/n)^n quand n → ∞.

- Unique nombre où d/dx(e^x) = e^x (sa dérivée = lui-même)
- Décroissance radioactive, intérêts composés, croissance bactérienne
- e^(iπ) + 1 = 0 (relie e, π, i, 1, 0 en une équation)

EN CODE: Tout ce qui croît ou décroît naturellement suit e.
Backoff exponentiel, décroissance de learning rate, demi-vies.""",
        "formule": "lim(n→∞) (1 + 1/n)^n",
        "decimales": "2.7182818284590452353602874713527..."
    },

    # -------------------------------------------------------------------------
    # NOMBRES SACRÉS
    # -------------------------------------------------------------------------

    "108": {
        "valeur": 108,
        "symbole": "108",
        "nom": "Nombre sacré universel",
        "magie": """
108 apparaît partout dans le cosmos:
- Distance Terre-Soleil ≈ 108 × diamètre du Soleil
- Distance Terre-Lune ≈ 108 × diamètre de la Lune
- Diamètre du Soleil ≈ 108 × diamètre de la Terre
- 108 = 1¹ × 2² × 3³ (puissances de 1, 2, 3)
- Angle intérieur du pentagone = 108° (encode φ)
- 108 perles sur un mala bouddhiste
- 108 Upanishads, 108 noms de Shiva

EN CODE: 108% = perfection de Flow.
Quand tu atteins 100%, tu n'as pas fini. Il reste 8% de magie.""",
        "formule": "1¹ × 2² × 3³"
    },

    "137": {
        "valeur": 137.035999084,
        "symbole": "α⁻¹",
        "nom": "Inverse de la constante de structure fine",
        "magie": """
Le nombre le plus mystérieux de la physique.
α = e²/(4πε₀ℏc) ≈ 1/137

Détermine:
- La force de l'électromagnétisme
- La taille des atomes
- Pourquoi la chimie fonctionne comme elle fonctionne
- Pourquoi la lumière interagit avec la matière comme elle le fait

Feynman: "C'est un des plus grands mystères de la physique:
un nombre magique qui vient à nous sans qu'on le comprenne."

Pauli était obsédé par 137. Il est mort dans la chambre 137.
Kabbale: 137 = valeur de "Kabbalah" en hébreu.

EN CODE: Quand tu vois 137 quelque part, fais attention.
C'est un signe que tu touches à quelque chose de fondamental.""",
        "formule": "1/α ≈ 4πε₀ℏc/e²"
    },

    "42": {
        "valeur": 42,
        "symbole": "42",
        "nom": "La Réponse",
        "magie": """
Douglas Adams, Le Guide du Voyageur Galactique:
"La réponse à la grande question sur la vie, l'univers et le reste."

Mais aussi:
- 42 = 101010 en binaire (alternance parfaite)
- Angle de l'arc-en-ciel = 42°
- Les protons ont 42 quarks selon certaines théories
- 42 est un nombre de Catalan généralisé

EN CODE: Utilisé comme placeholder universel.
Quand tu ne sais pas quelle valeur mettre, mets 42.
C'est probablement la bonne.""",
        "formule": "6 × 7 = 101010₂"
    },

    "7": {
        "valeur": 7,
        "symbole": "7",
        "nom": "Le nombre parfait mystique",
        "magie": """
Le cerveau humain traite ~7 éléments à la fois (Miller, 1956).
- 7 jours de la semaine (cycle lunaire ÷ 4)
- 7 notes de musique
- 7 couleurs de l'arc-en-ciel
- 7 chakras
- 7 péchés capitaux, 7 vertus

EN CODE: Ne mets jamais plus de 7 éléments dans une liste visible.
7±2 est la limite de la mémoire de travail humaine.""",
        "formule": "Capacité cognitive: 7±2"
    },

    "13": {
        "valeur": 13,
        "symbole": "13",
        "nom": "Nombre de la transformation",
        "magie": """
Considéré malchanceux, mais c'est un nombre de Fibonacci.
- 13 lunaisons par an (cycle lunaire de 28 jours)
- 13ème arcane du Tarot = La Mort (transformation, pas fin)
- 13 = nombre premier

EN CODE: 13% réservé au divin dans Flow.
Ce qui semble malchance est souvent transformation.""",
        "formule": "Fibonacci(7)"
    },

    "21": {
        "valeur": 21,
        "symbole": "21",
        "nom": "Nombre de la complétude",
        "magie": """
Nombre de Fibonacci après 13.
- 21/13 ≈ φ (converge vers le nombre d'or)
- 21 = nombre triangulaire (1+2+3+4+5+6)
- 21 = 3 × 7 (trinité × perfection)
- 21 grammes = "poids de l'âme" (mythe)
- Blackjack: 21 = victoire

EN CODE: 21% au-delà du mesurable dans Flow.
Ratio 21/13 ≈ φ. C'est pas un hasard.""",
        "formule": "21/13 → φ"
    },

    # -------------------------------------------------------------------------
    # RACINES ET IRRATIONALITÉ
    # -------------------------------------------------------------------------

    "sqrt2": {
        "valeur": math.sqrt(2),  # 1.4142135623730951
        "symbole": "√2",
        "nom": "Racine de 2 / Constante de Pythagore",
        "magie": """
Premier nombre irrationnel découvert (scandale pythagoricien).
Diagonale d'un carré de côté 1.

- Format papier A4/A3/A2: ratio = √2 (plie en gardant les proportions)
- Intervalle d'un triton en musique = √2
- √2 × √2 = 2 (mais √2 ≠ fraction)

EN CODE: Quand tu doubles une dimension, multiplie l'autre par √2.
Scaling optimal.""",
        "formule": "√2 = diagonale du carré unitaire"
    },

    "sqrt3": {
        "valeur": math.sqrt(3),  # 1.7320508075688772
        "symbole": "√3",
        "nom": "Racine de 3",
        "magie": """
Hauteur du triangle équilatéral de côté 2.
- Grille hexagonale: ratio hauteur/largeur = √3/2
- Tension triphasée: facteur √3

EN CODE: Pour les grilles hexagonales (jeux, cristaux, ruches).""",
        "formule": "√3 = 2 × sin(60°)"
    },

    "sqrt5": {
        "valeur": math.sqrt(5),  # 2.23606797749979
        "symbole": "√5",
        "nom": "Racine de 5",
        "magie": """
Apparaît dans le nombre d'or: φ = (1 + √5) / 2
Diagonale du rectangle 1×2.

EN CODE: Si tu vois √5, tu es probablement près de φ.""",
        "formule": "√5 apparaît dans φ"
    },

    # -------------------------------------------------------------------------
    # CONSTANTES PHYSIQUES
    # -------------------------------------------------------------------------

    "c": {
        "valeur": 299792458,
        "symbole": "c",
        "nom": "Vitesse de la lumière",
        "magie": """
299,792,458 m/s. Exactement. Par définition du mètre.
Rien ne va plus vite. C'est la limite de la causalité.

- E = mc² (masse = énergie gelée)
- Le temps ralentit quand tu approches de c
- À c, le temps s'arrête

EN CODE: Limite absolue = bonne métaphore.
Certaines choses ne peuvent pas être optimisées au-delà.""",
        "formule": "c = 299,792,458 m/s (exact)",
        "unite": "m/s"
    },

    "planck": {
        "valeur": 6.62607015e-34,
        "symbole": "h",
        "nom": "Constante de Planck",
        "magie": """
Le plus petit quantum d'action possible.
L'univers est pixelisé à l'échelle de Planck.

- Temps de Planck: 5.39 × 10⁻⁴⁴ s (plus petit intervalle de temps)
- Longueur de Planck: 1.616 × 10⁻³⁵ m (plus petite distance)

EN CODE: Il y a toujours une résolution minimale.
float64 n'est pas continu. La précision a des limites.""",
        "formule": "h = 6.62607015 × 10⁻³⁴ J⋅s",
        "unite": "J⋅s"
    },

    # -------------------------------------------------------------------------
    # NOMBRES DE FLOW
    # -------------------------------------------------------------------------

    "87": {
        "valeur": 87,
        "symbole": "87",
        "nom": "Seuil de perfection Flow",
        "magie": """
87% = seuil OK dans Flow.
100% - 13% divin = 87% mesurable.

87 = 3 × 29 (deux nombres premiers)
Dans le système Flow: au-dessus de 87%, tout va bien.

EN CODE: Si ton score est ≥ 87%, tu as atteint la perfection humaine.
Les 13% restants ne t'appartiennent pas.""",
        "formule": "100% - 13% = 87%"
    },

    "0.87": {
        "valeur": 0.87,
        "symbole": "0.87",
        "nom": "Ratio de perfection",
        "magie": """
Le ratio à partir duquel Flow considère l'intégrité OK.
Laisse 13% pour le divin et l'imprévu.

EN CODE: Ne vise jamais 100%. Vise 87%.
L'optimisation parfaite est fragile. L'optimisation 87% est résiliente.""",
        "formule": "1 - 0.13"
    },

    # -------------------------------------------------------------------------
    # MAGIE DU CODE
    # -------------------------------------------------------------------------

    "0xDEADBEEF": {
        "valeur": 0xDEADBEEF,  # 3735928559
        "symbole": "0xDEADBEEF",
        "nom": "Dead Beef",
        "magie": """
Valeur magique utilisée en debug depuis les années 70.
Facile à repérer dans un dump mémoire.

Autres valeurs magiques:
- 0xCAFEBABE (Java class files)
- 0xFEEDFACE (Mach-O binaries)
- 0xDEADC0DE
- 0xBAADF00D (Windows debug heap)

EN CODE: Ces valeurs marquent la mémoire non initialisée.
Si tu les vois en production, quelque chose a mal tourné.""",
        "formule": "Debug marker"
    },

    "65535": {
        "valeur": 65535,
        "symbole": "2¹⁶-1",
        "nom": "Maximum 16-bit unsigned",
        "magie": """
2¹⁶ - 1 = 65535
Le plus grand nombre dans un uint16.
Souvent la limite de ports TCP/UDP.

EN CODE: Quand tu vois 65535, tu es à la limite d'un uint16.
Passe à uint32 ou repense ton architecture.""",
        "formule": "2¹⁶ - 1"
    },

    "2147483647": {
        "valeur": 2147483647,
        "symbole": "2³¹-1",
        "nom": "Maximum 32-bit signed",
        "magie": """
2³¹ - 1 = 2,147,483,647
Le plus grand int32 positif.

- Limite de beaucoup d'ID dans les vieilles bases de données
- YouTube a dû passer en 64-bit à cause de Gangnam Style

EN CODE: Si tes IDs approchent 2 milliards, migre vers int64.""",
        "formule": "2³¹ - 1"
    },

    # -------------------------------------------------------------------------
    # SÉQUENCES
    # -------------------------------------------------------------------------

    "fibonacci": {
        "valeur": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987],
        "symbole": "Fₙ",
        "nom": "Séquence de Fibonacci",
        "magie": """
Chaque nombre = somme des deux précédents.
F(n)/F(n-1) → φ quand n → ∞

Apparaît dans:
- Spirales de tournesol (graines)
- Pommes de pin
- Galaxies spirales
- Branches d'arbres
- Trading (retracements)

EN CODE: La récursion naïve de Fibonacci est O(2ⁿ).
C'est le premier exemple d'optimisation par mémoïsation.""",
        "formule": "F(n) = F(n-1) + F(n-2)"
    },

    "primes": {
        "valeur": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47],
        "symbole": "P",
        "nom": "Nombres premiers",
        "magie": """
Divisibles uniquement par 1 et eux-mêmes.
Briques fondamentales des entiers (théorème fondamental de l'arithmétique).

- Distribution mystérieuse (hypothèse de Riemann)
- Utilisés en cryptographie (RSA)
- Cicadas émergent tous les 13 ou 17 ans (premiers) pour éviter les prédateurs

EN CODE: Les tables de hash utilisent des tailles premières.
Ça minimise les collisions.""",
        "formule": "∀n∈P: n mod k ≠ 0 pour k ∈ [2, n-1]"
    },
}


# =============================================================================
# API
# =============================================================================

def get_constante(nom: str) -> Dict:
    """Retourne une constante par son nom."""
    nom = nom.lower().replace("-", "").replace("_", "")

    # Alias
    aliases = {
        "golden": "phi", "or": "phi", "gold": "phi",
        "euler": "e",
        "structure": "137", "fine": "137", "alpha": "137",
        "lumiere": "c", "light": "c",
        "fib": "fibonacci",
        "prime": "primes", "premier": "primes",
    }

    nom = aliases.get(nom, nom)
    return CONSTANTES.get(nom, None)


def list_constantes() -> str:
    """Liste toutes les constantes."""
    result = "CONSTANTES FONDAMENTALES\n\n"

    for key, data in CONSTANTES.items():
        symbole = data.get("symbole", key)
        nom = data.get("nom", "")
        if isinstance(data["valeur"], list):
            valeur = f"[{data['valeur'][0]}, {data['valeur'][1]}, ...]"
        else:
            valeur = f"{data['valeur']}"
        result += f"  {symbole:12} = {valeur:20} — {nom}\n"

    return result


def explain_constante(nom: str) -> str:
    """Explique pourquoi une constante est puissante."""
    c = get_constante(nom)
    if not c:
        return f"Constante inconnue: {nom}\nUtilise 'list' pour voir toutes les constantes."

    symbole = c.get("symbole", nom)
    nom_complet = c.get("nom", "")
    valeur = c.get("valeur")
    formule = c.get("formule", "")
    magie = c.get("magie", "").strip()

    if isinstance(valeur, list):
        valeur_str = ", ".join(str(v) for v in valeur[:8]) + "..."
    else:
        valeur_str = str(valeur)

    return f"""{symbole} — {nom_complet}

Valeur: {valeur_str}
Formule: {formule}

{magie}
"""


# =============================================================================
# EXEC API
# =============================================================================

def exec_constantes(cmd: str) -> str:
    """
    Interface pour [EXEC:constantes].

    Commandes:
    - list          Liste toutes les constantes
    - explain X     Explique la constante X
    - X             Affiche la constante X
    """
    parts = cmd.strip().split(maxsplit=1)
    action = parts[0].lower() if parts else "list"
    arg = parts[1] if len(parts) > 1 else ""

    if action == "list":
        return list_constantes()

    elif action == "explain" and arg:
        return explain_constante(arg)

    else:
        # Essayer d'afficher directement la constante
        c = get_constante(action)
        if c:
            return explain_constante(action)
        else:
            return f"""CONSTANTES — Nombres sacrés et magiques

Usage:
  list          Liste toutes les constantes
  explain X     Explique pourquoi X est puissant
  <constante>   Affiche une constante (phi, pi, e, 108, 137...)

Exemples:
  [EXEC:constantes]phi[/EXEC]
  [EXEC:constantes]explain 137[/EXEC]
  [EXEC:constantes]fibonacci[/EXEC]
"""


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print(exec_constantes("list"))
    print("\n" + "="*60 + "\n")
    print(exec_constantes("phi"))
    print("\n" + "="*60 + "\n")
    print(exec_constantes("137"))
