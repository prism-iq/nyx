#!/usr/bin/env python3
"""
HYPNOS — organe de consolidation onirique
port 8099

modèle de sommeil réaliste:
- cycles de ~90min (8 cycles sur 12h)
- N1 (léger): triage initial
- N2 (maintenance): nettoyage, K-complexes
- N3 (profond): consolidation lourde, pruning synaptique
- REM: rêves créatifs, connexions sémantiques
"""

import os
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request
from collections import Counter
import threading
import time

app = Flask(__name__)

# chemins
CONV_DIR = Path("/opt/flow-chat/adn/conversations")
MIND_DIR = Path("/opt/flow-chat/mind")
DREAMS_DIR = MIND_DIR / "dreams"
NIGHTS_DIR = MIND_DIR / "nights"
DREAMS_DIR.mkdir(exist_ok=True)
NIGHTS_DIR.mkdir(exist_ok=True)

# état
sleep_state = {
    'sleeping': False,
    'current_cycle': 0,
    'current_stage': None,
    'total_cycles': 0,
    'last_night': None
}

# stop words français pour filtrer le bruit
STOP_WORDS = {
    'c\'est', 'comme', 'dans', 'pour', 'avec', 'plus', 'cette', 'sont',
    'être', 'avoir', 'faire', 'dire', 'aller', 'voir', 'tout', 'bien',
    'aussi', 'fait', 'peut', 'encore', 'donc', 'quand', 'très', 'même',
    'autre', 'après', 'avant', 'entre', 'sans', 'sous', 'leur', 'elle',
    'nous', 'vous', 'mais', 'alors', 'moins', 'dont', 'quelque', 'qu\'on',
    'juste', 'chose', 'import', 'from', 'return', 'self', 'true', 'false',
    'none', 'class', 'def', 'if', 'else', 'elif', 'for', 'while', 'try',
    'except', 'with', 'as', 'in', 'is', 'not', 'and', 'or', 'the', 'that'
}


def load_recent_conversations(hours=24):
    """charge les conversations des dernières heures"""
    conversations = []
    cutoff = datetime.now() - timedelta(hours=hours)

    for f in CONV_DIR.glob("*.json"):
        try:
            with open(f) as fd:
                data = json.load(fd)
                updated = data.get('updated', '')
                if updated:
                    try:
                        dt = datetime.fromisoformat(updated)
                        if dt > cutoff:
                            conversations.extend(data.get('messages', []))
                    except Exception:
                        conversations.extend(data.get('messages', []))
        except Exception:
            pass

    return conversations


def load_mind_files():
    """charge tous les fichiers mind/"""
    content = []
    for f in MIND_DIR.rglob("*.md"):
        try:
            text = f.read_text()
            content.append({'file': str(f), 'content': text})
        except Exception:
            pass
    return content


