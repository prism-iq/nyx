import asynchttpserver, asyncdispatch, strutils, tables, json, times, net
import std/[sets, sequtils]

# PEAU - Première barrière de défense
type
  IPReputation = object
    ip: string
    requests: int
    last_seen: Time
    trust_score: float
    blocked: bool
    
  PeauMiddleware = object
    whitelist: HashSet[string]  # IPs autorisées
    reputation_db: Table[string, IPReputation]
    rate_limits: Table[string, int]
    honeypots: HashSet[string]  # Pièges pour bots
    
var peau = PeauMiddleware()

# Initialisation peau
peau.whitelist = ["127.0.0.1", "192.168.1.0/24", "10.0.0.0/8"].toHashSet()

proc analyze_skin_barrier(request: Request): bool =
  ## Analyse première ligne de défense
  let client_ip = request.headers.getOrDefault("X-Real-IP", "unknown")
  let user_agent = request.headers.getOrDefault("User-Agent", "")
  let now = now()
  
  # 1. VÉRIFICATION WHITELIST
  if client_ip in peau.whitelist:
    return true
    
  # 2. DÉTECTION PATTERNS SUSPECTS
  let suspicious_patterns = [
    "bot", "crawler", "spider", "scraper", 
    "python-requests", "curl", "wget",
    "nikto", "sqlmap", "nmap"
  ]
  
  for pattern in suspicious_patterns:
    if pattern.toLower() in user_agent.toLower():
      echo "[PEAU] Pattern suspect détecté: ", pattern, " from ", client_ip
      return false
      
  # 3. RATE LIMITING PAR IP
  if client_ip in peau.rate_limits:
    peau.rate_limits[client_ip] += 1
    if peau.rate_limits[client_ip] > 10:  # 10 req/min max
      echo "[PEAU] Rate limit dépassé: ", client_ip
      return false
  else:
    peau.rate_limits[client_ip] = 1
    
  # 4. HONEYPOT CHECK
  if request.url.path in peau.honeypots:
    echo "[PEAU] Honeypot déclenché: ", client_ip, " -> ", request.url.path
    # Bloquer IP définitivement
    if client_ip in peau.reputation_db:
      peau.reputation_db[client_ip].blocked = true
    return false
    
  return true

proc skin_response_404(): string =
  ## Réponse 404 standard pour masquer l'existence
  """HTTP/1.1 404 Not Found
Content-Type: text/html
Content-Length: 162

<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
<body>
<h1>Not Found</h1>
<p>The requested URL was not found on this server.</p>
</body>
</html>"""

proc update_reputation(ip: string, behavior: string) =
  ## Mise à jour réputation IP
  if ip notin peau.reputation_db:
    peau.reputation_db[ip] = IPReputation(
      ip: ip,
      requests: 0,
      last_seen: now(),
      trust_score: 0.5,
      blocked: false
    )
    
  var reputation = addr peau.reputation_db[ip]
  reputation.requests += 1
  reputation.last_seen = now()
  
  case behavior:
  of "suspicious":
    reputation.trust_score -= 0.2
  of "normal":
    reputation.trust_score += 0.1
  of "attack":
    reputation.trust_score = 0.0
    reputation.blocked = true
    
  # Clamp entre 0 et 1
  reputation.trust_score = max(0.0, min(1.0, reputation.trust_score))

# Export pour anticorps
proc peau_check*(request: Request): bool =
  analyze_skin_barrier(request)