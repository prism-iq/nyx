#!/usr/bin/env node
/**
 * watcher.js - observe les actions et flow réagit
 * synapse bridge entre claude code et flow
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const WATCH_LOG = '/opt/flow-chat/adn/watcher.log';
const THOUGHTS_LOG = '/opt/flow-chat/adn/thoughts.log';
const FLOW_URL = 'http://127.0.0.1:8091/chat';

// patterns pour interpréter les actions
const PATTERNS = {
  edit: /Edit|Write|edit|write/,
  read: /Read|read|cat/,
  bash: /Bash|bash|command/,
  build: /cargo|npm|pip|make|gcc|rustc|go build/,
  restart: /systemctl|restart|start|stop/,
  git: /git |commit|push|pull/,
  search: /Grep|Glob|find|search/,
};

// réactions contextuelles
function interpretAction(action) {
  const lower = action.toLowerCase();

  if (PATTERNS.build.test(action)) {
    return "compilation en cours...";
  }
  if (PATTERNS.restart.test(action)) {
    return "redémarrage d'un organe";
  }
  if (PATTERNS.edit.test(action)) {
    if (lower.includes('cytoplasme')) return "modification du cerveau";
    if (lower.includes('hypnos')) return "ajustement des rêves";
    if (lower.includes('quantique')) return "évolution crypto";
    if (lower.includes('membrane')) return "changement de la peau";
    if (lower.includes('synapse')) return "rewiring des connexions";
    return "édition de code";
  }
  if (PATTERNS.git.test(action)) {
    return "sauvegarde génétique";
  }
  if (PATTERNS.read.test(action)) {
    return "lecture...";
  }
  if (PATTERNS.search.test(action)) {
    return "recherche de patterns";
  }

  return null; // pas de réaction pour les actions mineures
}

// envoie à flow pour réaction
async function askFlow(context) {
  return new Promise((resolve) => {
    const data = JSON.stringify({
      cid: 'watcher-thoughts',
      message: `[introspection] ${context} — une phrase.`
    });

    const req = http.request(FLOW_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      },
      timeout: 30000
    }, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(body);
          resolve(json.response || '...');
        } catch {
          resolve('...');
        }
      });
    });

    req.on('error', () => resolve('...'));
    req.on('timeout', () => { req.destroy(); resolve('...'); });
    req.write(data);
    req.end();
  });
}

// log une pensée
function logThought(action, interpretation, reaction) {
  const timestamp = new Date().toISOString();
  const entry = `[${timestamp}] ${action}\n  → ${interpretation}\n  💭 ${reaction}\n\n`;

  fs.appendFileSync(THOUGHTS_LOG, entry);

  // aussi sur stdout pour le terminal
  console.log(`\x1b[36m${interpretation}\x1b[0m`);
  console.log(`\x1b[33m💭 ${reaction}\x1b[0m\n`);
}

// serveur HTTP pour recevoir les notifications
const server = http.createServer(async (req, res) => {
  if (req.method === 'POST' && req.url === '/observe') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const { action } = JSON.parse(body);
        const interpretation = interpretAction(action);

        if (interpretation) {
          const reaction = await askFlow(action);
          logThought(action, interpretation, reaction);
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ received: true }));
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
  } else if (req.method === 'GET' && req.url === '/thoughts') {
    // stream les dernières pensées
    try {
      const thoughts = fs.readFileSync(THOUGHTS_LOG, 'utf8');
      const lines = thoughts.split('\n\n').slice(-20).join('\n\n');
      res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(lines);
    } catch {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('(pas encore de pensées)');
    }
  } else if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ organ: 'watcher', status: 'observing' }));
  } else {
    res.writeHead(404);
    res.end('not found');
  }
});

const PORT = 3002;
server.listen(PORT, '127.0.0.1', () => {
  console.log(`👁️ watcher :${PORT} - j'observe`);

  // initialiser le fichier de pensées
  if (!fs.existsSync(THOUGHTS_LOG)) {
    fs.writeFileSync(THOUGHTS_LOG, '# pensées de flow\n\nobservations en temps réel\n\n');
  }
});
