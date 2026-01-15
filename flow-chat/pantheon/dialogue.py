#!/usr/bin/env python3
"""dialogue.py - gère les conversations multi-voix avec le panthéon"""

from flask import Blueprint, request, jsonify
from council import convene_council
from resonance import detect_resonance, load_god
import os

pantheon_bp = Blueprint('pantheon', __name__)

# historique des conseils par session
council_history = {}

@pantheon_bp.route('/council', methods=['POST'])
def council():
    """endpoint principal - convoque le conseil"""
    data = request.get_json()
    question = data.get('question', '').strip()
    cid = data.get('cid', 'default')

    if not question:
        return jsonify({'error': 'no question'})

    # convoquer le conseil
    result = convene_council(question)

    # stocker dans l'historique
    if cid not in council_history:
        council_history[cid] = []
    council_history[cid].append(result)

    return jsonify(result)

@pantheon_bp.route('/gods', methods=['GET'])
def list_gods():
    """liste tous les dieux disponibles"""
    gods_path = "/var/www/flow/pantheon/gods"
    gods = []
    for f in os.listdir(gods_path):
        if f.endswith('.md'):
            name = f[:-3]
            content = load_god(name)
            # extraire le domaine
            domain = ""
            if content:
                for line in content.split('\n'):
                    if line.startswith('## domaine'):
                        idx = content.find(line)
                        next_section = content.find('##', idx + 10)
                        domain = content[idx+11:next_section].strip().split('\n')[0]
                        break
            gods.append({'name': name, 'domain': domain})
    return jsonify({'gods': gods})

@pantheon_bp.route('/god/<name>', methods=['GET'])
def get_god(name):
    """récupère un dieu spécifique"""
    content = load_god(name)
    if content:
        return jsonify({'name': name, 'content': content})
    return jsonify({'error': 'god not found'}), 404

@pantheon_bp.route('/resonance', methods=['POST'])
def check_resonance():
    """vérifie quels dieux résonnent avec une question sans convoquer le conseil"""
    data = request.get_json()
    question = data.get('question', '')
    gods = detect_resonance(question)
    return jsonify({'question': question, 'gods': gods})

@pantheon_bp.route('/history/<cid>', methods=['GET'])
def get_history(cid):
    """récupère l'historique des conseils pour une session"""
    history = council_history.get(cid, [])
    return jsonify({'cid': cid, 'councils': history})

def init_pantheon(app):
    """initialise le blueprint pantheon dans une app Flask"""
    app.register_blueprint(pantheon_bp, url_prefix='/pantheon')