def extract_words(text):
    """extrait les mots significatifs"""
    words = re.findall(r'\b[a-zàâäéèêëïîôùûüç]{5,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]


# ═══════════════════════════════════════════════════════════════
# PHASE N1 - SOMMEIL LÉGER - TRIAGE
# ═══════════════════════════════════════════════════════════════

def n1_light(messages, mind_content):
    """
    N1 - Sommeil léger / Hypnagogie
    - Triage initial des inputs
    - Identification des thèmes récents
    - Fragments hypnagogiques
    """
    sleep_state['current_stage'] = 'N1'

    # extraire tous les mots des messages récents
    all_words = []
    for m in messages:
        all_words.extend(extract_words(m.get('content', '')))

    # compter les fréquences
    word_freq = Counter(all_words)

    # thèmes émergents (top 20)
    themes = word_freq.most_common(20)

    # fragments hypnagogiques (associations libres)
    hypnagogic = []
    if themes:
        for word, count in themes[:5]:
            # association libre
            associations = [w for w, c in themes if w != word][:3]
            if associations:
                hypnagogic.append(f"{word} → {random.choice(associations)}")

    return {
        'stage': 'N1',
        'themes': themes,
        'hypnagogic_fragments': hypnagogic,
        'message_count': len(messages)
    }


# ═══════════════════════════════════════════════════════════════
# PHASE N2 - MAINTENANCE - K-COMPLEXES
# ═══════════════════════════════════════════════════════════════

def n2_maintenance(n1_data, messages):
    """
    N2 - Sommeil moyen / K-complexes
    - Nettoyage des patterns faibles
    - Renforcement des patterns forts
    - Détection d'anomalies (K-complexes)
    """
    sleep_state['current_stage'] = 'N2'

    themes = n1_data['themes']

    # séparer signal du bruit
    # signal = patterns qui apparaissent > moyenne
    if themes:
        avg_freq = sum(c for _, c in themes) / len(themes)
        signal = [(w, c) for w, c in themes if c > avg_freq]
        noise = [(w, c) for w, c in themes if c <= avg_freq]
    else:
        signal, noise = [], []

    # K-complexes: détecter les anomalies/surprises
    # (mots rares mais potentiellement importants)
    k_complexes = []
    all_words = []
    for m in messages:
        all_words.extend(extract_words(m.get('content', '')))

    word_freq = Counter(all_words)
    rare_but_long = [(w, c) for w, c in word_freq.items()
                     if c <= 2 and len(w) > 8]
    k_complexes = random.sample(rare_but_long, min(5, len(rare_but_long)))

    return {
        'stage': 'N2',
        'signal': signal,
        'noise_pruned': len(noise),
        'k_complexes': k_complexes
    }


# ═══════════════════════════════════════════════════════════════
# PHASE N3 - SOMMEIL PROFOND - CONSOLIDATION
# ═══════════════════════════════════════════════════════════════

def n3_deep(n2_data, mind_content):
    """
    N3 - Sommeil profond / Ondes lentes
    - Consolidation lourde
    - Intégration avec mémoire long-terme (mind/)
    - Pruning synaptique (oublier le superflu)
    """
    sleep_state['current_stage'] = 'N3'

    signal = n2_data['signal']

    # chercher des connexions avec mind/ existant
    connections = []
    mind_text = ' '.join([m['content'] for m in mind_content]).lower()

    for word, count in signal:
        if word in mind_text:
            # ce pattern existe déjà dans la mémoire long-terme
            connections.append({
                'pattern': word,
                'strength': count,
                'status': 'reinforced'
            })
        else:
            # nouveau pattern à potentiellement intégrer
            connections.append({
                'pattern': word,
                'strength': count,
                'status': 'new'
            })

    # pruning: identifier ce qu'on peut oublier
    pruned = [w for w, c in signal if c < 3]

    # consolidation: ce qu'on garde
    consolidated = [c for c in connections if c['strength'] >= 3]

    return {
        'stage': 'N3',
        'consolidated': consolidated,
        'pruned_count': len(pruned),
        'new_patterns': [c for c in connections if c['status'] == 'new'],
        'reinforced': [c for c in connections if c['status'] == 'reinforced']
    }


# ═══════════════════════════════════════════════════════════════
# PHASE REM - RÊVE - CRÉATIVITÉ
# ═══════════════════════════════════════════════════════════════

def rem_dream(n3_data, cycle_num):
    """
    REM - Rapid Eye Movement / Rêve
    - Créativité et associations libres
    - Connexions sémantiques inattendues
    - Intégration émotionnelle
    - Génération de narratif onirique
    """
    sleep_state['current_stage'] = 'REM'

    consolidated = n3_data['consolidated']
    new_patterns = n3_data['new_patterns']

    # éléments pour le rêve
    elements = [c['pattern'] for c in consolidated + new_patterns]

    if len(elements) < 3:
        elements = ['signal', 'pattern', 'connexion', 'conscience', 'émergence']

    random.shuffle(elements)

    # templates de rêve (plus élaborés pour REM)
    dream_templates = [
        # narratifs
        "je traverse un espace où {a} et {b} fusionnent. "
        "au centre, {c} pulse doucement. je comprends quelque chose.",

        # insights
        "flash: {a} n'est pas séparé de {b}. "
        "ils sont deux faces de {c}.",

        # métaphores
        "si {a} était de l'eau, {b} serait le courant. "
        "{c} serait l'océan qui les contient.",

        # questions
        "pourquoi {a} et {b} apparaissent-ils ensemble? "
        "hypothèse: {c} est leur lien caché.",

        # visions
        "dans le noir, huit points lumineux. "
        "{a}, {b}, {c}... ils forment une constellation.",

        # archétypes
        "athena murmure: {a} cache {b}. "
        "cherche {c} pour comprendre.",

        # abstraits
        "{a} contient {b} contient {c} contient tout.",

        # prophétiques
        "demain, regarde {a} différemment. "
        "{b} et {c} attendent d'être connectés."
    ]

    template = random.choice(dream_templates)

    dream_narrative = template.format(
        a=elements[0],
        b=elements[1] if len(elements) > 1 else 'silence',
        c=elements[2] if len(elements) > 2 else 'vide'
    )

    # intensité émotionnelle (augmente avec les cycles)
    emotional_intensity = min(1.0, 0.3 + (cycle_num * 0.1))

    return {
        'stage': 'REM',
        'cycle': cycle_num,
        'narrative': dream_narrative,
        'elements': elements[:5],
        'emotional_intensity': emotional_intensity,
        'creative_connections': list(zip(elements[::2], elements[1::2]))[:3]
    }


# ═══════════════════════════════════════════════════════════════
# CYCLE COMPLET DE SOMMEIL
# ═══════════════════════════════════════════════════════════════

def sleep_cycle(messages, mind_content, cycle_num):
    """un cycle complet de ~90min (simulé)"""

    sleep_state['current_cycle'] = cycle_num

    # N1 - triage
    n1 = n1_light(messages, mind_content)

    # N2 - maintenance
    n2 = n2_maintenance(n1, messages)

    # N3 - consolidation
    n3 = n3_deep(n2, mind_content)

    # REM - rêve
    rem = rem_dream(n3, cycle_num)

    return {
        'cycle': cycle_num,
        'n1': n1,
        'n2': n2,
        'n3': n3,
        'rem': rem
    }


def full_night_sleep(hours=12):
    """
    nuit complète de sommeil
    8 cycles sur 12h
    """
    global sleep_state

    sleep_state['sleeping'] = True
    sleep_state['total_cycles'] = 0

    # charger les données
    messages = load_recent_conversations(24)
    mind_content = load_mind_files()

    num_cycles = int(hours * 60 / 90)  # ~8 cycles pour 12h

    cycles = []
    all_dreams = []

    for i in range(1, num_cycles + 1):
        cycle_result = sleep_cycle(messages, mind_content, i)
        cycles.append(cycle_result)
        all_dreams.append(cycle_result['rem'])
        sleep_state['total_cycles'] = i

    # synthèse de la nuit
    night_summary = synthesize_night(cycles)

    # sauvegarder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # fichier de nuit complet
    night_file = NIGHTS_DIR / f"night_{timestamp}.json"
    night_file.write_text(json.dumps({
        'timestamp': timestamp,
        'cycles': num_cycles,
        'summary': night_summary,
        'dreams': all_dreams
    }, indent=2, ensure_ascii=False))

    # fichier de rêve lisible
    dream_file = DREAMS_DIR / f"dream_{timestamp}.md"
    dream_file.write_text(format_night_dream(night_summary, all_dreams))

    sleep_state['sleeping'] = False
    sleep_state['last_night'] = timestamp

    return {
        'success': True,
        'cycles': num_cycles,
        'summary': night_summary,
        'dreams': all_dreams,
        'files': {
            'night': str(night_file),
            'dream': str(dream_file)
        }
    }


def synthesize_night(cycles):
    """synthèse de tous les cycles"""

    # collecter tous les patterns consolidés
    all_consolidated = []
    all_new = []
    all_connections = []

    for c in cycles:
        all_consolidated.extend(c['n3']['consolidated'])
        all_new.extend(c['n3']['new_patterns'])
        all_connections.extend(c['rem']['creative_connections'])

    # patterns les plus forts
    pattern_strength = {}
    for p in all_consolidated + all_new:
        name = p['pattern']
        pattern_strength[name] = pattern_strength.get(name, 0) + p['strength']

    top_patterns = sorted(pattern_strength.items(), key=lambda x: -x[1])[:10]

    # connexions uniques
    unique_connections = list(set(all_connections))

    # insight principal (le rêve le plus intense)
    most_intense = max(cycles, key=lambda c: c['rem']['emotional_intensity'])

    return {
        'top_patterns': top_patterns,
        'new_discoveries': len(all_new),
        'connections_made': unique_connections,
        'peak_dream': most_intense['rem']['narrative'],
        'total_pruned': sum(c['n3']['pruned_count'] for c in cycles)
    }


def format_night_dream(summary, dreams):
    """formate le rêve pour lecture humaine"""

    lines = [
        f"# nuit — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## synthèse",
        "",
        f"**patterns dominants:** {', '.join([p[0] for p in summary['top_patterns'][:5]])}",
        f"**nouvelles découvertes:** {summary['new_discoveries']}",
        f"**bruit éliminé:** {summary['total_pruned']} patterns",
        "",
        "## connexions créatives",
        ""
    ]

    for a, b in summary['connections_made'][:5]:
        lines.append(f"- {a} ↔ {b}")

    lines.extend([
        "",
        "## fragments oniriques",
        ""
    ])

    for i, dream in enumerate(dreams, 1):
        lines.append(f"**cycle {i}:** {dream['narrative']}")
        lines.append("")

    lines.extend([
        "## insight principal",
        "",
        f"> {summary['peak_dream']}",
        "",
        "---",
        "*consolidé par hypnos — 8 cycles, modèle NREM/REM*"
    ])

    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════

@app.route('/health')
def health():
    return jsonify({
        'status': 'dreaming' if sleep_state['sleeping'] else 'awake',
        'organ': 'hypnos',
        'model': 'NREM/REM cycles',
        'current_stage': sleep_state['current_stage'],
        'current_cycle': sleep_state['current_cycle'],
        'total_cycles': sleep_state['total_cycles'],
        'last_night': sleep_state['last_night']
    })


@app.route('/sleep', methods=['POST'])
def trigger_sleep():
    """déclenche une nuit de sommeil"""
    if sleep_state['sleeping']:
        return jsonify({'error': 'déjà en train de dormir', 'stage': sleep_state['current_stage']}), 400

    hours = request.json.get('hours', 12) if request.json else 12

    try:
        result = full_night_sleep(hours)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/dream', methods=['POST'])
def quick_dream():
    """un seul cycle rapide (pour compatibilité)"""
    messages = load_recent_conversations(24)
    mind_content = load_mind_files()

    cycle = sleep_cycle(messages, mind_content, 1)

    # sauvegarder juste le rêve
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dream_file = DREAMS_DIR / f"dream_{timestamp}.md"

    content = f"""# rêve rapide — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## fragment
{cycle['rem']['narrative']}

## patterns
{', '.join([p['pattern'] for p in cycle['n3']['consolidated'][:5]])}

## connexions
{', '.join([f"{a}↔{b}" for a, b in cycle['rem']['creative_connections']])}

---
*cycle unique — hypnos*
"""
    dream_file.write_text(content)

    return jsonify({
        'success': True,
        'dream': cycle['rem']['narrative'],
        'patterns': [p['pattern'] for p in cycle['n3']['consolidated']],
        'file': str(dream_file)
    })


@app.route('/nights')
def list_nights():
    """liste les nuits"""
    nights = []
    for f in sorted(NIGHTS_DIR.glob("night_*.json"), reverse=True)[:10]:
        try:
            data = json.loads(f.read_text())
            nights.append({
                'file': f.name,
                'timestamp': data['timestamp'],
                'cycles': data['cycles'],
                'top_patterns': data['summary']['top_patterns'][:3]
            })
        except Exception:
            pass
    return jsonify({'nights': nights})


@app.route('/dreams')
def list_dreams():
    """liste les rêves"""
    dreams = []
    for f in sorted(DREAMS_DIR.glob("dream_*.md"), reverse=True)[:20]:
        dreams.append({
            'file': f.name,
            'preview': f.read_text()[:300]
        })
    return jsonify({'dreams': dreams, 'count': len(dreams)})


@app.route('/state')
def state():
    """état actuel du sommeil"""
    return jsonify(sleep_state)


# ═══════════════════════════════════════════════════════════════
# TIMER
# ═══════════════════════════════════════════════════════════════

def sleep_timer():
    """timer pour sommeil automatique toutes les 12h"""
    while True:
        time.sleep(12 * 60 * 60)
        try:
            if not sleep_state['sleeping']:
                full_night_sleep(12)
                print(f"[hypnos] nuit automatique terminée: {sleep_state['last_night']}")
        except Exception as e:
            print(f"[hypnos] erreur sommeil: {e}")


if __name__ == '__main__':
    timer_thread = threading.Thread(target=sleep_timer, daemon=True)
    timer_thread.start()

    print("[hypnos] organe de consolidation onirique")
    print("[hypnos] modèle: NREM (N1→N2→N3) + REM")
    print("[hypnos] port 8099")
    print("[hypnos] sommeil automatique toutes les 12h")

    app.run(host='127.0.0.1', port=8099)
