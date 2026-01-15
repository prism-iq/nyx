/**
 * Nyx Authentication & Rate Limiting Middleware
 * Features: JWT auth, rate limiting, token blacklist, challenge-response
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const KEYS_FILE = path.join(__dirname, '../../.nyx-keys.json');
const BLACKLIST_FILE = path.join(__dirname, '../../.nyx-blacklist.json');

// Simple JWT implementation (no external deps)
const JWT = {
  secret: null,

  init() {
    const entropy = [
      crypto.randomBytes(32).toString('hex'),
      process.pid.toString(),
      Date.now().toString(),
      require('os').hostname()
    ].join(':');
    this.secret = crypto.createHash('sha256').update(entropy).digest();
    return this;
  },

  sign(payload, expiresIn = 86400) {
    const header = { alg: 'HS256', typ: 'JWT' };
    const now = Math.floor(Date.now() / 1000);
    const data = { ...payload, iat: now, exp: now + expiresIn };

    const headerB64 = Buffer.from(JSON.stringify(header)).toString('base64url');
    const payloadB64 = Buffer.from(JSON.stringify(data)).toString('base64url');
    const signature = crypto
      .createHmac('sha256', this.secret)
      .update(headerB64 + '.' + payloadB64)
      .digest('base64url');

    return headerB64 + '.' + payloadB64 + '.' + signature;
  },

  verify(token) {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return { ok: false, error: 'invalid format' };

      const [headerB64, payloadB64, signature] = parts;
      const expected = crypto
        .createHmac('sha256', this.secret)
        .update(headerB64 + '.' + payloadB64)
        .digest('base64url');

      if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
        return { ok: false, error: 'invalid signature' };
      }

      const payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString());
      const now = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp < now) {
        return { ok: false, error: 'token expired' };
      }

      return { ok: true, payload };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }
};

JWT.init();

// Rate Limiter
const RateLimiter = {
  store: new Map(),
  limits: {
    ip: { max: 100, windowMs: 60000 },
    token: { max: 500, windowMs: 60000 },
    global: { max: 1000, windowMs: 60000 }
  },

  check(key, type = 'ip') {
    const limit = this.limits[type] || this.limits.ip;
    const now = Date.now();
    let entry = this.store.get(key);

    if (!entry || entry.resetAt < now) {
      entry = { count: 0, resetAt: now + limit.windowMs };
      this.store.set(key, entry);
    }

    entry.count++;

    if (entry.count > limit.max) {
      return {
        ok: false,
        remaining: 0,
        resetAt: entry.resetAt,
        retryAfter: Math.ceil((entry.resetAt - now) / 1000)
      };
    }

    return { ok: true, remaining: limit.max - entry.count, resetAt: entry.resetAt };
  },

  cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.store) {
      if (entry.resetAt < now) this.store.delete(key);
    }
  }
};

setInterval(() => RateLimiter.cleanup(), 300000);

// Token Blacklist
const Blacklist = {
  tokens: new Set(),

  load() {
    try {
      if (fs.existsSync(BLACKLIST_FILE)) {
        const data = JSON.parse(fs.readFileSync(BLACKLIST_FILE, 'utf8'));
        this.tokens = new Set(data.tokens || []);
      }
    } catch {}
    return this;
  },

  save() {
    try {
      fs.writeFileSync(BLACKLIST_FILE, JSON.stringify({
        tokens: Array.from(this.tokens), updated: Date.now()
      }, null, 2));
    } catch {}
  },

  add(token) {
    const sig = token.split('.')[2];
    if (sig) { this.tokens.add(sig); this.save(); }
  },

  has(token) {
    const sig = token.split('.')[2];
    return sig ? this.tokens.has(sig) : false;
  }
};

Blacklist.load();

// Key Manager
const KeyManager = {
  keys: {},

  load() {
    try {
      if (fs.existsSync(KEYS_FILE)) {
        this.keys = JSON.parse(fs.readFileSync(KEYS_FILE, 'utf8'));
      }
    } catch {}
    return this;
  },

  save() {
    try {
      fs.writeFileSync(KEYS_FILE, JSON.stringify(this.keys, null, 2));
    } catch {}
  },

  verify(keyId) {
    return this.keys[keyId] || null;
  },

  create(name, permissions = ['chat']) {
    const id = crypto.randomBytes(8).toString('hex');
    const secret = crypto.randomBytes(32).toString('hex');
    const hash = crypto.createHash('sha256').update(secret).digest('hex');

    this.keys[id] = { name, hash, permissions, created: Date.now(), lastUsed: null };
    this.save();
    return { id, secret };
  },

  verifySecret(id, secret) {
    const key = this.keys[id];
    if (!key) return null;

    const hash = crypto.createHash('sha256').update(secret).digest('hex');
    if (key.hash !== hash) return null;

    key.lastUsed = Date.now();
    this.save();
    return key;
  }
};

KeyManager.load();

// Auth Middleware
function authMiddleware(options = {}) {
  const {
    required = true,
    permissions = [],
    skipPaths = ['/api/health', '/api/challenge', '/api/auth/login', '/metrics']
  } = options;

  return (req, res, next) => {
    if (skipPaths.some(p => req.path.startsWith(p))) return next();
    if (!req.path.startsWith('/api/')) return next();

    const ip = req.ip || req.connection.remoteAddress || 'unknown';
    const ipCheck = RateLimiter.check('ip:' + ip, 'ip');

    if (!ipCheck.ok) {
      res.set('Retry-After', ipCheck.retryAfter);
      return res.status(429).json({ error: 'rate_limit_exceeded', retryAfter: ipCheck.retryAfter });
    }

    const authHeader = req.headers.authorization;
    let token = null;
    let user = null;

    if (authHeader) {
      if (authHeader.startsWith('Bearer ')) {
        token = authHeader.slice(7);
        if (Blacklist.has(token)) return res.status(401).json({ error: 'token_revoked' });

        const result = JWT.verify(token);
        if (!result.ok) return res.status(401).json({ error: result.error });
        user = result.payload;

        const tokenCheck = RateLimiter.check('token:' + user.sub, 'token');
        if (!tokenCheck.ok) {
          res.set('Retry-After', tokenCheck.retryAfter);
          return res.status(429).json({ error: 'rate_limit_exceeded', retryAfter: tokenCheck.retryAfter });
        }
      } else if (authHeader.startsWith('Key ')) {
        const [id, secret] = authHeader.slice(4).split(':');
        const key = KeyManager.verifySecret(id, secret);
        if (!key) return res.status(401).json({ error: 'invalid_key' });
        user = { sub: id, name: key.name, permissions: key.permissions };
      }
    }

    if (required && !user) return res.status(401).json({ error: 'authentication_required' });

    if (permissions.length > 0 && user) {
      const userPerms = user.permissions || [];
      const hasPermission = permissions.some(p => userPerms.includes(p) || userPerms.includes('*'));
      if (!hasPermission) return res.status(403).json({ error: 'insufficient_permissions' });
    }

    req.user = user;
    req.token = token;
    res.set('X-RateLimit-Remaining', ipCheck.remaining);
    res.set('X-RateLimit-Reset', Math.ceil(ipCheck.resetAt / 1000));
    next();
  };
}

function rateLimitMiddleware(type = 'ip') {
  return (req, res, next) => {
    const ip = req.ip || req.connection.remoteAddress || 'unknown';
    const key = type === 'ip' ? 'ip:' + ip : 'global:all';
    const check = RateLimiter.check(key, type);

    if (!check.ok) {
      res.set('Retry-After', check.retryAfter);
      return res.status(429).json({ error: 'rate_limit_exceeded', retryAfter: check.retryAfter });
    }

    res.set('X-RateLimit-Remaining', check.remaining);
    res.set('X-RateLimit-Reset', Math.ceil(check.resetAt / 1000));
    next();
  };
}

function authRoutes(app) {
  app.get('/api/challenge', (req, res) => {
    const challenge = crypto.randomBytes(32).toString('hex');
    const expires = Date.now() + 300000;
    RateLimiter.store.set('challenge:' + challenge, { expires });
    res.json({ challenge, expires });
  });

  app.post('/api/auth/login', (req, res) => {
    const { keyId, secret } = req.body;
    if (keyId && secret) {
      const key = KeyManager.verifySecret(keyId, secret);
      if (!key) return res.status(401).json({ error: 'invalid_credentials' });

      const token = JWT.sign({ sub: keyId, name: key.name, permissions: key.permissions }, 86400);
      return res.json({ token, expiresIn: 86400, permissions: key.permissions });
    }
    res.status(400).json({ error: 'missing_credentials' });
  });

  app.post('/api/auth/logout', authMiddleware({ required: true }), (req, res) => {
    if (req.token) Blacklist.add(req.token);
    res.json({ ok: true });
  });

  app.post('/api/auth/keys', authMiddleware({ required: true, permissions: ['admin'] }), (req, res) => {
    const { name, permissions } = req.body;
    if (!name) return res.status(400).json({ error: 'name_required' });
    const key = KeyManager.create(name, permissions || ['chat']);
    res.json({ id: key.id, secret: key.secret, message: 'Save this secret - shown only once' });
  });

  app.get('/api/auth/keys', authMiddleware({ required: true, permissions: ['admin'] }), (req, res) => {
    const keys = Object.entries(KeyManager.keys).map(([id, k]) => ({
      id, name: k.name, permissions: k.permissions, created: k.created, lastUsed: k.lastUsed
    }));
    res.json({ keys });
  });

  app.delete('/api/auth/keys/:id', authMiddleware({ required: true, permissions: ['admin'] }), (req, res) => {
    const { id } = req.params;
    if (KeyManager.keys[id]) {
      delete KeyManager.keys[id];
      KeyManager.save();
      res.json({ ok: true });
    } else {
      res.status(404).json({ error: 'key_not_found' });
    }
  });

  app.get('/api/auth/me', authMiddleware({ required: true }), (req, res) => {
    res.json({ user: req.user });
  });
}

module.exports = { JWT, RateLimiter, Blacklist, KeyManager, authMiddleware, rateLimitMiddleware, authRoutes };
