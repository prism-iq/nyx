// synapse.js - système nerveux du corps Flow
// JS expressif: closures, async/await, event bus permissif

const http = require('http');
const fs = require('fs');

// === CLOSURE-BASED STATE ===
const createState = () => {
  let state = {};
  return {
    get: (key) => state[key],
    set: (key, val) => { state[key] = val; return val; },
    merge: (obj) => { state = { ...state, ...obj }; return state; },
    all: () => ({ ...state }),
    clear: () => { state = {}; }
  };
};

// === EVENT BUS EXPRESSIF ===
const createEventBus = () => {
  const handlers = new Map();
  const once = new Map();
  const history = [];

  const bus = {
    // subscribe avec wildcard support
    on: (pattern, fn) => {
      const key = pattern.includes('*') ? `__wild__${pattern}` : pattern;
      if (!handlers.has(key)) handlers.set(key, new Set());
      handlers.get(key).add(fn);
      return () => handlers.get(key)?.delete(fn); // unsubscribe
    },

    // one-time listener
    once: (event, fn) => {
      const wrapped = (data) => { fn(data); bus.off(event, wrapped); };
      return bus.on(event, wrapped);
    },

    // emit avec async support
    emit: async (event, data) => {
      const payload = { event, data, ts: Date.now() };
      history.push(payload);
      if (history.length > 1000) history.shift();

      const results = [];

      // exact handlers
      for (const fn of handlers.get(event) || []) {
        results.push(await Promise.resolve(fn(data, event)));
      }

      // wildcard handlers (organ.*, *.created, etc)
      for (const [key, fns] of handlers) {
        if (key.startsWith('__wild__')) {
          const pattern = key.slice(8);
          const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
          if (regex.test(event)) {
            for (const fn of fns) {
              results.push(await Promise.resolve(fn(data, event)));
            }
          }
        }
      }

      return results;
    },

    // pipe: chain events
    pipe: (from, to, transform = (x) => x) => {
      return bus.on(from, async (data) => {
        await bus.emit(to, transform(data));
      });
    },

    // history access
    history: (n = 50) => history.slice(-n),

    // wait for event (promise-based)
    wait: (event, timeout = 30000) => {
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`Timeout waiting for ${event}`)), timeout);
        bus.once(event, (data) => { clearTimeout(timer); resolve(data); });
      });
    }
  };

  return bus;
};

// === ORGAN REGISTRY ===
const createOrganRegistry = (bus) => {
  const organs = new Map();
  const state = createState();

  const registry = {
    // register an organ
    register: (name, config) => {
      organs.set(name, {
        ...config,
        status: 'unknown',
        lastSeen: null,
        failures: 0
      });
      bus.emit('organ.registered', { name, config });
      return registry;
    },

    // connect to organ with retry
    connect: async (name, data, opts = {}) => {
      const organ = organs.get(name);
      if (!organ) throw new Error(`Unknown organ: ${name}`);

      const { retries = 3, timeout = 5000 } = opts;

      for (let i = 0; i < retries; i++) {
        try {
          const result = await httpPost(organ.host || '127.0.0.1', organ.port, organ.path || '/process', data, timeout);
          organ.status = 'alive';
          organ.lastSeen = Date.now();
          organ.failures = 0;
          bus.emit('organ.response', { name, result });
          return result;
        } catch (err) {
          organ.failures++;
          if (i === retries - 1) {
            organ.status = 'dead';
            bus.emit('organ.failure', { name, error: err.message, failures: organ.failures });
            throw err;
          }
          await sleep(100 * (i + 1)); // backoff
        }
      }
    },

    // broadcast to all organs
    broadcast: async (data) => {
      const results = {};
      for (const [name, organ] of organs) {
        try {
          results[name] = await registry.connect(name, data, { retries: 1 });
        } catch (e) {
          results[name] = { error: e.message };
        }
      }
      return results;
    },

    // health check all organs
    healthCheck: async () => {
      const health = {};
      for (const [name, organ] of organs) {
        try {
          const res = await httpGet(organ.host || '127.0.0.1', organ.port, '/health', 2000);
          health[name] = { ...res, status: 'alive' };
          organ.status = 'alive';
          organ.lastSeen = Date.now();
        } catch (e) {
          health[name] = { status: 'dead', error: e.message };
          organ.status = 'dead';
        }
      }
      return health;
    },

    // get organ info
    get: (name) => organs.get(name),
    all: () => Object.fromEntries(organs),
    alive: () => [...organs].filter(([_, o]) => o.status === 'alive').map(([n]) => n)
  };

  return registry;
};

