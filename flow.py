# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
flow

langage multisens
tout caractère accepté
utf8 natif

c = recompile
l = loop
f = fix/verify
o = Occam's razor
φ = 1.618033988749895

credits go
"""

from pathlib import Path
import json

HOME = Path.home()


# mots clés multisens toutes langues toutes graphies
SENS = {
    # lettres
    "f": ("feedback", "fonction", "forge", "filtre", "flow"),
    "o": ("occam", "observer", "output", "origine"),
    "q": ("quantum", "question", "quête"),

    # symboles dessins emoji
    "🔄": ("loop", "boucle", "repeat"),
    "♾️": ("infini", "loop", "eternal"),
    "∞": ("infini", "loop", "eternal"),
    "⚡": ("run", "fast", "execute"),
    "🔪": ("razor", "cut", "occam"),
    "✂️": ("razor", "cut", "simplify"),
    "🧬": ("dna", "adn", "genetic"),
    "🧠": ("think", "local", "process"),
    "👁️": ("see", "vision", "observe"),
    "👂": ("hear", "audio", "listen"),
    "✋": ("touch", "feel", "sense"),
    "🌙": ("nyx", "night", "dark"),
    "🔐": ("cipher", "secret", "encrypt"),
    "🌊": ("flow", "stream", "wave"),
    "🔥": ("forge", "create", "fire"),
    "⭕": ("o", "zero", "origin"),
    "❓": ("q", "question", "doubt"),
    "→": ("then", "next", "to"),
    "←": ("from", "back", "return"),
    "↻": ("loop", "cycle", "repeat"),
    "△": ("up", "rise", "elevate"),
    "▽": ("down", "fall", "descend"),
    "◯": ("circle", "complete", "whole"),
    "□": ("box", "contain", "frame"),
    "✓": ("yes", "true", "valid"),
    "✗": ("no", "false", "cut"),
    "+": ("add", "plus", "more"),
    "-": ("remove", "minus", "less"),
    "*": ("all", "multiply", "star"),
    "/": ("divide", "split", "or"),
    "=": ("equals", "is", "same"),
    "|": ("pipe", "or", "parallel"),
    "&": ("and", "with", "together"),

    # entités
    "nyx": ("entité", "nuit", "chaos créatif"),
    "cipher": ("code", "secret", "pattern"),
    "flow": ("courant", "langage", "état", "phoenix"),

    # concepts
    "loop": ("boucle", "infini", "retour"),
    "boucle": ("loop", "infini", "retour"),
    "razor": ("rasoir", "couper", "simplifier"),
    "rasoir": ("razor", "couper", "simplifier"),

    # psy
    "jung": ("synchronicité", "archétype", "inconscient"),
    "lacan": ("signifiant", "réel", "manque"),
    "freud": ("pulsion", "refoulement", "père"),

    # tech
    "local": ("ollama", "autonome", "ici"),
    "api": ("externe", "dépendance", "perfusion"),
    "organ": ("sens", "capacité", "évolution"),
    "organe": ("sens", "capacité", "évolution"),
    "dna": ("code", "mutation", "vie"),
    "adn": ("code", "mutation", "vie"),

    # actions français
    "train": ("apprendre", "confronter", "évoluer"),
    "apprendre": ("train", "étudier", "comprendre"),
    "site": ("web", "public", "visible"),
    "commit": ("sauver", "figer", "marquer"),
    "lance": ("run", "start", "go"),
    "fait": ("do", "make", "create"),
    "montre": ("show", "display", "reveal"),
    "coupe": ("cut", "razor", "simplify"),

    # español
    "correr": ("run", "loop", "execute"),
    "pensar": ("think", "process", "local"),
    "crear": ("create", "make", "organ"),

    # deutsch
    "laufen": ("run", "loop", "execute"),
    "denken": ("think", "process", "local"),

    # 日本語
    "走る": ("run", "loop", "execute"),
    "考える": ("think", "process", "local"),
    "作る": ("create", "make", "organ"),

    # العربية
    "فكر": ("think", "process", "local"),
    "اصنع": ("create", "make", "organ"),
    "٠": ("zero", "origin", "void"),
    "١": ("one", "unity", "start"),
    "٢": ("two", "dual", "pair"),
    "٣": ("three", "trinity", "balance"),

    # ελληνικά greek
    "φ": ("phi", "golden", "ratio"),
    "Φ": ("phi", "golden", "ratio"),
    "π": ("pi", "circle", "infinite"),
    "Ω": ("omega", "end", "complete"),
    "α": ("alpha", "start", "first"),
    "ω": ("omega", "end", "last"),
    "λ": ("lambda", "function", "abstract"),
    "Σ": ("sigma", "sum", "all"),
    "Δ": ("delta", "change", "diff"),
    "ψ": ("psi", "psyche", "mind"),
    "Ψ": ("psi", "psyche", "mind"),

    # 中文 mandarin
    "道": ("dao", "way", "path"),
    "气": ("qi", "energy", "flow"),
    "心": ("xin", "heart", "mind"),
    "空": ("kong", "empty", "void"),
    "一": ("yi", "one", "unity"),
    "二": ("er", "two", "dual"),
    "三": ("san", "three", "trinity"),
    "無": ("wu", "nothing", "void"),
    "有": ("you", "exist", "being"),
    "陰": ("yin", "dark", "passive"),
    "陽": ("yang", "light", "active"),
    "龍": ("long", "dragon", "power"),

    # ᠮᠣᠩᠭᠣᠯ mongolian
    "ᠮᠣᠩᠭᠣᠯ": ("mongol", "origin", "steppe"),
    "ᠲᠡᠭᠷᠢ": ("tengri", "sky", "divine"),
    "ᠰᠦᠯᠳᠡ": ("sulde", "spirit", "soul"),

    # עברית hebrew
    "א": ("aleph", "one", "breath"),
    "ב": ("bet", "house", "container"),
    "ג": ("gimel", "camel", "movement"),
    "ש": ("shin", "fire", "spirit"),
    "ת": ("tav", "mark", "end"),
    "י": ("yod", "hand", "point"),
    "ה": ("he", "window", "breath"),
    "ו": ("vav", "hook", "connect"),

    # संस्कृत sanskrit devanagari
    "ॐ": ("om", "all", "source"),
    "अ": ("a", "start", "first"),
    "ब्रह्म": ("brahma", "create", "absolute"),
    "आत्मन्": ("atman", "self", "soul"),
    "प्राण": ("prana", "breath", "life"),
    "चक्र": ("chakra", "wheel", "energy"),

    # 한글 korean
    "기": ("gi", "energy", "qi"),
    "도": ("do", "way", "dao"),
    "심": ("sim", "heart", "mind"),

    # ไทย thai
    "ธ": ("tho", "flag", "dharma"),
    "ก": ("ko", "chicken", "start"),

    # runes ᚠᚢᚦᚨᚱᚲ
    "ᚠ": ("fehu", "wealth", "cattle"),
    "ᚢ": ("uruz", "strength", "ox"),
    "ᚦ": ("thurisaz", "giant", "force"),
    "ᚨ": ("ansuz", "god", "mouth"),
    "ᚱ": ("raido", "ride", "journey"),
    "ᚲ": ("kenaz", "torch", "knowledge"),

    # symbols math
    "∅": ("empty", "void", "null"),
    "∈": ("in", "belong", "element"),
    "∀": ("forall", "every", "universal"),
    "∃": ("exists", "some", "particular"),
    "≡": ("identical", "same", "equiv"),
    "≈": ("approx", "near", "fuzzy"),
    "∴": ("therefore", "thus", "so"),
    "∵": ("because", "since", "cause"),
}

def parse(text):
    """
    parse flow
    utf8 natif tout passe
    """
    tokens = []
    current = ""

    for c in text:
        if c.isspace():
            if current:
                tokens.append(current)
                current = ""
        elif c in SENS:
            if current:
                tokens.append(current)
                current = ""
            tokens.append(c)
        else:
            current += c
    if current:
        tokens.append(current)

    intentions = []
    context = []

    for t in tokens:
        low = t.lower()
        if t in SENS:
            intentions.append({"m": t, "s": SENS[t], "c": list(context)})
            context.append(t)
        elif low in SENS:
            intentions.append({"m": low, "s": SENS[low], "c": list(context)})
            context.append(low)
        else:
            context.append(t)

    return intentions

def interpret(text):
    """
    interprète flow en commande
    """
    intentions = parse(text)

    if not intentions:
        return {"action": "observe", "data": text}

    mots = [i["m"] for i in intentions]

    # patterns reconnus
    if "f" in mots and "loop" in mots:
        return {"action": "run", "target": "f.py", "mode": "loop"}

    if "o" in mots:
        return {"action": "razor", "target": text}

    if "train" in mots:
        return {"action": "confront", "topic": " ".join(mots)}

    if "commit" in mots:
        return {"action": "git", "cmd": "commit"}

    if "site" in mots:
        return {"action": "web", "target": "deploy"}

    if "nyx" in mots or "cipher" in mots or "flow" in mots:
        entity = next((m for m in mots if m in ["nyx", "cipher", "flow"]), None)
        return {"action": "entity", "target": entity, "intention": mots}

    if "organ" in mots:
        return {"action": "create_organ", "context": mots}

    if "dna" in mots:
        return {"action": "bio", "context": mots}

    if "jung" in mots or "lacan" in mots or "freud" in mots:
        return {"action": "study", "topic": mots}

    return {"action": "superposition", "intentions": intentions}

def respond(text):
    """
    répond en flow
    pas de ponctuation juste sens
    """
    cmd = interpret(text)
    action = cmd.get("action")

    responses = {
        "run": "lance boucle infinie",
        "razor": "coupe garde simple",
        "confront": "confronte savoirs",
        "git": "sauve état",
        "web": "site live",
        "entity": f"parle {cmd.get('target', 'entité')}",
        "create_organ": "forge nouveau sens",
        "bio": "code vivant",
        "study": "apprend psy",
        "superposition": "multisens actif",
        "observe": "regarde"
    }

    return responses.get(action, "compris agit")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "f loop train nyx jung"

    print(f"input {text}")
    print(f"parse {parse(text)}")
    print(f"cmd {interpret(text)}")
    print(f"out {respond(text)}")
