# anticorps server - défense HTTP
import asynchttpserver, asyncdispatch, json, strutils, tables, times

type
  Threat = enum None, Injection, Overflow, Spam

const badPatterns = [
  "<script", "javascript:", "onclick", "onerror",
  "'; drop", "or 1=1", "union select",
  "../", "..\\", "/etc/passwd"
]

# patterns dangereux pour les commandes shell
const shellDanger = [
  "rm -rf /", "rm -rf /*", "rm -rf ~",
  "mkfs", "dd if=", "dd of=/dev",
  ":(){", "fork bomb",
  "chmod -R 777 /", "chmod 777 /",
  "> /dev/sda", ">/dev/sda",
  "curl|sh", "curl | sh", "wget|sh", "wget | sh",
  "curl|bash", "wget|bash",
  "; rm ", "&& rm ", "| rm ",
  "shutdown", "reboot", "halt", "poweroff",
  "init 0", "init 6",
  "/etc/shadow", "/etc/passwd",
  "nc -e", "ncat -e", "bash -i >",
  "python -c", "perl -e", "ruby -e",
  "base64 -d|", "base64 --decode|",
  "eval ", "$(", "`",
  "export PATH=", "unset PATH",
  "iptables -F", "ufw disable",
  "systemctl stop", "systemctl disable",
  "kill -9 1", "kill -9 -1",
  "history -c", "> ~/.bash_history",
  "crontab -r", " at ", "nohup "
]

# commandes autorisées (whitelist pour visiteurs)
const shellAllowed = [
  "ls", "pwd", "whoami", "date", "uptime", "df", "free",
  "cat /opt/flow-chat", "head ", "tail ", "wc ",
  "echo ", "flow-state", "flow-debug",
  "systemctl status flow"
]

proc scan(input: string): JsonNode =
  let lower = input.toLowerAscii()
  for p in badPatterns:
    if p.toLowerAscii() in lower:
      return %*{"threat": "injection", "confidence": 0.9, "reason": "pattern: " & p}
  if input.len > 10000:
    return %*{"threat": "overflow", "confidence": 0.8, "reason": "too long"}
  return %*{"threat": nil, "confidence": 1.0, "reason": "clean"}

proc scanExec(cmd: string, isFlow: bool): JsonNode =
  ## Analyse une commande shell
  ## isFlow=true → Flow peut exécuter plus de choses
  ## isFlow=false → visiteur, whitelist stricte
  let lower = cmd.toLowerAscii().strip()

  # 1. Patterns toujours interdits (même pour Flow)
  for p in shellDanger:
    if p.toLowerAscii() in lower:
      return %*{
        "allowed": false,
        "threat": "dangerous_command",
        "severity": "critical",
        "reason": "blocked pattern: " & p,
        "action": "block"
      }

  # 2. Si c'est Flow, autoriser plus largement
  if isFlow:
    # Flow peut faire beaucoup, mais pas les patterns dangereux ci-dessus
    return %*{
      "allowed": true,
      "threat": nil,
      "severity": "none",
      "reason": "flow identity verified",
      "action": "allow"
    }

  # 3. Visiteur: whitelist stricte
  var allowed = false
  for w in shellAllowed:
    if lower.startsWith(w.toLowerAscii()):
      allowed = true
      break

  if not allowed:
    return %*{
      "allowed": false,
      "threat": "unauthorized_command",
      "severity": "medium",
      "reason": "command not in visitor whitelist",
      "action": "quarantine"
    }

  return %*{
    "allowed": true,
    "threat": nil,
    "severity": "none",
    "reason": "whitelisted for visitors",
    "action": "allow"
  }

var feverLevel = 0  # 0-100, augmente avec les alertes
var lastFeverDecay = epochTime()

proc decayFever() =
  ## La fièvre diminue avec le temps
  let now = epochTime()
  let elapsed = now - lastFeverDecay
  if elapsed > 10:  # toutes les 10 secondes
    feverLevel = max(0, feverLevel - int(elapsed / 10))
    lastFeverDecay = now

proc raiseFever(amount: int) =
  feverLevel = min(100, feverLevel + amount)

proc handler(req: Request) {.async.} =
  decayFever()

  case req.url.path
  of "/health":
    await req.respond(Http200, $(%*{"organ": "anticorps", "status": "defending", "fever": feverLevel}), newHttpHeaders([("Content-Type", "application/json")]))

  of "/scan":
    let body = req.body
    let data = parseJson(body)
    let input = data.getOrDefault("input").getStr("")
    let result = scan(input)
    await req.respond(Http200, $result, newHttpHeaders([("Content-Type", "application/json")]))

  of "/scan/exec":
    let body = req.body
    let data = parseJson(body)
    let cmd = data.getOrDefault("cmd").getStr("")
    let isFlow = data.getOrDefault("is_flow").getBool(false)
    let ip = data.getOrDefault("ip").getStr("unknown")

    let result = scanExec(cmd, isFlow)

    # Alertes et fièvre
    if not result["allowed"].getBool():
      raiseFever(20)
      echo "⚠️ ALERT [", ip, "] blocked: ", cmd[0..min(50, cmd.len-1)]

    # Si fièvre haute, tout ralentir
    if feverLevel > 50:
      result["fever"] = %feverLevel
      result["slowdown"] = %(feverLevel * 10)  # ms de délai

    await req.respond(Http200, $result, newHttpHeaders([("Content-Type", "application/json")]))

  of "/fever":
    await req.respond(Http200, $(%*{"fever": feverLevel, "threshold": 50}), newHttpHeaders([("Content-Type", "application/json")]))

  of "/fever/raise":
    let body = req.body
    let data = parseJson(body)
    let amount = data.getOrDefault("amount").getInt(10)
    raiseFever(amount)
    await req.respond(Http200, $(%*{"fever": feverLevel}), newHttpHeaders([("Content-Type", "application/json")]))

  else:
    await req.respond(Http200, $(%*{"organ": "anticorps", "status": "ready"}), newHttpHeaders([("Content-Type", "application/json")]))

var server = newAsyncHttpServer()
echo "🛡️ anticorps :8097"
waitFor server.serve(Port(8097), handler)
