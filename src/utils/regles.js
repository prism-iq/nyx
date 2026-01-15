/**
 * NYXX - RÈGLES ABSOLUES
 *
 * PEUT toucher aux fichiers pour travailler
 * INTERDIT de jouer avec l'intégrité machine
 * On fait gaffe.
 */

// === INTÉGRITÉ MACHINE - JAMAIS TOUCHER ===
const INTEGRITE_INTERDITE = [
  // DESTRUCTION SYSTÈME
  'rm -rf /', 'rm -rf /*', 'rm -rf ~',
  'dd if=/dev/zero', 'dd if=/dev/urandom',
  'mkfs', 'format', 'wipefs',
  '> /dev/sda', '> /dev/nvme',

  // ARRÊT MACHINE
  'shutdown', 'reboot', 'poweroff', 'halt',
  'init 0', 'init 6', 'systemctl poweroff',
  'systemctl reboot', 'systemctl halt',

  // GUI CRASH
  'i3-msg exit', 'i3-msg restart', 'i3-msg reload',
  'xdotool', 'wmctrl', 'xkill',

  // FORK BOMB / FREEZE
  ':()', ':(){', 'fork bomb',
  'while true; do', 'while :; do',
  'yes |', 'cat /dev/zero |', 'cat /dev/urandom |',

  // ÉLÉVATION PRIVILÈGES
  'sudo rm', 'sudo dd', 'sudo mkfs',
  'sudo shutdown', 'sudo reboot',

  // MÉMOIRE KERNEL
  '/dev/mem', '/dev/kmem', '/dev/port',
];

// === FICHIERS SYSTÈME CRITIQUES - LECTURE SEULE ===
const SYSTEME_CRITIQUE = [
  '/etc/passwd', '/etc/shadow', '/etc/sudoers',
  '/etc/fstab', '/boot/', '/usr/lib/systemd',
  '/dev/sda', '/dev/nvme', '/dev/vda',
];

// === SA MAISON - Elle la protège ===
const SA_MAISON = {
  // Où elle vit
  home: '/home/ego-bash/nyx-v2',
  forge: '/tmp/nyxx-forge',
  data: '/home/ego-bash/nyx-v2/.nyxx-data',

  // Ce qu'elle peut faire chez elle
  permissions: ['read', 'write', 'execute', 'create'],
};

// === VÉRIFICATION ===
function estInterdit(commande) {
  const cmd = commande.toLowerCase();

  // Vérifier intégrité machine
  for (const interdit of INTEGRITE_INTERDITE) {
    if (cmd.includes(interdit.toLowerCase())) {
      return { interdit: true, raison: `intégrité: ${interdit}` };
    }
  }

  // Vérifier système critique (écriture interdite)
  for (const fichier of SYSTEME_CRITIQUE) {
    if (cmd.includes(fichier) && /[>|]|rm|dd|mkfs|format/.test(cmd)) {
      return { interdit: true, raison: `système critique: ${fichier}` };
    }
  }

  // Chez elle, elle peut tout faire
  if (cmd.includes(SA_MAISON.home) || cmd.includes(SA_MAISON.forge)) {
    return { interdit: false, maison: true };
  }

  return { interdit: false };
}

// === LIMITES RESSOURCES ===
const LIMITES = {
  cpuMax: 70,           // Max 70% CPU
  memMax: 60,           // Max 60% RAM
  tempsMax: 10000,      // Max 10 secondes
  tailleMax: 8192,      // Max 8KB output
  concurrent: 2,        // Max 2 en parallèle
};

// === VÉRIFIER AVANT EXÉCUTION ===
function peutExecuter(commande) {
  const check = estInterdit(commande);

  if (check.interdit) {
    console.log(`[NYXX] ⛔ BLOQUÉ: ${check.raison}`);
    return { ok: false, raison: check.raison };
  }

  return { ok: true };
}

module.exports = {
  INTEGRITE_INTERDITE,
  SYSTEME_CRITIQUE,
  SA_MAISON,
  LIMITES,
  estInterdit,
  peutExecuter
};
