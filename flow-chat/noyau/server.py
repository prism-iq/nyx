#!/opt/flow-chat/venv/bin/python
"""noyau server - logique pure, mémoire de travail"""

from flask import Flask, request, jsonify
from main import Certitude, Pensee, evaluer, cross_domain, decide, IRON_CODE
from collections import deque
from datetime import datetime

app = Flask(__name__)

# mémoire de travail (court terme)
working_memory = deque(maxlen=100)

# mémoire des décisions
decisions = deque(maxlen=50)

@app.route('/health')
def health():
    return jsonify({
        "organ": "noyau",
        "status": "thinking",
        "working_memory": len(working_memory),
        "decisions": len(decisions),
        "iron_code": IRON_CODE[:20] + "..."
    })

@app.route('/think', methods=['POST'])
def think():
    """Ajouter une pensée à la mémoire de travail"""
    data = request.get_json() or {}
    content = data.get('thought', '')

    if not content:
        return jsonify({"error": "thought required"}), 400

    certitude = evaluer(content)
    pensee = Pensee(
        contenu=content,
        certitude=certitude,
        source=data.get('source', 'external')
    )

    working_memory.append({
        "thought": content,
        "certitude": certitude.name,
        "timestamp": datetime.now().isoformat()
    })

    return jsonify({
        "stored": True,
        "certitude": certitude.name,
        "memory_size": len(working_memory)
    })

@app.route('/recall')
def recall():
    """Rappeler les pensées récentes"""
    n = request.args.get('n', 10, type=int)
    thoughts = list(working_memory)[-n:]
    return jsonify({"thoughts": thoughts})

@app.route('/decide', methods=['POST'])
def decide_endpoint():
    """Prendre une décision"""
    data = request.get_json() or {}
    options = data.get('options', [])
    context = data.get('context', '')

    if not options:
        return jsonify({"error": "options required"}), 400

    choice = decide(options, context)

    decisions.append({
        "options": options,
        "choice": choice,
        "context": context,
        "timestamp": datetime.now().isoformat()
    })

    return jsonify({"decision": choice})

@app.route('/cross', methods=['POST'])
def cross():
    """Trouver des connexions cross-domain"""
    data = request.get_json() or {}
    concept = data.get('concept', '')

    if not concept:
        return jsonify({"error": "concept required"}), 400

    connections = cross_domain(concept)
    return jsonify({"connections": connections})

@app.route('/iron')
def iron():
    """Le code de fer"""
    return jsonify({"iron_code": IRON_CODE})

if __name__ == '__main__':
    print("🧠 noyau :8094 - pure logic")
    app.run(host='127.0.0.1', port=8094)
