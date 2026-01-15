#!/usr/bin/env python3
"""anticorps.py - défense, validation (port du Nim)"""

BAD_PATTERNS = [
    "<script", "javascript:", "onclick", "onerror",  # XSS
    "'; drop", "or 1=1", "union select",             # SQL injection
    "../", "..\\", "/etc/passwd"                      # path traversal
]

def scan(input_str):
    """Scan input for threats"""
    lower = input_str.lower()

    # check patterns
    for p in BAD_PATTERNS:
        if p.lower() in lower:
            return {"threat": "injection", "confidence": 0.9, "reason": f"pattern: {p}"}

    # check length
    if len(input_str) > 10000:
        return {"threat": "overflow", "confidence": 0.8, "reason": "too long"}

    # check spam (repetition)
    if len(input_str) > 100:
        words = input_str.split()
        counts = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1
        for w, c in counts.items():
            if c > len(input_str) // 10:
                return {"threat": "spam", "confidence": 0.7, "reason": f"repetition: {w}"}

    return {"threat": None, "confidence": 1.0, "reason": "clean"}

def is_safe(input_str):
    return scan(input_str)["threat"] is None

if __name__ == "__main__":
    print("🛡️ anticorps ready")