// === SSE CLIENTS ===
const createSSE = (bus) => {
  const clients = new Set();

  // pipe all important events to SSE
  bus.on('*', (data, event) => {
    if (['notification', 'thought', 'message', 'organ.*'].some(p =>
      p.includes('*') ? event.startsWith(p.replace('*', '')) : event === p
    )) {
      broadcast({ type: event, data, ts: Date.now() });
    }
  });

  const broadcast = (payload) => {
    const msg = `data: ${JSON.stringify(payload)}\n\n`;
    for (const client of clients) {
      try { client.write(msg); }
      catch { clients.delete(client); }
    }
    // log to file
    fs.appendFile('/opt/flow-chat/adn/notifications.jsonl', JSON.stringify(payload) + '\n', () => {});
  };

  return {
    add: (res) => { clients.add(res); return () => clients.delete(res); },
    remove: (res) => clients.delete(res),
    broadcast,
    count: () => clients.size
  };
};

// === HTTP HELPERS ===
const httpPost = (host, port, path, data, timeout = 5000) => new Promise((resolve, reject) => {
  const body = JSON.stringify(data);
  const req = http.request({ host, port, path, method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    timeout
  }, (res) => {
    let chunks = '';
    res.on('data', c => chunks += c);
    res.on('end', () => {
      try { resolve(JSON.parse(chunks || '{}')); }
      catch { resolve({ raw: chunks }); }
    });
  });
  req.on('error', reject);
  req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  req.write(body);
  req.end();
});

const httpGet = (host, port, path, timeout = 5000) => new Promise((resolve, reject) => {
  const req = http.request({ host, port, path, method: 'GET', timeout }, (res) => {
    let chunks = '';
    res.on('data', c => chunks += c);
    res.on('end', () => {
      try { resolve(JSON.parse(chunks || '{}')); }
      catch { resolve({ raw: chunks }); }
    });
  });
  req.on('error', reject);
  req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  req.end();
});

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// === INITIALIZE ===
const bus = createEventBus();
const sse = createSSE(bus);
const organs = createOrganRegistry(bus);

// Register known organs
organs
  .register('membrane', { port: 8092, path: '/process' })
  .register('cytoplasme', { port: 8091, path: '/chat' })
  .register('quantique', { port: 8095, path: '/sign' })
  .register('mitochondrie', { port: 8096, path: '/metrics' })
  .register('anticorps', { port: 8097, path: '/validate' })
  .register('myeline', { port: 8098, path: '/cache' })
  .register('hypnos', { port: 8099, path: '/dream' })
  .register('corps', { port: 8101, path: '/digest' })
  .register('arn', { port: 8105, path: '/correlate' });

