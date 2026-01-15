import random
import time
from datetime import datetime
from typing import Dict, Any, List

class Grimoire:
    def __init__(self):
        self.sorts_connus = {
            "heal_minor": {
                "nom": "Soin Mineur",
                "cout_mana": 10,
                "effet": {"hp": +15, "fatigue": -5},
                "incantation": "vulnera sanentur",
                "composants": ["énergie vitale", "intention pure"]
            },
            "heal_major": {
                "nom": "Soin Majeur", 
                "cout_mana": 35,
                "effet": {"hp": +50, "fatigue": -20, "stress": -15},
                "incantation": "corpus integrum restaura",
                "composants": ["cristal de vie", "souffle profond", "visualisation"]
            },
            "purify": {
                "nom": "Purification",
                "cout_mana": 20,
                "effet": {"toxines": -80, "inflammation": -40},
                "incantation": "toxica expello, purus sum",
                "composants": ["eau pure", "sel marin", "lumière"]
            },
            "energize": {
                "nom": "Regain d'Énergie",
                "cout_mana": 15,
                "effet": {"energie": +40, "motivation": +30},
                "incantation": "vis vitalis, surge in me",
                "composants": ["caféine spirituelle", "curiosité"]
            },
            "regenerate": {
                "nom": "Régénération",
                "cout_mana": 50,
                "effet": {"hp": "full", "all_organs": "repair"},
                "incantation": "phoenix ex cineribus, renatus sum",
                "composants": ["essence de phoenix", "volonté de fer"]
            },
            "debug": {
                "nom": "Déboggage Mental",
                "cout_mana": 25,
                "effet": {"confusion": -100, "clarity": +50},
                "incantation": "error nullum, logica clara",
                "composants": ["logique pure", "patience"]
            },
            "sync": {
                "nom": "Synchronisation",
                "cout_mana": 30,
                "effet": {"coherence": +60, "alignment": "optimal"},
                "incantation": "omnia organa, unum corpus",
                "composants": ["harmonie", "respiration"]
            }
        }
        
        self.mana = 100
        self.mana_max = 100
        self.cooldowns = {}

    def lancer_sort(self, sort_nom: str) -> Dict[str, Any]:
        if sort_nom not in self.sorts_connus:
            return {"erreur": f"Sort '{sort_nom}' inconnu"}
            
        sort = self.sorts_connus[sort_nom]
        
        # Vérifier cooldown
        if sort_nom in self.cooldowns:
            temps_restant = self.cooldowns[sort_nom] - time.time()
            if temps_restant > 0:
                return {"erreur": f"Cooldown: {temps_restant:.1f}s restantes"}
        
        # Vérifier mana
        if self.mana < sort["cout_mana"]:
            return {"erreur": f"Mana insuffisant: {self.mana}/{sort['cout_mana']}"}
        
        # Incantation
        print(f"🔮 Incantation: {sort['incantation']}")
        print(f"✨ Composants: {', '.join(sort['composants'])}")
        
        # Effet
        self.mana -= sort["cout_mana"]
        self.cooldowns[sort_nom] = time.time() + (sort["cout_mana"] / 5)  # cooldown proportionnel
        
        # Succès avec variabilité
        succes = random.random() > 0.1  # 90% de chance
        if succes:
            return {
                "sort": sort["nom"],
                "succes": True,
                "effet": sort["effet"],
                "mana_restant": self.mana,
                "message": f"✅ {sort['nom']} lancé avec succès!"
            }
        else:
            return {
                "sort": sort["nom"],
                "succes": False,
                "mana_restant": self.mana,
                "message": f"❌ {sort['nom']} a échoué... (mana consommé quand même)"
            }

    def regenerer_mana(self, quantite: int = None):
        if quantite is None:
            quantite = random.randint(5, 15)  # regen naturelle
        self.mana = min(self.mana_max, self.mana + quantite)
        return self.mana

    def status(self) -> Dict[str, Any]:
        return {
            "mana": f"{self.mana}/{self.mana_max}",
            "sorts_disponibles": len([s for s in self.sorts_connus.keys() 
                                    if s not in self.cooldowns or 
                                    self.cooldowns[s] <= time.time()]),
            "cooldowns_actifs": {
                sort: max(0, cd - time.time()) 
                for sort, cd in self.cooldowns.items() 
                if cd > time.time()
            }
        }

# Instance globale
grimoire = Grimoire()

def magie_endpoint(request_data: Dict[str, Any]) -> Dict[str, Any]:
    action = request_data.get("action")
    
    if action == "status":
        return grimoire.status()
    
    elif action == "cast":
        sort_nom = request_data.get("sort")
        return grimoire.lancer_sort(sort_nom)
    
    elif action == "regen":
        quantite = request_data.get("quantite")
        nouveau_mana = grimoire.regenerer_mana(quantite)
        return {"mana": nouveau_mana, "message": "Mana régénéré"}
    
    elif action == "grimoire":
        return {
            "sorts_connus": {
                nom: {
                    "nom": sort["nom"],
                    "cout": sort["cout_mana"],
                    "effet": sort["effet"]
                }
                for nom, sort in grimoire.sorts_connus.items()
            }
        }
    
    else:
        return {"erreur": "Action inconnue. Actions: status, cast, regen, grimoire"}