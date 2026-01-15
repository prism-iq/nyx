/**
 * Nyxx Sandbox - Protection d'exécution
 * Isolation des processus, limites ressources, protection système
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');

const TEMP_DIR = '/tmp/nyxx-exec';
const MAX_OUTPUT = 8192;
const MAX_FILE_SIZE = 1024 * 100; // 100KB max code

// Commandes et patterns INTERDITS - protection absolue
const FORBIDDEN = {
  // Destruction
  destroy: [
    /\brm\s+-[rf]/i, /\bunlink\b/i, /\brmdir\b/i, /\bshred\b/i,
    /\bdd\s+if=/i, /\bmkfs\b/i, /\bformat\b/i
  ],
  // Système
  system: [
    /\breboot\b/i, /\bshutdown\b/i, /\bhalt\b/i, /\bpoweroff\b/i,
    /\binit\s+[06]/i, /\bsystemctl\b/i, /\bservice\b/i
  ],
  // Processus
  process: [
    /\bkill\b/i, /\bpkill\b/i, /\bkillall\b/i,
    /\bfork\s*\(/i, /:\(\)\s*\{/i, /while\s+true/i
  ],
  // Privilèges
  privilege: [
    /\bsudo\b/i, /\bsu\s+-/i, /\bchmod\b/i, /\bchown\b/i,
    /\bpasswd\b/i, /\buseradd\b/i, /\buserdel\b/i
  ],
  // Réseau dangereux
  network: [
    /\bnc\s+-[el]/i, /\bncat\b/i, /\bnetcat\b/i,
    /\bcurl\s+.*-[oO]/i, /\bwget\s+/i
  ],
  // GUI/X11 (crash prevention)
  gui: [
    /\bi3-msg\b/i, /\bxdotool\b/i, /\bwmctrl\b/i,
    /\bxsetroot\b/i, /\bnotify-send\b/i, /\bzenity\b/i
  ],
  // Packages
  packages: [
    /\bapt\s+/i, /\bpacman\s+/i, /\byum\s+/i,
    /\bnpm\s+install/i, /\bpip\s+install/i
  ],
  // Python dangereux
  python: [
    /\bos\.system\b/i, /\bsubprocess\b/i, /\b__import__\b/i,
    /\beval\s*\(/i, /\bexec\s*\(/i, /\bcompile\s*\(/i
  ],
  // Node dangereux
  node: [
    /child_process/i, /\bspawn\b/i, /\bexec\b/i,
    /\brequire\s*\(\s*['"]fs['"]\s*\)/i
  ]
};

// Vérification de sécurité du code
function isCodeSafe(code, lang) {
  const lower = code.toLowerCase();

  // Vérifier toutes les catégories
  for (const [category, patterns] of Object.entries(FORBIDDEN)) {
    for (const pattern of patterns) {
      if (pattern.test(code)) {
        return { safe: false, reason: `${category}: ${pattern.source}` };
      }
    }
  }

  // Vérifications spécifiques par langage
  if (lang === 'python') {
    if (/import\s+(os|subprocess|shutil|sys)/i.test(code)) {
      // Whitelist certains usages
      if (/os\.(getcwd|path|listdir|environ)/i.test(code)) {
        // OK - lecture seule
      } else if (/os\./i.test(code)) {
        return { safe: false, reason: 'python: dangerous os usage' };
      }
    }
  }

  if (lang === 'javascript' || lang === 'node') {
    if (/require\s*\(\s*['"]child_process['"]\s*\)/i.test(code)) {
      return { safe: false, reason: 'node: child_process forbidden' };
    }
    if (/process\.exit/i.test(code)) {
      return { safe: false, reason: 'node: process.exit forbidden' };
    }
  }

  if (lang === 'bash' || lang === 'sh') {
    // Bash est le plus dangereux - restrictions strictes
    if (/[|&;]/.test(code) && /rm|kill|sudo|chmod/i.test(code)) {
      return { safe: false, reason: 'bash: dangerous pipe/chain' };
    }
  }

  return { safe: true };
}

// Création d'un environnement d'exécution isolé
function createSandbox(id) {
  const sandboxDir = path.join(TEMP_DIR, id);

  try {
    fs.mkdirSync(sandboxDir, { recursive: true, mode: 0o700 });
    return { ok: true, dir: sandboxDir };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

// Nettoyage du sandbox
function cleanupSandbox(sandboxDir) {
  try {
    const files = fs.readdirSync(sandboxDir);
    for (const file of files) {
      fs.unlinkSync(path.join(sandboxDir, file));
    }
    fs.rmdirSync(sandboxDir);
  } catch {}
}

// Configuration des langages
const LANGUAGES = {
  python: { ext: '.py', cmd: 'python3', timeout: 10000 },
  javascript: { ext: '.js', cmd: 'node', timeout: 10000 },
  bash: { ext: '.sh', cmd: 'bash', timeout: 5000 },
  ruby: { ext: '.rb', cmd: 'ruby', timeout: 10000 },
  perl: { ext: '.pl', cmd: 'perl', timeout: 10000 },
  lua: { ext: '.lua', cmd: 'lua', timeout: 10000 },
  go: { ext: '.go', cmd: 'go', args: ['run'], timeout: 15000 },
  c: { ext: '.c', compile: true, timeout: 15000 },
  rust: { ext: '.rs', compile: true, timeout: 20000 }
};

// Exécution sécurisée
async function safeExec(code, lang, options = {}) {
  const startTime = Date.now();

  // Vérification du langage
  const langConfig = LANGUAGES[lang];
  if (!langConfig) {
    return { ok: false, error: `unsupported language: ${lang}` };
  }

  // Vérification de la taille
  if (code.length > MAX_FILE_SIZE) {
    return { ok: false, error: 'code too large' };
  }

  // Vérification de sécurité
  const safeCheck = isCodeSafe(code, lang);
  if (!safeCheck.safe) {
    return { ok: false, error: `blocked: ${safeCheck.reason}`, blocked: true };
  }

  // Créer sandbox
  const id = crypto.randomBytes(8).toString('hex');
  const sandbox = createSandbox(id);
  if (!sandbox.ok) {
    return { ok: false, error: sandbox.error };
  }

  const filename = path.join(sandbox.dir, `code${langConfig.ext}`);
  const timeout = options.timeout || langConfig.timeout;

  try {
    // Écrire le code
    fs.writeFileSync(filename, code, { mode: 0o600 });

    // Préparer la commande
    let cmd, args;

    if (langConfig.compile) {
      // Langages compilés
      const binary = path.join(sandbox.dir, 'program');

      if (lang === 'c') {
        // Compiler C
        const compileResult = await runProcess('gcc', [filename, '-o', binary], {
          timeout: 10000,
          cwd: sandbox.dir
        });
        if (!compileResult.ok) {
          return { ok: false, error: compileResult.output || 'compilation failed', lang };
        }
        cmd = binary;
        args = [];
      } else if (lang === 'rust') {
        // Compiler Rust
        const compileResult = await runProcess('rustc', [filename, '-o', binary], {
          timeout: 15000,
          cwd: sandbox.dir
        });
        if (!compileResult.ok) {
          return { ok: false, error: compileResult.output || 'compilation failed', lang };
        }
        cmd = binary;
        args = [];
      }
    } else {
      cmd = langConfig.cmd;
      args = langConfig.args ? [...langConfig.args, filename] : [filename];
    }

    // Exécuter avec nice pour limiter priorité
    const result = await runProcess('nice', ['-n', '15', cmd, ...args], {
      timeout,
      cwd: sandbox.dir,
      maxBuffer: MAX_OUTPUT
    });

    return {
      ok: result.ok,
      output: result.output,
      duration: Date.now() - startTime,
      lang
    };

  } catch (e) {
    return { ok: false, error: e.message, lang };
  } finally {
    // Nettoyage
    cleanupSandbox(sandbox.dir);
  }
}

// Exécution de processus avec limites
function runProcess(cmd, args, options = {}) {
  return new Promise((resolve) => {
    const timeout = options.timeout || 10000;
    const maxBuffer = options.maxBuffer || MAX_OUTPUT;

    let output = '';
    let killed = false;
    let timer;

    const proc = spawn(cmd, args, {
      cwd: options.cwd || TEMP_DIR,
      env: {
        PATH: '/usr/bin:/bin:/usr/local/bin',
        HOME: '/tmp',
        LANG: 'C.UTF-8'
      },
      stdio: ['pipe', 'pipe', 'pipe'],
      detached: false
    });

    // Timeout
    timer = setTimeout(() => {
      killed = true;
      try {
        process.kill(-proc.pid, 'SIGKILL');
      } catch {
        proc.kill('SIGKILL');
      }
    }, timeout);

    proc.stdout.on('data', (data) => {
      if (output.length < maxBuffer) {
        output += data.toString();
      }
    });

    proc.stderr.on('data', (data) => {
      if (output.length < maxBuffer) {
        output += data.toString();
      }
    });

    proc.on('close', (code) => {
      clearTimeout(timer);

      if (output.length > maxBuffer) {
        output = output.slice(0, maxBuffer) + '\n[truncated]';
      }

      resolve({
        ok: code === 0 && !killed,
        output: output.trim(),
        exitCode: code,
        killed
      });
    });

    proc.on('error', (err) => {
      clearTimeout(timer);
      resolve({
        ok: false,
        output: err.message,
        exitCode: -1
      });
    });

    // Fermer stdin
    proc.stdin.end();
  });
}

// Détection automatique du langage
function detectLanguage(code) {
  const patterns = [
    { lang: 'python', patterns: [/^#!/.*python/m, /^(import|from|def|class)\s/m, /print\s*\(/] },
    { lang: 'javascript', patterns: [/^#!/.*node/m, /console\.log/i, /const\s+\w+\s*=/, /=>\s*\{/] },
    { lang: 'bash', patterns: [/^#!/.*(bash|sh)/m, /^\s*(echo|ls|cd|pwd)\s/m] },
    { lang: 'go', patterns: [/^package\s+\w+/m, /func\s+main\s*\(/] },
    { lang: 'rust', patterns: [/^fn\s+main/m, /^use\s+std::/m] },
    { lang: 'c', patterns: [/^#include\s*</m, /int\s+main\s*\(/] },
    { lang: 'ruby', patterns: [/^#!/.*ruby/m, /^(require|puts|def)\s/m] },
    { lang: 'perl', patterns: [/^#!/.*perl/m, /^(use strict|my\s+\$)/m] },
    { lang: 'lua', patterns: [/^local\s+\w+/, /\bend\b/] }
  ];

  for (const { lang, patterns: pats } of patterns) {
    for (const pat of pats) {
      if (pat.test(code)) return lang;
    }
  }

  return 'javascript'; // Default
}

// Initialisation
try {
  fs.mkdirSync(TEMP_DIR, { recursive: true, mode: 0o700 });
} catch {}

module.exports = {
  safeExec,
  isCodeSafe,
  detectLanguage,
  LANGUAGES,
  FORBIDDEN
};
