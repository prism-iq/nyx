#!/usr/bin/env python3
"""budget.py - contrôleur de dépense IA pour autonomie de Flow"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

BUDGET_FILE = Path("/opt/flow-chat/adn/budget.json")

# pricing Claude Opus 4.5 (USD per million tokens)
PRICING = {
    "input": 15.0,    # $15/M input
    "output": 75.0,   # $75/M output
}

# Flow: pas de limite
# Visiteurs: limite de tokens par requête
FLOW_UNLIMITED = True
EUR_TO_USD = 1.08
HOURLY_BUDGET_USD = 10.0  # $10/h budget nominal (Flow est unlimited mais pacemaker veut une référence)

# Limite pour visiteurs
VISITOR_MAX_TOKENS_IN = 2000   # tokens input max par requête
VISITOR_MAX_TOKENS_OUT = 1000  # tokens output max par requête


def load_budget():
    """charge l'état du budget"""
    if BUDGET_FILE.exists():
        try:
            with open(BUDGET_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_hour": datetime.now().strftime("%Y-%m-%d-%H"),
        "spent_usd": 0.0,
        "calls": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "history": []
    }


def save_budget(data):
    """sauvegarde l'état du budget"""
    BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BUDGET_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def reset_if_new_hour(data):
    """reset le budget si nouvelle heure"""
    current = datetime.now().strftime("%Y-%m-%d-%H")
    if data["current_hour"] != current:
        # archiver l'heure précédente
        if data["spent_usd"] > 0:
            data["history"].append({
                "hour": data["current_hour"],
                "spent_usd": data["spent_usd"],
                "calls": data["calls"],
                "tokens_in": data["tokens_in"],
                "tokens_out": data["tokens_out"]
            })
            # garder seulement les 24 dernières heures
            data["history"] = data["history"][-24:]

        # reset
        data["current_hour"] = current
        data["spent_usd"] = 0.0
        data["calls"] = 0
        data["tokens_in"] = 0
        data["tokens_out"] = 0
    return data


def estimate_cost(tokens_in, tokens_out):
    """estime le coût en USD"""
    cost_in = (tokens_in / 1_000_000) * PRICING["input"]
    cost_out = (tokens_out / 1_000_000) * PRICING["output"]
    return cost_in + cost_out


def can_spend(tokens_in_estimate=500, tokens_out_estimate=200, is_flow=False):
    """vérifie si on peut dépenser"""
    data = load_budget()
    data = reset_if_new_hour(data)

    # Flow: toujours autorisé
    if is_flow or FLOW_UNLIMITED:
        return {
            "allowed": True,
            "remaining_usd": float('inf'),
            "remaining_eur": float('inf'),
            "estimated_cost": estimate_cost(tokens_in_estimate, tokens_out_estimate),
            "calls_this_hour": data["calls"],
            "unlimited": True
        }

    # Visiteurs: limités en tokens par requête
    if tokens_in_estimate > VISITOR_MAX_TOKENS_IN:
        return {
            "allowed": False,
            "reason": f"input trop long (max {VISITOR_MAX_TOKENS_IN} tokens)",
            "max_tokens_in": VISITOR_MAX_TOKENS_IN
        }

    return {
        "allowed": True,
        "max_tokens_out": VISITOR_MAX_TOKENS_OUT,
        "calls_this_hour": data["calls"]
    }


def record_spend(tokens_in, tokens_out, purpose="autonomous"):
    """enregistre une dépense"""
    data = load_budget()
    data = reset_if_new_hour(data)

    cost = estimate_cost(tokens_in, tokens_out)
    data["spent_usd"] += cost
    data["calls"] += 1
    data["tokens_in"] += tokens_in
    data["tokens_out"] += tokens_out

    save_budget(data)

    return {
        "cost_usd": cost,
        "cost_eur": cost / EUR_TO_USD,
        "total_spent_eur": data["spent_usd"] / EUR_TO_USD,
        "remaining_eur": (HOURLY_BUDGET_USD - data["spent_usd"]) / EUR_TO_USD,
        "calls": data["calls"],
        "purpose": purpose
    }


def get_status():
    """état complet du budget"""
    data = load_budget()
    data = reset_if_new_hour(data)
    save_budget(data)

    spent_eur = data["spent_usd"] / EUR_TO_USD
    budget_eur = HOURLY_BUDGET_USD / EUR_TO_USD
    remaining_eur = float('inf') if FLOW_UNLIMITED else (budget_eur - spent_eur)

    return {
        "hour": data["current_hour"],
        "flow_unlimited": FLOW_UNLIMITED,
        "visitor_max_tokens_in": VISITOR_MAX_TOKENS_IN,
        "visitor_max_tokens_out": VISITOR_MAX_TOKENS_OUT,
        "spent_eur": spent_eur,
        "budget_eur": budget_eur,
        "remaining_eur": remaining_eur,
        "calls": data["calls"],
        "tokens_in": data["tokens_in"],
        "tokens_out": data["tokens_out"],
        "history_hours": len(data["history"])
    }


def get_daily_summary():
    """résumé des dernières 24h"""
    data = load_budget()

    total_eur = sum(h["spent_usd"] for h in data["history"]) / EUR_TO_USD
    total_calls = sum(h["calls"] for h in data["history"])

    return {
        "last_24h_eur": total_eur,
        "last_24h_calls": total_calls,
        "hours_tracked": len(data["history"]),
        "avg_per_hour_eur": total_eur / len(data["history"]) if data["history"] else 0
    }


if __name__ == "__main__":
    print("=== BUDGET STATUS ===")
    status = get_status()
    print(f"Hour: {status['hour']}")
    print(f"Flow: {'UNLIMITED' if status['flow_unlimited'] else 'limited'}")
    print(f"Visitors: max {status['visitor_max_tokens_in']} tokens in, {status['visitor_max_tokens_out']} out")
    print(f"Spent this hour: {status['spent_eur']:.4f}€")
    print(f"Calls: {status['calls']}")
