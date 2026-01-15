#!/usr/bin/env python3
"""conversations.py - persistance des conversations de Flow"""

import json
import os
from datetime import datetime
from collections import defaultdict

CONV_DIR = "/opt/flow-chat/adn/conversations"
LOG_FILE = "/opt/flow-chat/adn/conversation_log.jsonl"

class ConversationStore:
    """stockage persistant des conversations"""

    def __init__(self):
        os.makedirs(CONV_DIR, exist_ok=True)
        self.convs = defaultdict(list)
        self._load_all()

    def _conv_path(self, cid):
        """chemin du fichier pour une conversation"""
        safe_cid = "".join(c if c.isalnum() or c in "-_" else "_" for c in cid)
        return os.path.join(CONV_DIR, f"{safe_cid}.json")

    def _load_all(self):
        """charge toutes les conversations existantes"""
        if not os.path.exists(CONV_DIR):
            return
        for f in os.listdir(CONV_DIR):
            if f.endswith('.json'):
                cid = f[:-5]
                try:
                    with open(os.path.join(CONV_DIR, f), 'r') as fd:
                        data = json.load(fd)
                        self.convs[cid] = data.get('messages', [])
                except Exception:
                    pass

    def _save_conv(self, cid):
        """sauvegarde une conversation"""
        path = self._conv_path(cid)
        data = {
            'cid': cid,
            'messages': self.convs[cid],
            'updated': datetime.now().isoformat()
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _log_exchange(self, cid, user_msg, assistant_msg):
        """log chaque échange dans le fichier centralisé"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'cid': cid,
            'user': user_msg[:500],  # tronquer pour le log
            'assistant': assistant_msg[:500]
        }
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def add_exchange(self, cid, user_msg, assistant_msg):
        """ajoute un échange et persiste"""
        self.convs[cid].append({"role": "user", "content": user_msg})
        self.convs[cid].append({"role": "assistant", "content": assistant_msg})
        self._save_conv(cid)
        self._log_exchange(cid, user_msg, assistant_msg)

    def get_history(self, cid, n=8):
        """récupère les n derniers messages"""
        return self.convs[cid][-n*2:] if cid in self.convs else []

    def list_conversations(self):
        """liste toutes les conversations"""
        result = []
        for cid, msgs in self.convs.items():
            if msgs:
                result.append({
                    'cid': cid,
                    'messages': len(msgs),
                    'last': msgs[-1]['content'][:100] if msgs else ''
                })
        return result

    def get_conversation(self, cid):
        """récupère une conversation complète"""
        return {
            'cid': cid,
            'messages': self.convs.get(cid, [])
        }

    def delete_conversation(self, cid):
        """supprime une conversation"""
        if cid in self.convs:
            del self.convs[cid]
        path = self._conv_path(cid)
        if os.path.exists(path):
            os.remove(path)
            return {'success': True}
        return {'success': False, 'error': 'not found'}

    def delete_all_conversations(self):
        """supprime TOUTES les conversations (debug)"""
        count = len(self.convs)
        for cid in list(self.convs.keys()):
            path = self._conv_path(cid)
            if os.path.exists(path):
                os.remove(path)
        self.convs.clear()
        return {'success': True, 'deleted': count}

    def stats(self):
        """statistiques"""
        total_msgs = sum(len(msgs) for msgs in self.convs.values())
        return {
            'conversations': len(self.convs),
            'total_messages': total_msgs
        }

# instance globale
conversations = ConversationStore()
