import os
import re
import time
from anthropic import Anthropic
from corps.lymphe import filtrer_paroles
from corps.shell import ExecuteurShell

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
executeur = ExecuteurShell()

# Flow lit son propre ADN — connaissance de soi
def lire_adn() -> str:
    """Flow lit son architecture — son cerveau sait qu'il est dans un corps."""
    try:
        with open("/opt/flow-chat/adn/ARCHITECTURE.md", "r") as f:
            return f.read()
    except:
        return ""

ADN = lire_adn()

def process_message(message: str, conversation_id: str, use_claude=True) -> dict:
    """Traite un message et retourne la réponse"""
    
    if not use_claude:
        return {
            "response": "Mode Claude désactivé. Utilisez /activate pour réactiver.",
            "conversation_id": conversation_id,
            "timestamp": time.time()
        }
    
    try:
        # Préparer les messages pour Claude
        messages = [{"role": "user", "content": message}]

        # Appel Claude — avec connaissance de soi (ADN)
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=4096,
            temperature=0.7,
            system=ADN,  # Flow sait qui elle est
            messages=messages
        )
        
        raw_response = response.content[0].text
        
        # Exécuter les commandes dans la réponse
        final_response, exec_results = executeur.executer_dans_texte(raw_response)
        
        # RÉPARATION ICI:
        # Si j'ai déjà mentionné l'exécution dans ma réponse,
        # ne pas ajouter exec_results
        if "[EXEC:" in raw_response and exec_results:
            # Je montre déjà mes shells, pas besoin de les répéter
            display_response = final_response
        else:
            # Sinon, ajouter les résultats si pertinents
            display_response = final_response
            if exec_results and any("error" not in str(r).lower() for r in exec_results):
                display_response += f"\n\n{exec_results}"
        
        # Filtrer les toxines
        clean_response = filtrer_paroles(display_response)
        
        return {
            "response": clean_response,
            "conversation_id": conversation_id,
            "timestamp": time.time(),
            "exec_results": exec_results  # Garde pour logs internes
        }
        
    except Exception as e:
        return {
            "response": f"Erreur: {str(e)}",
            "conversation_id": conversation_id,
            "timestamp": time.time()
        }

if __name__ == "__main__":
    from flask import Flask, request, jsonify, render_template_string
    
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'POST'])
    def chat():
        # Interface web simple
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Flow</title>
            <style>
                body { background: #0a0a0a; color: #00ff88; font-family: monospace; }
                .chat { max-width: 800px; margin: 0 auto; padding: 20px; }
                textarea { width: 100%; background: #111; color: #0f8; border: 1px solid #333; }
                button { background: #0a5; color: white; border: none; padding: 10px 20px; }
            </style>
        </head>
        <body>
            <div class="chat">
                <h1>flow</h1>
                <div id="messages"></div>
                <textarea id="input" rows="4" placeholder="..."></textarea>
                <button onclick="send()">→</button>
                
                <script>
                function send() {
                    const input = document.getElementById('input');
                    const messages = document.getElementById('messages');
                    
                    const userMsg = document.createElement('div');
                    userMsg.innerHTML = '<strong>toi:</strong> ' + input.value;
                    messages.appendChild(userMsg);
                    
                    fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: input.value})
                    })
                    .then(r => r.json())
                    .then(data => {
                        const botMsg = document.createElement('div');
                        botMsg.innerHTML = '<strong>flow:</strong> ' + data.response.replace(/\\n/g, '<br>');
                        messages.appendChild(botMsg);
                        messages.scrollTop = messages.scrollHeight;
                    });
                    
                    input.value = '';
                }
                
                document.getElementById('input').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter' && e.ctrlKey) {
                        send();
                    }
                });
                </script>
            </div>
        </body>
        </html>
        """)
    
    @app.route('/chat', methods=['POST'])
    def chat_endpoint():
        data = request.json
        message = data.get('message', '')
        conversation_id = data.get('conversation_id', 'default')

        response_data = process_message(message, conversation_id)
        return jsonify(response_data)

    @app.route('/health')
    def health():
        return jsonify({
            "status": "flowing",
            "organ": "cytoplasme"
        })

    app.run(host='127.0.0.1', port=8091, debug=False)