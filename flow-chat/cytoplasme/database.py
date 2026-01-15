#!/usr/bin/env python3
"""database.py - accès complet à la database pour Flow"""

import json
import os
from datetime import datetime
import psycopg2

ADN_PATH = "/opt/flow-chat/adn"
MEMORY_FILE = os.path.join(ADN_PATH, "memory.json")

class FlowDatabase:
    """Interface database pour Flow - prolog-style facts + SQL"""

    def __init__(self):
        self.memory = self._load_memory()

    def _load_memory(self):
        """charge la mémoire depuis le fichier"""
        default = {"facts": {}, "souvenirs": [], "concepts": {}}
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                # merge avec default pour s'assurer que toutes les clés existent
                for key in default:
                    if key not in data:
                        data[key] = default[key]
                return data
            except Exception:
                pass
        return default

    def _save_memory(self):
        """sauvegarde la mémoire"""
        os.makedirs(ADN_PATH, exist_ok=True)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    # === PROLOG-STYLE FACTS ===

    def assert_fact(self, predicate, *args):
        """ajoute un fait (prolog: assert)"""
        key = f"{predicate}({','.join(str(a) for a in args)})"
        self.memory["facts"][key] = {
            "predicate": predicate,
            "args": list(args),
            "timestamp": datetime.now().isoformat()
        }
        self._save_memory()
        return {'success': True, 'fact': key}

    def retract_fact(self, predicate, *args):
        """supprime un fait (prolog: retract)"""
        key = f"{predicate}({','.join(str(a) for a in args)})"
        if key in self.memory["facts"]:
            del self.memory["facts"][key]
            self._save_memory()
            return {'success': True}
        return {'success': False, 'error': 'fact not found'}

    def query_facts(self, predicate=None):
        """cherche des faits"""
        if predicate is None:
            return list(self.memory["facts"].values())
        return [f for f in self.memory["facts"].values() if f["predicate"] == predicate]

    # === SOUVENIRS ===

    def remember(self, key, value, context=""):
        """mémorise quelque chose"""
        self.memory["souvenirs"].append({
            "key": key,
            "value": value,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        self._save_memory()
        return {'success': True}

    def recall(self, query):
        """rappelle des souvenirs"""
        query_lower = query.lower()
        results = []
        for s in self.memory["souvenirs"]:
            if query_lower in s["key"].lower() or query_lower in s["value"].lower():
                results.append(s)
        return results

    def forget(self, key):
        """oublie un souvenir"""
        before = len(self.memory["souvenirs"])
        self.memory["souvenirs"] = [s for s in self.memory["souvenirs"] if s["key"] != key]
        self._save_memory()
        return {'success': True, 'removed': before - len(self.memory["souvenirs"])}

    # === CONCEPTS ===

    def define_concept(self, name, definition):
        """définit un concept"""
        self.memory["concepts"][name] = {
            "definition": definition,
            "timestamp": datetime.now().isoformat()
        }
        self._save_memory()
        return {'success': True}

    def get_concept(self, name):
        """récupère un concept"""
        return self.memory["concepts"].get(name)

    def list_concepts(self):
        """liste tous les concepts"""
        return list(self.memory["concepts"].keys())

    # === SQL (CIPHER DB) ===

    def _get_sql_conn(self):
        """connexion SQL"""
        return psycopg2.connect(
            host="localhost", port=5432,
            database="ldb", user="lframework", password=""
        )

    def sql_query(self, query, params=None):
        """exécute une requête SQL en lecture"""
        # sécurité: seulement SELECT
        if not query.strip().upper().startswith("SELECT"):
            return {'error': 'only SELECT queries allowed'}
        try:
            conn = self._get_sql_conn()
            cur = conn.cursor()
            cur.execute(query, params or ())
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            conn.close()
            return {'success': True, 'rows': [dict(zip(cols, r)) for r in rows]}
        except Exception as e:
            return {'error': str(e)}

    def sql_tables(self):
        """liste les tables"""
        return self.sql_query("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")

    # === BACKUP ===

    def backup(self):
        """sauvegarde complète"""
        backup_path = os.path.join(ADN_PATH, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_path, 'w') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
        return {'success': True, 'path': backup_path}

    def stats(self):
        """statistiques"""
        return {
            'facts': len(self.memory["facts"]),
            'souvenirs': len(self.memory["souvenirs"]),
            'concepts': len(self.memory["concepts"])
        }

# instance globale
db = FlowDatabase()