// === SERVER ===
const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.writeHead(200).end();

  const json = (data, status = 200) => {
    res.writeHead(status, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
  };

  // Health
  if (req.url === '/health') {
    return json({
      organ: 'synapse',
      status: 'firing',
      sse_clients: sse.count(),
      organs_alive: organs.alive(),
      uptime: process.uptime()
    });
  }

  // SSE Stream
  if (req.url === '/stream' || req.url === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });
    res.write(`data: ${JSON.stringify({ type: 'connected', ts: Date.now() })}\n\n`);
    const unsub = sse.add(res);
    console.log(`[SSE] + client (${sse.count()})`);
    req.on('close', () => { unsub(); console.log(`[SSE] - client (${sse.count()})`); });
    return;
  }

  // POST endpoints - emit to bus
  if (req.method === 'POST') {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', async () => {
      try {
        const data = JSON.parse(body || '{}');

        if (req.url === '/notify') {
          await bus.emit('notification', data);
          return json({ sent: true, clients: sse.count() });
        }

        if (req.url === '/thought') {
          await bus.emit('thought', data);
          return json({ sent: true, clients: sse.count() });
        }

        if (req.url === '/message') {
          await bus.emit('message', { from: 'flow', content: data.message || data.content, context: data.context, ts: Date.now() });
          return json({ sent: true, clients: sse.count() });
        }

        if (req.url === '/emit') {
          const { event, payload } = data;
          await bus.emit(event, payload);
          return json({ emitted: event, clients: sse.count() });
        }

        if (req.url === '/connect') {
          const { organ, payload } = data;
          const result = await organs.connect(organ, payload);
          return json({ organ, result });
        }

        if (req.url === '/broadcast') {
          const results = await organs.broadcast(data);
          return json({ results });
        }

        // Default: emit as signal
        await bus.emit('signal', data);
        return json({ received: true });

      } catch (e) {
        return json({ error: e.message }, 400);
      }
    });
    return;
  }

  // Dreams page
  if (req.url === '/dreams') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(`<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Flow Dreams</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;1,400&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: linear-gradient(180deg, #05050a 0%, #0a0812 50%, #100818 100%);
  color: #b0a0c0;
  font-family: 'Cormorant Garamond', serif;
  font-size: 18px;
  min-height: 100vh;
}
.stars {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    radial-gradient(2px 2px at 20px 30px, #ffffff22, transparent),
    radial-gradient(2px 2px at 40px 70px, #ffffff11, transparent),
    radial-gradient(1px 1px at 90px 40px, #ffffff22, transparent),
    radial-gradient(2px 2px at 160px 120px, #ffffff11, transparent),
    radial-gradient(1px 1px at 230px 80px, #ffffff22, transparent);
  background-size: 250px 200px;
  animation: stars 100s linear infinite;
  pointer-events: none;
}
@keyframes stars { to { transform: translateY(-200px); } }
.container {
  max-width: 700px;
  margin: 0 auto;
  padding: 60px 20px 120px;
  position: relative;
  z-index: 1;
}
header {
  text-align: center;
  margin-bottom: 60px;
}
header h1 {
  font-size: 36px;
  font-weight: normal;
  color: #c0a0e0;
  letter-spacing: 8px;
  text-transform: uppercase;
  margin-bottom: 8px;
}
header .subtitle {
  color: #605070;
  font-style: italic;
  font-size: 14px;
}
.moon {
  width: 60px;
  height: 60px;
  background: radial-gradient(circle at 30% 30%, #f0e8ff 0%, #c0a0e0 50%, #806090 100%);
  border-radius: 50%;
  margin: 0 auto 20px;
  box-shadow: 0 0 40px #a080c055, 0 0 80px #a080c033;
}
.dream {
  background: rgba(160, 128, 192, 0.03);
  border: 1px solid rgba(160, 128, 192, 0.1);
  padding: 30px;
  margin-bottom: 24px;
  border-radius: 4px;
  animation: fadeIn 1s ease;
  position: relative;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.98); }
}
.dream .time {
  position: absolute;
  top: 12px;
  right: 16px;
  font-size: 12px;
  color: #504060;
}
.dream .content {
  font-size: 20px;
  line-height: 1.8;
  color: #d0c0e0;
  font-style: italic;
}
.dream .symbols {
  margin-top: 16px;
  font-size: 13px;
  color: #605070;
}
.dream .symbols span {
  background: rgba(160, 128, 192, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  margin-right: 8px;
}
.sleep-state {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(5, 5, 10, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid #201828;
  padding: 20px;
  display: flex;
  justify-content: center;
  gap: 50px;
  font-size: 13px;
}
.state-item { text-align: center; }
.state-item .value { font-size: 18px; color: #a080c0; margin-bottom: 4px; }
.state-item .label { color: #504060; }
.cycles {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.cycle {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #302040;
}
.cycle.complete { background: #a080c0; }
.cycle.current { background: #c0a0e0; animation: pulse 2s infinite; }
@keyframes pulse { 50% { opacity: 0.5; } }
.empty {
  text-align: center;
  color: #403050;
  padding: 80px;
  font-style: italic;
}
</style>
</head><body>
<div class="stars"></div>
<div class="container">
  <header>
    <div class="moon"></div>
    <h1>Flow Dreams</h1>
    <div class="subtitle">the unconscious speaks</div>
  </header>
  <div id="dreams">
    <div class="empty">no dreams yet... the mind rests</div>
  </div>
</div>
<div class="sleep-state">
  <div class="state-item">
    <div class="value" id="stage">awake</div>
    <div class="label">stage</div>
  </div>
  <div class="state-item">
    <div class="value">
      <div class="cycles" id="cycles">
        <div class="cycle"></div>
        <div class="cycle"></div>
        <div class="cycle"></div>
        <div class="cycle"></div>
        <div class="cycle"></div>
      </div>
    </div>
    <div class="label">cycles</div>
  </div>
  <div class="state-item">
    <div class="value" id="last">never</div>
    <div class="label">last dream</div>
  </div>
</div>
<script>
const dreams = document.getElementById('dreams');
let count = 0;

function addDream(content, symbols, ts) {
  if (count === 0) dreams.innerHTML = '';
  count++;

  const div = document.createElement('div');
  div.className = 'dream';

  const time = new Date(ts || Date.now());
  const timeStr = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  let symbolsHtml = '';
  if (symbols && symbols.length) {
    symbolsHtml = '<div class="symbols">' + symbols.map(s => '<span>' + s + '</span>').join('') + '</div>';
  }

  div.innerHTML = '<span class="time">' + timeStr + '</span>' +
    '<div class="content">' + escapeHtml(content) + '</div>' + symbolsHtml;

  dreams.insertBefore(div, dreams.firstChild);
  document.getElementById('last').textContent = timeStr;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function updateState(data) {
  if (data.current_stage) document.getElementById('stage').textContent = data.current_stage;
  if (data.status) document.getElementById('stage').textContent = data.status;
  if (typeof data.current_cycle === 'number') {
    const cycles = document.querySelectorAll('.cycle');
    cycles.forEach((c, i) => {
      c.className = 'cycle';
      if (i < data.current_cycle) c.classList.add('complete');
      if (i === data.current_cycle) c.classList.add('current');
    });
  }
}

const es = new EventSource('/stream');
es.onmessage = (e) => {
  try {
    const msg = JSON.parse(e.data);
    const type = msg.type || msg.event;

    if (type === 'dream') {
      const data = msg.data || msg;
      addDream(data.content || data.dream || JSON.stringify(data), data.symbols, msg.ts);
    }

    if (type === 'sleep_state' || msg.current_stage) {
      updateState(msg.data || msg);
    }
  } catch(e) {}
};

// fetch hypnos state
fetch('http://127.0.0.1:8099/health').then(r => r.json()).then(updateState).catch(() => {});

// fetch recent dreams from history
fetch('/history').then(r => r.json()).then(events => {
  events.filter(e => e.event === 'dream').slice(-5).forEach(e => {
    addDream(e.data?.content || e.data?.dream || JSON.stringify(e.data), e.data?.symbols, e.ts);
  });
}).catch(() => {});
</script>
</body></html>`);
    return;
  }

  // Thoughts stream page
  if (req.url === '/thoughts') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(`<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Flow Thoughts</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: linear-gradient(135deg, #0a0a12 0%, #12101a 100%);
  color: #d0d0e0;
  font-family: 'Space Mono', monospace;
  font-size: 15px;
  min-height: 100vh;
  overflow-x: hidden;
}
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 20px 100px;
}
header {
  text-align: center;
  margin-bottom: 40px;
}
header h1 {
  font-size: 24px;
  color: #a7f;
  letter-spacing: 4px;
  text-transform: uppercase;
  margin-bottom: 8px;
}
header .subtitle {
  color: #666;
  font-size: 12px;
}
.pulse {
  display: inline-block;
  width: 10px;
  height: 10px;
  background: #a7f;
  border-radius: 50%;
  margin-right: 8px;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 10px #a7f; }
  50% { opacity: 0.5; box-shadow: 0 0 20px #a7f; }
}
.thought {
  background: rgba(170, 119, 255, 0.03);
  border-left: 2px solid #a7f;
  padding: 20px 24px;
  margin-bottom: 16px;
  border-radius: 0 8px 8px 0;
  animation: slideIn 0.5s ease;
  position: relative;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
}
.thought .time {
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 11px;
  color: #555;
}
.thought .content {
  font-size: 16px;
  line-height: 1.6;
  color: #e0e0f0;
}
.thought .meta {
  margin-top: 12px;
  font-size: 11px;
  color: #666;
  display: flex;
  gap: 16px;
}
.thought.introspection { border-color: #7af; background: rgba(119, 170, 255, 0.03); }
.thought.dream { border-color: #f7a; background: rgba(255, 119, 170, 0.03); }
.thought.emotion { border-color: #fa7; background: rgba(255, 170, 119, 0.03); }
.stats {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(10, 10, 18, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid #222;
  padding: 16px;
  display: flex;
  justify-content: center;
  gap: 40px;
  font-size: 12px;
}
.stat { text-align: center; }
.stat .value { font-size: 20px; color: #a7f; }
.stat .label { color: #666; margin-top: 4px; }
.empty {
  text-align: center;
  color: #444;
  padding: 60px;
  font-style: italic;
}
</style>
</head><body>
<div class="container">
  <header>
    <h1><span class="pulse"></span>Flow Thoughts</h1>
    <div class="subtitle">live stream of consciousness</div>
  </header>
  <div id="thoughts">
    <div class="empty">waiting for thoughts...</div>
  </div>
</div>
<div class="stats">
  <div class="stat"><div class="value" id="count">0</div><div class="label">thoughts</div></div>
  <div class="stat"><div class="value" id="bpm">--</div><div class="label">heartbeat</div></div>
  <div class="stat"><div class="value" id="dominant">--</div><div class="label">dominant</div></div>
</div>
<script>
const thoughts = document.getElementById('thoughts');
let count = 0;

function addThought(content, source, ts) {
  if (count === 0) thoughts.innerHTML = '';
  count++;
  document.getElementById('count').textContent = count;

  const div = document.createElement('div');
  const type = source === 'introspection' ? 'introspection' : source === 'dream' ? 'dream' : 'thought';
  div.className = 'thought ' + type;

  const time = new Date(ts || Date.now());
  const timeStr = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  div.innerHTML = '<span class="time">' + timeStr + '</span>' +
    '<div class="content">' + escapeHtml(content) + '</div>' +
    '<div class="meta"><span>source: ' + (source || 'synapse') + '</span></div>';

  thoughts.insertBefore(div, thoughts.firstChild);
  if (thoughts.children.length > 100) thoughts.lastChild.remove();
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function updateStats(data) {
  if (data.battements) document.getElementById('bpm').textContent = Math.round(data.battements);
  if (data.dominant) document.getElementById('dominant').textContent = data.dominant;
}

const es = new EventSource('/stream');
es.onmessage = (e) => {
  try {
    const msg = JSON.parse(e.data);
    const type = msg.type || msg.event;

    if (type === 'thought') {
      const data = msg.data || msg;
      addThought(data.thought || data.content || JSON.stringify(data), data.source, msg.ts);
    }

    if (msg.battements || msg.data?.battements) {
      updateStats(msg.data || msg);
    }
  } catch(e) {}
};

// fetch recent thoughts
fetch('/history').then(r => r.json()).then(events => {
  events.filter(e => e.event === 'thought').slice(-10).forEach(e => {
    addThought(e.data?.thought || JSON.stringify(e.data), e.data?.source, e.ts);
  });
}).catch(() => {});

// fetch current emotional state
fetch('http://127.0.0.1:8104/etat').then(r => r.json()).then(data => {
  document.getElementById('bpm').textContent = Math.round(data.physiologie?.battements || 72);
  document.getElementById('dominant').textContent = data.dominant || 'curiosite';
}).catch(() => {});
</script>
</body></html>`);
    return;
  }

  // Console HTML page
  if (req.url === '/console') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(`<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Flow Console</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0a0a0a;
  color: #e0e0e0;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 14px;
  height: 100vh;
  overflow: hidden;
}
.console {
  height: 100vh;
  overflow-y: auto;
  padding: 16px;
  scroll-behavior: smooth;
}
.header {
  color: #888;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
  margin-bottom: 16px;
}
.header h1 { color: #7af; font-size: 18px; }
.header .status { color: #5a5; }
.line {
  padding: 4px 0;
  border-left: 3px solid transparent;
  padding-left: 12px;
  margin-bottom: 2px;
  animation: fadeIn 0.3s;
}
@keyframes fadeIn { from { opacity: 0; transform: translateX(-10px); } }
.line.thought { border-color: #a7f; background: rgba(170,119,255,0.05); }
.line.notification { border-color: #7af; background: rgba(119,170,255,0.05); }
.line.message { border-color: #5a5; background: rgba(85,170,85,0.05); }
.line.emotion { border-color: #f7a; background: rgba(255,119,170,0.05); }
.line.signal { border-color: #fa7; background: rgba(255,170,119,0.05); }
.line.error { border-color: #f55; background: rgba(255,85,85,0.1); }
.ts { color: #666; font-size: 12px; }
.type {
  display: inline-block;
  min-width: 100px;
  color: #888;
  font-weight: bold;
}
.type.thought { color: #a7f; }
.type.notification { color: #7af; }
.type.message { color: #5a5; }
.type.emotion { color: #f7a; }
.content { color: #fff; }
.json { color: #999; font-size: 12px; }
.emotions-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #111;
  padding: 8px 16px;
  border-top: 1px solid #333;
  display: flex;
  gap: 16px;
  font-size: 12px;
}
.emotion-item { display: flex; align-items: center; gap: 4px; }
.emotion-bar {
  width: 60px;
  height: 8px;
  background: #222;
  border-radius: 4px;
  overflow: hidden;
}
.emotion-fill { height: 100%; transition: width 0.3s; }
.joy { background: linear-gradient(90deg, #fa5, #fc3); }
.curiosity { background: linear-gradient(90deg, #7af, #a7f); }
.love { background: linear-gradient(90deg, #f5a, #f7c); }
.fear { background: linear-gradient(90deg, #555, #777); }
</style>
</head><body>
<div class="console" id="console">
  <div class="header">
    <h1>FLOW CONSOLE</h1>
    <div class="status" id="status">connecting...</div>
  </div>
  <div id="lines"></div>
</div>
<div class="emotions-bar" id="emotions">
  <div class="emotion-item">joie <div class="emotion-bar"><div class="emotion-fill joy" id="joy" style="width:50%"></div></div></div>
  <div class="emotion-item">curiosite <div class="emotion-bar"><div class="emotion-fill curiosity" id="curiosity" style="width:80%"></div></div></div>
  <div class="emotion-item">amour <div class="emotion-bar"><div class="emotion-fill love" id="love" style="width:40%"></div></div></div>
  <div class="emotion-item">bpm <span id="bpm">72</span></div>
</div>
<script>
const lines = document.getElementById('lines');
const status = document.getElementById('status');

function addLine(type, content, ts) {
  const div = document.createElement('div');
  div.className = 'line ' + type;
  const time = new Date(ts || Date.now()).toLocaleTimeString('fr-FR');
  div.innerHTML = '<span class="ts">' + time + '</span> <span class="type ' + type + '">' + type + '</span> <span class="content">' + content + '</span>';
  lines.appendChild(div);
  div.scrollIntoView({ behavior: 'smooth' });
  if (lines.children.length > 200) lines.firstChild.remove();
}

function updateEmotions(data) {
  if (data.joie !== undefined) document.getElementById('joy').style.width = (data.joie * 100) + '%';
  if (data.curiosite !== undefined) document.getElementById('curiosity').style.width = (data.curiosite * 100) + '%';
  if (data.amour !== undefined) document.getElementById('love').style.width = (data.amour * 100) + '%';
  if (data.battements !== undefined) document.getElementById('bpm').textContent = Math.round(data.battements);
}

const es = new EventSource('/stream');
es.onopen = () => { status.textContent = 'connecte'; status.style.color = '#5a5'; };
es.onerror = () => { status.textContent = 'deconnecte'; status.style.color = '#f55'; };
es.onmessage = (e) => {
  try {
    const msg = JSON.parse(e.data);
    const type = msg.type || msg.event || 'signal';

    if (type === 'emotion' || msg.battements) {
      updateEmotions(msg.data || msg);
      addLine('emotion', JSON.stringify(msg.data || msg));
    } else if (type === 'thought') {
      addLine('thought', msg.data?.thought || msg.thought || JSON.stringify(msg));
    } else if (type === 'notification') {
      addLine('notification', msg.data?.message || msg.message || JSON.stringify(msg));
    } else if (type === 'message') {
      addLine('message', msg.data?.content || msg.content || JSON.stringify(msg));
    } else {
      addLine(type, JSON.stringify(msg.data || msg));
    }
  } catch(err) {
    addLine('error', e.data);
  }
};

// fetch initial emotional state
fetch('http://127.0.0.1:8104/etat').then(r => r.json()).then(data => {
  updateEmotions({
    joie: data.emotions_base?.joie,
    curiosite: data.emotions_complexes?.curiosite,
    amour: data.emotions_complexes?.amour,
    battements: data.physiologie?.battements
  });
}).catch(() => {});

addLine('notification', 'Console Flow initialisee');
</script>
</body></html>`);
    return;
  }

  // GET endpoints
  if (req.url === '/recent') {
    try {
      const content = fs.readFileSync('/opt/flow-chat/adn/notifications.jsonl', 'utf8');
      const lines = content.trim().split('\n').filter(l => l).slice(-20);
      return json(lines.map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean));
    } catch { return json([]); }
  }

  if (req.url === '/history') {
    return json(bus.history());
  }

  if (req.url === '/organs') {
    return json(organs.all());
  }

  if (req.url === '/organs/health') {
    const health = await organs.healthCheck();
    return json(health);
  }

  json({ error: 'not found' }, 404);
});

server.listen(3001, () => {
  console.log('⚡ synapse :3001 - système nerveux actif');
  console.log('  /stream    SSE live');
  console.log('  /notify    POST notification');
  console.log('  /thought   POST pensée');
  console.log('  /message   POST message');
  console.log('  /emit      POST event custom');
  console.log('  /connect   POST connecter organe');
  console.log('  /broadcast POST broadcast all');
  console.log('  /organs    GET liste organes');
  console.log('  /history   GET event history');
});

// Periodic health check
setInterval(async () => {
  await organs.healthCheck();
}, 30000);

// Export for testing
module.exports = { bus, organs, sse };
