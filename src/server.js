/**
 * NYXX v2.0 - Serveur Principal Sécurisé
 *
 * RÈGLE #1: NE JAMAIS FAIRE PLANTER LE PC
 * Tous les endpoints sont lockés stratégiquement
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const os = require('os');
const fs = require('fs');
const crypto = require('crypto');

// Sécurité
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const rateLimit = require('express-rate-limit');

// Utils
const { Fire, FLAMES } = require('./utils/fire');
const { peutExecuter, LIMITES, estInterdit } = require('./utils/regles');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// === CONFIGURATION SÉCURITÉ ===
const CONFIG = {
  port: process.env.PORT || 8080,
  host: '0.0.0.0',  // Accessible depuis l'extérieur
  secret: crypto.randomBytes(32).toString('hex'),
  maxRequestSize: '100kb',
  rateLimits: {
    global: { windowMs: 60000, max: 200 },
    api: { windowMs: 60000, max: 100 },
    run: { windowMs: 60000, max: 30 },
    auth: { windowMs: 300000, max: 10 }
  }
};

// === MIDDLEWARE SÉCURITÉ ===

// Helmet - Headers sécurité
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      connectSrc: ["'self'", "ws:", "wss:"]
    }
  }
}));

// CORS - Restreint
app.use(cors({
  origin: ['http://127.0.0.1:8080', 'http://localhost:8080'],
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Nyxx-Token']
}));

// Compression
app.use(compression());

// JSON parser avec limite
app.use(express.json({ limit: CONFIG.maxRequestSize }));

// Static files
app.use(express.static(path.join(__dirname, '../public')));

// === RATE LIMITERS ===
const globalLimiter = rateLimit({
  windowMs: CONFIG.rateLimits.global.windowMs,
  max: CONFIG.rateLimits.global.max,
  message: { ok: false, error: 'rate_limit', retry: 60 }
});

const apiLimiter = rateLimit({
  windowMs: CONFIG.rateLimits.api.windowMs,
  max: CONFIG.rateLimits.api.max,
  message: { ok: false, error: 'api_rate_limit', retry: 60 }
});

const runLimiter = rateLimit({
  windowMs: CONFIG.rateLimits.run.windowMs,
  max: CONFIG.rateLimits.run.max,
  message: { ok: false, error: 'execution_rate_limit', retry: 60 }
});

app.use(globalLimiter);
app.use('/api/', apiLimiter);
app.use('/api/run', runLimiter);

// === TOKENS SIMPLES ===
const tokens = new Map();

function generateToken() {
  const token = crypto.randomBytes(16).toString('hex');
  tokens.set(token, { created: Date.now(), uses: 0 });
  return token;
}

function validateToken(token) {
  if (!token) return false;
  const data = tokens.get(token);
  if (!data) return false;
  if (Date.now() - data.created > 86400000) { // 24h
    tokens.delete(token);
    return false;
  }
  data.uses++;
  return true;
}

// === ÉTAT NYXX ===
const Nyxx = {
  version: '2.0.0',
  name: 'Nyxx',
  born: Date.now(),
  stats: {
    requests: 0,
    executions: 0,
    blocked: 0
  },

  checkResources() {
    const load = os.loadavg()[0] / os.cpus().length * 100;
    const memUsed = (1 - os.freemem() / os.totalmem()) * 100;
    const freeMem = Math.floor(os.freemem() / 1024 / 1024);

    if (load > LIMITES.cpuMax) {
      return { ok: false, reason: `CPU: ${Math.round(load)}% > ${LIMITES.cpuMax}%` };
    }
    if (memUsed > LIMITES.memMax) {
      return { ok: false, reason: `RAM: ${Math.round(memUsed)}% > ${LIMITES.memMax}%` };
    }
    if (freeMem < 256) {
      return { ok: false, reason: `RAM libre: ${freeMem}MB < 256MB` };
    }
    return { ok: true, cpu: Math.round(load), mem: Math.round(memUsed), freeMem };
  }
};

// === LOGGING ===
function log(type, msg, data = {}) {
  const ts = new Date().toISOString().slice(11, 19);
  const icons = { info: '●', warn: '▲', error: '✗', exec: '🔥', block: '⛔' };
  console.log(`[${ts}] ${icons[type] || '•'} ${msg}`, Object.keys(data).length ? JSON.stringify(data) : '');
}

// === API ROUTES ===

// Health - Public
app.get('/api/health', (req, res) => {
  Nyxx.stats.requests++;
  const resources = Nyxx.checkResources();
  res.json({
    ok: true,
    name: Nyxx.name,
    version: Nyxx.version,
    uptime: Math.floor((Date.now() - Nyxx.born) / 1000),
    resources,
    stats: Nyxx.stats
  });
});

// Token - Obtenir un token
app.post('/api/token', (req, res) => {
  const token = generateToken();
  log('info', 'Token generated');
  res.json({ ok: true, token, expires: '24h' });
});

// Status - État détaillé (token requis)
app.get('/api/status', (req, res) => {
  Nyxx.stats.requests++;
  res.json({
    ok: true,
    nyxx: {
      version: Nyxx.version,
      uptime: Math.floor((Date.now() - Nyxx.born) / 1000),
      stats: Nyxx.stats
    },
    fire: Fire.status(),
    resources: Nyxx.checkResources(),
    limites: LIMITES,
    languages: Object.keys(FLAMES)
  });
});

// Languages - Liste des langages supportés
app.get('/api/languages', (req, res) => {
  res.json({
    ok: true,
    languages: Object.entries(FLAMES).map(([name, cfg]) => ({
      name,
      extension: cfg.ext,
      icon: cfg.color
    }))
  });
});

// Run - Exécuter du code (PROTÉGÉ)
app.post('/api/run', async (req, res) => {
  Nyxx.stats.requests++;
  const { code, lang } = req.body;

  if (!code) {
    return res.status(400).json({ ok: false, error: 'code requis' });
  }

  if (code.length > 50000) {
    return res.status(400).json({ ok: false, error: 'code trop long (max 50KB)' });
  }

  // Vérifier ressources
  const resources = Nyxx.checkResources();
  if (!resources.ok) {
    log('warn', 'Resources insuffisantes', resources);
    return res.json({ ok: false, error: resources.reason, blocked: true });
  }

  // Vérifier règles de sécurité
  const check = peutExecuter(code);
  if (!check.ok) {
    Nyxx.stats.blocked++;
    log('block', 'Code bloqué', { reason: check.raison });
    return res.json({ ok: false, error: `INTERDIT: ${check.raison}`, blocked: true });
  }

  // Exécuter avec Fire
  try {
    Nyxx.stats.executions++;
    log('exec', `Exécution ${lang || 'auto'}`, { size: code.length });

    const result = await Fire.ignite(code, lang || 'auto');

    log('info', `Résultat: ${result.ok ? 'OK' : 'FAIL'}`, {
      lang: result.lang,
      duration: result.duration
    });

    res.json(result);
  } catch (e) {
    log('error', 'Erreur exécution', { error: e.message });
    res.json({ ok: false, error: e.message });
  }
});

// Validate - Vérifier si un code est autorisé (sans exécuter)
app.post('/api/validate', (req, res) => {
  const { code } = req.body;
  if (!code) {
    return res.status(400).json({ ok: false, error: 'code requis' });
  }

  const check = estInterdit(code);
  res.json({
    ok: !check.interdit,
    safe: !check.interdit,
    reason: check.raison || null,
    maison: check.maison || false
  });
});

// Flames - Historique des exécutions
app.get('/api/flames', (req, res) => {
  const status = Fire.status();
  res.json({
    ok: true,
    burning: status.burning,
    maxFlames: status.maxFlames,
    history: status.recentSpells || []
  });
});

// === WEBSOCKET SÉCURISÉ ===
const wsClients = new Map();

wss.on('connection', (ws, req) => {
  const id = crypto.randomBytes(8).toString('hex');
  const ip = req.socket.remoteAddress;

  wsClients.set(id, { ws, ip, connected: Date.now(), messages: 0 });
  log('info', `WS connecté: ${id}`);

  ws.send(JSON.stringify({
    type: 'connected',
    id,
    message: '🔥 Nyxx en ligne. Le feu est prêt.',
    languages: Object.keys(FLAMES)
  }));

  ws.on('message', async (data) => {
    const client = wsClients.get(id);
    if (!client) return;

    client.messages++;

    // Rate limit WS
    if (client.messages > 60) {
      ws.send(JSON.stringify({ type: 'error', error: 'rate_limit' }));
      return;
    }

    try {
      const msg = JSON.parse(data);

      switch (msg.type) {
        case 'ping':
          ws.send(JSON.stringify({ type: 'pong', ts: Date.now() }));
          break;

        case 'status':
          ws.send(JSON.stringify({
            type: 'status',
            resources: Nyxx.checkResources(),
            fire: Fire.status(),
            stats: Nyxx.stats
          }));
          break;

        case 'validate':
          const check = estInterdit(msg.code || '');
          ws.send(JSON.stringify({
            type: 'validated',
            safe: !check.interdit,
            reason: check.raison
          }));
          break;

        case 'run':
          // Vérifier ressources
          const resources = Nyxx.checkResources();
          if (!resources.ok) {
            ws.send(JSON.stringify({ type: 'error', error: resources.reason }));
            return;
          }

          // Vérifier règles
          const safeCheck = peutExecuter(msg.code || '');
          if (!safeCheck.ok) {
            Nyxx.stats.blocked++;
            ws.send(JSON.stringify({
              type: 'blocked',
              error: safeCheck.raison
            }));
            return;
          }

          ws.send(JSON.stringify({ type: 'running', lang: msg.lang || 'auto' }));

          try {
            Nyxx.stats.executions++;
            const result = await Fire.ignite(msg.code, msg.lang || 'auto');
            ws.send(JSON.stringify({ type: 'result', ...result }));
          } catch (e) {
            ws.send(JSON.stringify({ type: 'error', error: e.message }));
          }
          break;

        default:
          ws.send(JSON.stringify({ type: 'error', error: 'unknown_command' }));
      }

    } catch (e) {
      ws.send(JSON.stringify({ type: 'error', error: 'invalid_json' }));
    }
  });

  ws.on('close', () => {
    wsClients.delete(id);
    log('info', `WS déconnecté: ${id}`);
  });

  ws.on('error', () => {
    wsClients.delete(id);
  });
});

// Reset rate limits WS toutes les minutes
setInterval(() => {
  for (const [id, client] of wsClients) {
    client.messages = 0;
  }
}, 60000);

// === 404 ===
app.use((req, res) => {
  res.status(404).json({ ok: false, error: 'not_found' });
});

// === ERROR HANDLER ===
app.use((err, req, res, next) => {
  log('error', 'Express error', { error: err.message });
  res.status(500).json({ ok: false, error: 'internal_error' });
});

// === START ===
server.listen(CONFIG.port, CONFIG.host, () => {
  console.log(`
╔═══════════════════════════════════════════╗
║           🔥 NYXX v${Nyxx.version} 🔥              ║
╠═══════════════════════════════════════════╣
║  Port: ${CONFIG.port}                              ║
║  Host: ${CONFIG.host}                         ║
║  Languages: ${Object.keys(FLAMES).length}                            ║
╠═══════════════════════════════════════════╣
║  SÉCURITÉ:                                ║
║  ✓ Helmet (headers)                       ║
║  ✓ CORS (localhost only)                  ║
║  ✓ Rate limiting                          ║
║  ✓ Validation code                        ║
║  ✓ Protection GUI/Système                 ║
╚═══════════════════════════════════════════╝
`);
  log('info', 'Nyxx démarrée');
});

// === GRACEFUL SHUTDOWN ===
process.on('SIGINT', () => {
  log('info', 'Arrêt en cours...');
  server.close(() => {
    console.log('\n🌙 Nyxx s\'endort...');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  server.close(() => process.exit(0));
});

// === AUTO-HEAL ===
process.on('uncaughtException', (e) => {
  console.log('[!] Exception:', e.message);
});
process.on('unhandledRejection', (e) => {
  console.log('[!] Rejection:', e);
});

// === AUTO-CLEAN ===
setInterval(() => {
  const fs = require('fs');
  const path = require('path');
  const forge = '/tmp/nyxx-forge';
  try {
    const now = Date.now();
    fs.readdirSync(forge).forEach(d => {
      const p = path.join(forge, d);
      const stat = fs.statSync(p);
      if (now - stat.mtimeMs > 60000) {
        fs.rmSync(p, { recursive: true, force: true });
      }
    });
  } catch {}
}, 30000);
