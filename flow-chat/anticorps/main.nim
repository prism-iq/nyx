# anticorps.nim - défense, validation, paranoia
import strutils, tables, times

type
  Threat = enum
    None, Injection, Overflow, Spam, Malformed

  Scan = object
    threat: Threat
    confidence: float
    reason: string

# patterns dangereux
const badPatterns = [
  "<script", "javascript:", "onclick", "onerror",  # XSS
  "'; DROP", "OR 1=1", "UNION SELECT",              # SQL injection
  "../", "..\\", "/etc/passwd"                       # path traversal
]

proc scan*(input: string): Scan =
  let lower = input.toLowerAscii()

  # check patterns
  for p in badPatterns:
    if p.toLowerAscii() in lower:
      return Scan(threat: Injection, confidence: 0.9, reason: "pattern: " & p)

  # check length
  if input.len > 10000:
    return Scan(threat: Overflow, confidence: 0.8, reason: "too long")

  # check spam (répétition)
  if input.len > 100:
    let words = input.split()
    var counts = initTable[string, int]()
    for w in words:
      counts[w] = counts.getOrDefault(w) + 1
    for w, c in counts:
      if c > input.len div 10:
        return Scan(threat: Spam, confidence: 0.7, reason: "repetition: " & w)

  return Scan(threat: None, confidence: 1.0, reason: "clean")

proc isSafe*(input: string): bool =
  scan(input).threat == None

when isMainModule:
  echo "🛡️ anticorps ready"
