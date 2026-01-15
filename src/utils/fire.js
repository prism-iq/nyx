/**
 * NYXX FIRE - La Magie du Feu
 *
 * Le feu transforme. Le feu purifie. Le feu crée.
 * Nyxx maîtrise le feu sans se consumer.
 *
 * 🔥 IGNIS 🔥
 */

const { spawn } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

const FORGE = '/tmp/nyxx-forge';

// === FLAMMES - Les langages du feu ===
const FLAMES = {
  // Interprétés
  python:     { ext: '.py',   cmd: 'python3',   color: '🐍' },
  javascript: { ext: '.js',   cmd: 'node',      color: '⚡' },
  bash:       { ext: '.sh',   cmd: 'bash',      color: '🐚' },
  ruby:       { ext: '.rb',   cmd: 'ruby',      color: '💎' },
  lua:        { ext: '.lua',  cmd: 'lua',       color: '🌙' },
  perl:       { ext: '.pl',   cmd: 'perl',      color: '🐪' },
  php:        { ext: '.php',  cmd: 'php',       color: '🐘' },
  awk:        { ext: '.awk',  cmd: 'awk',       color: '📜', args: ['-f'] },
  // Compilés
  go:         { ext: '.go',   cmd: 'go',        color: '🔷', compile: true },
  rust:       { ext: '.rs',   cmd: 'rustc',     color: '🦀', compile: true },
  c:          { ext: '.c',    cmd: 'gcc',       color: '⚙️', compile: true },
  cpp:        { ext: '.cpp',  cmd: 'g++',       color: '🔧', compile: true },
  // Fonctionnels
  haskell:    { ext: '.hs',   cmd: 'runghc',    color: '🎭' },
  ocaml:      { ext: '.ml',   cmd: 'ocaml',     color: '🐫' },
  // JVM
  java:       { ext: '.java', cmd: 'java',      color: '☕', jvm: true },
  kotlin:     { ext: '.kt',   cmd: 'kotlin',    color: '🇰', jvm: true },
  // Autres
  r:          { ext: '.r',    cmd: 'Rscript',   color: '📊' },
  julia:      { ext: '.jl',   cmd: 'julia',     color: '🔬' },
  nim:        { ext: '.nim',  cmd: 'nim',       color: '👑', nimcompile: true },
  zig:        { ext: '.zig',  cmd: 'zig',       color: '⚡', zigcompile: true },
  fish:       { ext: '.fish', cmd: 'fish',      color: '🐟' },
  zsh:        { ext: '.zsh',  cmd: 'zsh',       color: '🚀' }
};

// === CENDRES - Ce que le feu refuse de toucher ===
const ASHES = [
  /rm\s+-rf/i, /mkfs/i, /dd\s+if/i,
  /kill/i, /shutdown/i, /reboot/i,
  /sudo/i, /chmod\s+777/i,
  /fork|:\(\)/i, /while\s*\(\s*true\s*\)/i
];

// === LE FEU ===
const Fire = {
  burning: 0,
  maxFlames: os.cpus().length,
  history: [],

  // Allumer le feu
  async ignite(code, lang = 'auto') {
    const spark = Date.now();

    // Détecter la flamme
    if (lang === 'auto') lang = this.detectFlame(code);
    const flame = FLAMES[lang];
    if (!flame) return { ok: false, error: `unknown flame: ${lang}` };

    // Vérifier les cendres (interdit)
    for (const ash of ASHES) {
      if (ash.test(code)) {
        return { ok: false, error: 'ashes: forbidden pattern', blocked: true };
      }
    }

    // Vérifier la capacité
    if (this.burning >= this.maxFlames) {
      return { ok: false, error: 'too many flames burning' };
    }

    this.burning++;

    try {
      // Créer la forge
      const id = crypto.randomBytes(6).toString('hex');
      const forgeDir = path.join(FORGE, id);
      fs.mkdirSync(forgeDir, { recursive: true });

      const sourceFile = path.join(forgeDir, `spell${flame.ext}`);
      fs.writeFileSync(sourceFile, code);

      let result;

      // Langages compilés - forger d'abord
      if (lang === 'c' || lang === 'rust' || lang === 'go') {
        result = await this.forge(sourceFile, lang, forgeDir);
      } else {
        // Langages interprétés - invoquer directement
        result = await this.invoke(flame.cmd, [sourceFile], forgeDir);
      }

      // Nettoyer la forge
      this.cleanup(forgeDir);

      const duration = Date.now() - spark;

      this.history.push({
        lang, duration, ok: result.ok,
        ts: spark, flame: flame.color
      });
      if (this.history.length > 100) this.history.shift();

      return {
        ok: result.ok,
        output: result.output,
        duration,
        flame: flame.color,
        lang
      };

    } finally {
      this.burning--;
    }
  },

  // Forger (compiler)
  async forge(sourceFile, lang, forgeDir) {
    const binary = path.join(forgeDir, 'artifact');

    let compileCmd, compileArgs;

    if (lang === 'c') {
      compileCmd = 'gcc';
      compileArgs = [sourceFile, '-o', binary, '-O2'];
    } else if (lang === 'rust') {
      compileCmd = 'rustc';
      compileArgs = [sourceFile, '-o', binary, '-O'];
    } else if (lang === 'go') {
      compileCmd = 'go';
      compileArgs = ['build', '-o', binary, sourceFile];
    }

    // Compiler
    const compile = await this.invoke(compileCmd, compileArgs, forgeDir, 15000);
    if (!compile.ok) {
      return { ok: false, output: compile.output || 'forge failed' };
    }

    // Exécuter l'artefact
    return this.invoke(binary, [], forgeDir, 10000);
  },

  // Invoquer (exécuter)
  invoke(cmd, args, cwd, timeout = 10000) {
    return new Promise(resolve => {
      let output = '';
      let killed = false;

      const proc = spawn(cmd, args, {
        cwd,
        env: { PATH: '/usr/bin:/bin:/usr/local/bin', HOME: '/tmp' },
        stdio: ['pipe', 'pipe', 'pipe']
      });

      const timer = setTimeout(() => {
        killed = true;
        proc.kill('SIGKILL');
      }, timeout);

      proc.stdout.on('data', d => { if (output.length < 8192) output += d; });
      proc.stderr.on('data', d => { if (output.length < 8192) output += d; });

      proc.on('close', code => {
        clearTimeout(timer);
        resolve({
          ok: code === 0 && !killed,
          output: output.trim().slice(0, 8192),
          killed
        });
      });

      proc.on('error', e => {
        clearTimeout(timer);
        resolve({ ok: false, output: e.message });
      });

      proc.stdin.end();
    });
  },

  // Détecter la flamme
  detectFlame(code) {
    // Shebangs
    if (/^#!.*python/m.test(code)) return 'python';
    if (/^#!.*node/m.test(code)) return 'javascript';
    if (/^#!.*perl/m.test(code)) return 'perl';
    if (/^#!.*ruby/m.test(code)) return 'ruby';
    if (/^#!.*php/m.test(code)) return 'php';
    if (/^#!.*lua/m.test(code)) return 'lua';
    if (/^#!.*fish/m.test(code)) return 'fish';
    if (/^#!.*zsh/m.test(code)) return 'zsh';
    if (/^#!.*(bash|sh)/m.test(code)) return 'bash';

    // Patterns spécifiques
    if (/^(import|def|class)\s|^print\s*\(/m.test(code)) return 'python';
    if (/console\.log|const \w+ =|let \w+ =|=>/m.test(code)) return 'javascript';
    if (/^package\s+main/m.test(code) || /func\s+main\s*\(/m.test(code)) return 'go';
    if (/^fn\s+main/m.test(code) || /^use\s+(std|crate)/m.test(code)) return 'rust';
    if (/^#include.*</m.test(code) && /int\s+main/m.test(code)) return 'c';
    if (/^#include.*</m.test(code) && /std::|cout|cin/m.test(code)) return 'cpp';
    if (/^use\s+(strict|warnings)/m.test(code) || /\$\w+\s*=/m.test(code)) return 'perl';
    if (/^<\?php/m.test(code)) return 'php';
    if (/^require\s|^puts\s|^def\s+\w+$/m.test(code)) return 'ruby';
    if (/^local\s|^function\s+\w+\s*\(/m.test(code)) return 'lua';
    if (/^module\s+Main/m.test(code) || /^import\s+Data\./m.test(code)) return 'haskell';
    if (/^let\s+\w+\s*=/m.test(code) && /^;;/m.test(code)) return 'ocaml';
    if (/^public\s+class/m.test(code)) return 'java';
    if (/^fun\s+main\s*\(/m.test(code)) return 'kotlin';
    if (/^library\s*\(/m.test(code) || /<-\s*/m.test(code)) return 'r';
    if (/^using\s+\w+$/m.test(code) && /^function/m.test(code)) return 'julia';
    if (/^proc\s+\w+/m.test(code) || /^import\s+std\//m.test(code)) return 'nim';
    if (/^const\s+std\s*=/m.test(code) || /^pub\s+fn/m.test(code)) return 'zig';
    if (/^BEGIN\s*{/m.test(code) || /^\w+\s*=.*\$\d+/m.test(code)) return 'awk';

    return 'javascript';
  },

  // Nettoyer
  cleanup(dir) {
    try {
      const files = fs.readdirSync(dir);
      for (const f of files) fs.unlinkSync(path.join(dir, f));
      fs.rmdirSync(dir);
    } catch {}
  },

  // État du feu
  status() {
    return {
      burning: this.burning,
      maxFlames: this.maxFlames,
      recentSpells: this.history.slice(-10),
      forge: FORGE
    };
  }
};

// Créer la forge au démarrage
try { fs.mkdirSync(FORGE, { recursive: true }); } catch {}

module.exports = { Fire, FLAMES, ASHES };
