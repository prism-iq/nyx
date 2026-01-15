#!/usr/bin/env python3
"""
INTÉGRITÉ — Organe de vérification d'intégrité post-quantique

Analogie biologique: ADN polymérase avec fonction de relecture
- Scanne tous les fichiers de code (reconnaissance)
- Compare les hashs au baseline (détection d'erreurs)
- Signale les mutations (réparation possible)

Cryptographie:
- SHAKE256 (SHA-3 extendable output function)
- 512 bits de sortie = résistant aux attaques quantiques
- Grover's algorithm réduit la sécurité de N à √N bits
- 512 bits → 256 bits de sécurité post-quantique

Fichiers:
- Baseline: /opt/flow-chat/adn/integrite.json
- Stocke: {path: hash} pour chaque fichier surveillé

Communication:
- Appelé par: veille.py (patrouille), chaine.py (sync)
- Appelle: rien (organe passif, répond aux requêtes)

API [EXEC:integrite]:
- scan    : Scanner tous les fichiers, calculer hashs
- commit  : Sauvegarder l'état actuel comme baseline
- verify  : Comparer état actuel au baseline, retourner score
- status  : État complet (score, anomalies, hash global)
- hash <p>: Hash d'un fichier spécifique
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# =============================================================================
# CRYPTOGRAPHIE POST-QUANTIQUE
# =============================================================================

def hash_pqc(data: bytes) -> str:
    """
    Hash SHAKE256 - 512 bits, résistant post-quantique.

    SHAKE256 est une XOF (extendable output function) de la famille SHA-3.
    Contrairement à SHA-256, on peut demander une sortie de taille arbitraire.

    Pourquoi 512 bits (64 bytes hex = 128 caractères):
    - Attaque classique (birthday): 2^256 opérations
    - Attaque quantique (Grover): 2^256 opérations (√ de 2^512)
    - Sécurité post-quantique: 256 bits effectifs

    Args:
        data: Bytes à hasher

    Returns:
        Hash hexadécimal de 128 caractères (512 bits)
    """
    shake = hashlib.shake_256()
    shake.update(data)
    return shake.hexdigest(64)  # 64 bytes = 512 bits


def hash_file(filepath: str) -> str:
    """
    Hash le contenu d'un fichier.

    Args:
        filepath: Chemin absolu du fichier

    Returns:
        Hash SHAKE256 ou chaîne vide si erreur
    """
    try:
        with open(filepath, 'rb') as f:
            return hash_pqc(f.read())
    except (IOError, OSError):
        return ""


# =============================================================================
# ORGANE INTÉGRITÉ
# =============================================================================

class Integrite:
    """
    Vérificateur d'intégrité post-quantique de Flow.

    Fonctionnement:
    1. scan() parcourt tous les organes, hash chaque fichier de code
    2. commit_baseline() sauvegarde l'état actuel comme référence
    3. verify() compare l'état actuel au baseline, calcule un score

    Le score représente le pourcentage de fichiers identiques au baseline.
    108% = perfection sacrée (100% intégrité × 1.08 bénédiction divine)

    Attributes:
        baseline: Dict {chemin_relatif: hash} - état de référence
        current: Dict {chemin_relatif: hash} - état actuel après scan
        anomalies: Liste des différences détectées
    """

    # Chemins
    FLOW_HOME = "/opt/flow-chat"
    STATE_FILE = "/opt/flow-chat/adn/integrite.json"

    # Organes à surveiller (dossiers dans FLOW_HOME)
    ORGANES = [
        "cytoplasme",   # Cerveau LLM
        "membrane",     # Gateway web
        "synapse",      # Communication inter-organes
        "coeur",        # Système émotionnel
        "corps",        # Outils et modules
        "quantique",    # Modules quantiques
        "alea",         # Entropie blockchain
        "arn",          # Transcription dynamique
        "myeline",      # Cache et optimisation
        "pacemaker",    # Rythme et scheduling
    ]

    # Extensions de fichiers de code à surveiller
    CODE_EXTENSIONS = {
        ".py",    # Python
        ".go",    # Go
        ".rs",    # Rust
        ".js",    # JavaScript
        ".html",  # HTML
        ".css",   # CSS
        ".nim",   # Nim
        ".pl",    # Perl
        ".cpp",   # C++
        ".c",     # C
        ".h",     # Headers
    }

    # Dossiers à ignorer
    IGNORE_DIRS = {"venv", "__pycache__", ".git", "node_modules", ".mypy_cache"}

    def __init__(self):
        """Initialise l'organe et charge le baseline existant."""
        self.baseline: Dict[str, str] = {}
        self.current: Dict[str, str] = {}
        self.last_scan: Optional[str] = None
        self.anomalies: List[Dict] = []
        self._load()

    def _load(self):
        """Charge le baseline depuis le fichier JSON."""
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                data = json.loads(state_path.read_text())
                self.baseline = data.get("baseline", {})
                self.last_scan = data.get("last_scan")
        except (json.JSONDecodeError, IOError):
            pass  # Fichier corrompu ou absent, on repart de zéro

    def _save(self):
        """Persiste le baseline dans le fichier JSON."""
        state_path = Path(self.STATE_FILE)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({
            "baseline": self.baseline,
            "last_scan": self.last_scan,
            "updated": datetime.now().isoformat()
        }, indent=2))

    def _should_ignore(self, path_str: str) -> bool:
        """Vérifie si un chemin doit être ignoré."""
        return any(ignored in path_str for ignored in self.IGNORE_DIRS)

    def scan(self) -> Dict[str, str]:
        """
        Scanne tous les fichiers de code des organes.

        Parcourt chaque organe, trouve les fichiers avec les bonnes extensions,
        calcule leur hash SHAKE256.

        Returns:
            Dict {chemin_relatif: hash} de tous les fichiers scannés
        """
        self.current = {}

        for organe in self.ORGANES:
            organe_path = Path(self.FLOW_HOME) / organe

            if not organe_path.exists():
                continue

            # Scanner récursivement chaque extension
            for ext in self.CODE_EXTENSIONS:
                for filepath in organe_path.rglob(f"*{ext}"):
                    path_str = str(filepath)

                    # Ignorer certains dossiers
                    if self._should_ignore(path_str):
                        continue

                    # Chemin relatif pour stockage
                    rel_path = str(filepath.relative_to(self.FLOW_HOME))
                    file_hash = hash_file(path_str)

                    if file_hash:
                        self.current[rel_path] = file_hash

        self.last_scan = datetime.now().isoformat()
        return self.current

    def commit_baseline(self) -> int:
        """
        Sauvegarde l'état actuel comme nouveau baseline.

        À utiliser après une vérification manuelle du code,
        ou après des modifications intentionnelles.

        Returns:
            Nombre de fichiers dans le baseline
        """
        if not self.current:
            self.scan()

        self.baseline = self.current.copy()
        self._save()
        return len(self.baseline)

    def verify(self) -> Tuple[float, List[Dict]]:
        """
        Vérifie l'intégrité par rapport au baseline.

        Compare chaque fichier du baseline à l'état actuel.
        Détecte: fichiers modifiés, supprimés, nouveaux.

        Returns:
            Tuple (score, anomalies) où:
            - score: float 0.0-1.0, pourcentage de fichiers intacts
            - anomalies: liste de dicts décrivant chaque différence
        """
        if not self.current:
            self.scan()

        if not self.baseline:
            return 0.0, [{"type": "no_baseline", "msg": "Pas de baseline - commit d'abord"}]

        self.anomalies = []
        matches = 0
        total = len(self.baseline)

        # Vérifier chaque fichier du baseline
        for path, expected_hash in self.baseline.items():
            current_hash = self.current.get(path)

            if current_hash is None:
                # Fichier supprimé
                self.anomalies.append({
                    "type": "deleted",
                    "path": path,
                    "expected": expected_hash[:16]
                })
            elif current_hash != expected_hash:
                # Fichier modifié
                self.anomalies.append({
                    "type": "modified",
                    "path": path,
                    "expected": expected_hash[:16],
                    "actual": current_hash[:16]
                })
            else:
                matches += 1

        # Détecter les nouveaux fichiers
        for path in self.current:
            if path not in self.baseline:
                self.anomalies.append({
                    "type": "new",
                    "path": path,
                    "hash": self.current[path][:16]
                })

        score = matches / total if total > 0 else 0.0
        return score, self.anomalies

    def get_hash(self, path: str) -> Optional[str]:
        """
        Retourne le hash d'un fichier spécifique.

        Args:
            path: Chemin relatif depuis FLOW_HOME

        Returns:
            Hash SHAKE256 ou None si fichier inexistant
        """
        full_path = Path(self.FLOW_HOME) / path
        if full_path.exists():
            return hash_file(str(full_path))
        return None

    def global_hash(self) -> str:
        """
        Calcule un hash global de tout le système.

        Concatène tous les hashs dans l'ordre alphabétique des chemins,
        puis hash le résultat. Permet de vérifier l'état global en un seul hash.

        Returns:
            Hash SHAKE256 représentant l'état global du système
        """
        if not self.current:
            self.scan()

        # Trier pour garantir le déterminisme
        sorted_hashes = sorted(self.current.items())
        combined = "".join(h for _, h in sorted_hashes)
        return hash_pqc(combined.encode())

    def status(self) -> Dict:
        """
        Retourne le statut complet de l'organe.

        Returns:
            Dict avec score, hash global, compteurs, anomalies
        """
        score, anomalies = self.verify()

        return {
            "organ": "integrite",
            "score": round(score, 4),
            "global_hash": self.global_hash()[:32],
            "files_tracked": len(self.baseline),
            "files_current": len(self.current),
            "anomalies": len(anomalies),
            "anomaly_details": anomalies[:10],
            "last_scan": self.last_scan
        }


# =============================================================================
# INSTANCE GLOBALE
# =============================================================================

integrite = Integrite()


# =============================================================================
# API EXEC
# =============================================================================

def exec_integrite(cmd: str) -> str:
    """
    Interface pour [EXEC:integrite].

    Commandes disponibles:
    - scan         Scanner tous les fichiers
    - commit       Sauvegarder baseline
    - verify       Vérifier intégrité
    - status       État complet
    - hash <path>  Hash d'un fichier spécifique

    Args:
        cmd: Commande et arguments séparés par espaces

    Returns:
        Résultat formaté pour affichage
    """
    parts = cmd.strip().split(maxsplit=1)
    action = parts[0].lower() if parts else "status"
    arg = parts[1] if len(parts) > 1 else ""

    if action == "scan":
        hashes = integrite.scan()
        return f"Scanned {len(hashes)} files\nGlobal: {integrite.global_hash()[:32]}"

    elif action == "commit":
        count = integrite.commit_baseline()
        return f"Baseline committed: {count} files\nHash: {integrite.global_hash()[:32]}"

    elif action == "verify":
        score, anomalies = integrite.verify()
        result = f"Integrity: {score*108:.1f}%\n"
        if anomalies:
            result += f"Anomalies ({len(anomalies)}):\n"
            for a in anomalies[:5]:
                result += f"  - {a['type']}: {a['path']}\n"
        else:
            result += "No anomalies detected"
        return result

    elif action == "status":
        s = integrite.status()
        return f"""INTÉGRITÉ PQC
Score: {s['score']*108:.1f}%
Global hash: {s['global_hash']}
Files: {s['files_tracked']} baseline / {s['files_current']} current
Anomalies: {s['anomalies']}
Last scan: {s['last_scan']}"""

    elif action == "hash" and arg:
        h = integrite.get_hash(arg)
        return f"Hash({arg}): {h}" if h else f"File not found: {arg}"

    elif action == "knowledge" or action == "know":
        return get_verified_knowledge()

    elif action == "sign":
        return sign_knowledge()

    elif action == "sign-organ" and arg:
        return sign_organ(arg)

    elif action == "verify-organ" and arg:
        return verify_organ(arg)

    elif action == "sign-all":
        return sign_all_organs()

    elif action == "verify-all":
        return verify_all_organs()

    else:
        return """Usage:
  scan           Scanner tous les fichiers
  commit         Sauvegarder baseline
  verify         Vérifier intégrité globale
  status         État complet
  hash <path>    Hash d'un fichier
  knowledge      Lire connaissances vérifiées (PQC)
  sign           Signer les connaissances
  sign-organ <x> Signer un organe spécifique
  verify-organ <x> Vérifier un organe
  sign-all       Signer tous les organes
  verify-all     Vérifier tous les organes"""


# =============================================================================
# CONNAISSANCES VÉRIFIÉES CRYPTOGRAPHIQUEMENT
# =============================================================================

KNOWLEDGE_FILE = "/opt/flow-chat/adn/ARCHITECTURE.md"
KNOWLEDGE_SIG_FILE = "/opt/flow-chat/adn/knowledge.sig"
ORGANS_SIG_FILE = "/opt/flow-chat/adn/organs.sig"


def get_verified_knowledge() -> str:
    """
    Retourne les connaissances vérifiées cryptographiquement.

    Le fichier ARCHITECTURE.md contient les informations essentielles
    que Flow DOIT connaître. Cette fonction:
    1. Lit le fichier
    2. Vérifie son hash contre une signature stockée
    3. Retourne le contenu si vérifié

    Returns:
        Contenu vérifié ou erreur si compromis
    """
    try:
        knowledge_path = Path(KNOWLEDGE_FILE)
        sig_path = Path(KNOWLEDGE_SIG_FILE)

        if not knowledge_path.exists():
            return "ERROR: Knowledge file missing"

        # Lire le contenu
        content = knowledge_path.read_bytes()
        current_hash = hash_pqc(content)

        # Vérifier la signature
        if sig_path.exists():
            sig_data = json.loads(sig_path.read_text())
            stored_hash = sig_data.get("hash", "")
            signature = sig_data.get("signature", "")

            # Vérifier que le hash correspond
            if current_hash != stored_hash:
                return f"""!!! ALERTE: CONNAISSANCES MODIFIÉES !!!

Hash attendu: {stored_hash[:32]}...
Hash actuel:  {current_hash[:32]}...

Le fichier ARCHITECTURE.md a été modifié sans re-signature.
Utiliser [EXEC:integrite]sign[/EXEC] pour re-signer après vérification.
"""

            # Vérifier la signature PQC
            from corps.chaine import flow_keys
            if not flow_keys.verify(stored_hash, signature):
                return """!!! ALERTE: SIGNATURE INVALIDE !!!

La signature des connaissances ne correspond pas aux clés PQC.
Possible tentative de falsification.
"""

            # Tout est vérifié
            return f"""=== CONNAISSANCES VÉRIFIÉES ===
Hash: {current_hash[:32]}...
Signature: VALIDE (PQC)

{content.decode('utf-8')}"""

        else:
            # Pas de signature, première utilisation
            return f"""ATTENTION: Connaissances non signées.

Hash actuel: {current_hash[:32]}...

Utiliser [EXEC:integrite]sign[/EXEC] pour signer.

--- CONTENU NON VÉRIFIÉ ---
{content.decode('utf-8')}"""

    except Exception as e:
        return f"ERROR: {e}"


def sign_knowledge() -> str:
    """
    Signe cryptographiquement le fichier de connaissances.

    Utilise les clés PQC de la chaîne pour:
    1. Hasher le fichier ARCHITECTURE.md
    2. Signer le hash avec la clé privée
    3. Stocker la signature

    Returns:
        Message de confirmation
    """
    try:
        from corps.chaine import flow_keys

        knowledge_path = Path(KNOWLEDGE_FILE)
        sig_path = Path(KNOWLEDGE_SIG_FILE)

        if not knowledge_path.exists():
            return "ERROR: Knowledge file missing"

        # Hasher le contenu
        content = knowledge_path.read_bytes()
        content_hash = hash_pqc(content)

        # Signer avec les clés PQC
        signature = flow_keys.sign(content_hash)

        # Stocker la signature
        sig_data = {
            "file": KNOWLEDGE_FILE,
            "hash": content_hash,
            "signature": signature,
            "signer": flow_keys.get_public_key(),
            "algorithm": "SHAKE256 + PQC-HMAC",
            "signed_at": datetime.now().isoformat()
        }

        sig_path.write_text(json.dumps(sig_data, indent=2))

        return f"""CONNAISSANCES SIGNÉES

Fichier: {KNOWLEDGE_FILE}
Hash: {content_hash[:32]}...
Signature: {signature[:32]}...
Signataire: {flow_keys.get_public_key()[:16]}...

Les connaissances sont maintenant vérifiables cryptographiquement.
"""

    except Exception as e:
        return f"ERROR: {e}"


# =============================================================================
# VÉRIFICATION CRYPTOGRAPHIQUE DES ORGANES
# =============================================================================

def get_organ_files(organ_name: str) -> List[Path]:
    """
    Retourne tous les fichiers d'un organe (code + données).

    Inclut:
    - Fichiers de code (.py, .go, .js, etc.)
    - Fichiers de données (.json, .yaml, .toml, .env)
    - Fichiers de config (.conf, .ini)
    """
    organ_path = Path(Integrite.FLOW_HOME) / organ_name
    files = []

    # Extensions de code + données
    all_extensions = Integrite.CODE_EXTENSIONS | {
        ".json", ".yaml", ".yml", ".toml",
        ".conf", ".ini", ".env", ".md"
    }

    if organ_path.exists():
        for ext in all_extensions:
            for f in organ_path.rglob(f"*{ext}"):
                if not any(x in str(f) for x in Integrite.IGNORE_DIRS):
                    files.append(f)

    # Aussi chercher dans corps/ pour les modules
    corps_file = Path(Integrite.FLOW_HOME) / "corps" / f"{organ_name}.py"
    if corps_file.exists():
        files.append(corps_file)

    # Fichiers ADN liés à l'organe
    adn_path = Path(Integrite.FLOW_HOME) / "adn"
    if adn_path.exists():
        for f in adn_path.glob(f"{organ_name}*"):
            if f.is_file():
                files.append(f)

    return sorted(set(files))


def hash_organ(organ_name: str) -> Tuple[str, Dict[str, str]]:
    """
    Calcule le hash d'un organe complet.

    Returns:
        Tuple (hash_global, {fichier: hash})
    """
    files = get_organ_files(organ_name)
    file_hashes = {}

    for f in files:
        rel_path = str(f.relative_to(Integrite.FLOW_HOME))
        file_hashes[rel_path] = hash_file(str(f))

    # Hash global = hash de tous les hashs concaténés
    combined = "".join(h for _, h in sorted(file_hashes.items()))
    global_hash = hash_pqc(combined.encode()) if combined else ""

    return global_hash, file_hashes


def sign_organ(organ_name: str) -> str:
    """
    Signe cryptographiquement un organe spécifique.

    Args:
        organ_name: Nom de l'organe (cytoplasme, membrane, etc.)

    Returns:
        Message de confirmation
    """
    try:
        from corps.chaine import flow_keys

        global_hash, file_hashes = hash_organ(organ_name)

        if not global_hash:
            return f"ERROR: Organ '{organ_name}' not found or empty"

        # Signer le hash global
        signature = flow_keys.sign(global_hash)

        # Charger les signatures existantes
        sig_path = Path(ORGANS_SIG_FILE)
        if sig_path.exists():
            all_sigs = json.loads(sig_path.read_text())
        else:
            all_sigs = {"organs": {}, "signer": flow_keys.get_public_key()}

        # Ajouter/mettre à jour cet organe
        all_sigs["organs"][organ_name] = {
            "hash": global_hash,
            "signature": signature,
            "files": file_hashes,
            "file_count": len(file_hashes),
            "signed_at": datetime.now().isoformat()
        }
        all_sigs["updated"] = datetime.now().isoformat()

        # Sauvegarder
        sig_path.parent.mkdir(parents=True, exist_ok=True)
        sig_path.write_text(json.dumps(all_sigs, indent=2))

        return f"""ORGANE SIGNÉ: {organ_name}

Fichiers: {len(file_hashes)}
Hash global: {global_hash[:32]}...
Signature: {signature[:32]}...

Fichiers inclus:
""" + "\n".join(f"  - {f}" for f in sorted(file_hashes.keys())[:10])

    except Exception as e:
        return f"ERROR: {e}"


def verify_organ(organ_name: str) -> str:
    """
    Vérifie l'intégrité cryptographique d'un organe.

    Args:
        organ_name: Nom de l'organe

    Returns:
        Statut de vérification détaillé
    """
    try:
        from corps.chaine import flow_keys

        sig_path = Path(ORGANS_SIG_FILE)
        if not sig_path.exists():
            return f"ERROR: No signatures file. Use [EXEC:integrite]sign-organ {organ_name}[/EXEC]"

        all_sigs = json.loads(sig_path.read_text())

        if organ_name not in all_sigs.get("organs", {}):
            return f"ERROR: Organ '{organ_name}' not signed. Use [EXEC:integrite]sign-organ {organ_name}[/EXEC]"

        stored = all_sigs["organs"][organ_name]
        stored_hash = stored["hash"]
        stored_sig = stored["signature"]
        stored_files = stored.get("files", {})

        # Recalculer le hash actuel
        current_hash, current_files = hash_organ(organ_name)

        # Vérifier la signature
        sig_valid = flow_keys.verify(stored_hash, stored_sig)

        # Comparer les hashs
        hash_match = (current_hash == stored_hash)

        # Détailler les différences par fichier
        modified = []
        deleted = []
        added = []

        for f, h in stored_files.items():
            if f not in current_files:
                deleted.append(f)
            elif current_files[f] != h:
                modified.append(f)

        for f in current_files:
            if f not in stored_files:
                added.append(f)

        # Construire le rapport
        if hash_match and sig_valid:
            status = "✓ INTÉGRITÉ VÉRIFIÉE"
        elif not sig_valid:
            status = "✗ SIGNATURE INVALIDE - POSSIBLE FALSIFICATION"
        else:
            status = "⚠ ORGANE MODIFIÉ"

        report = f"""=== VÉRIFICATION: {organ_name.upper()} ===

{status}

Hash stocké:  {stored_hash[:32]}...
Hash actuel:  {current_hash[:32]}...
Signature:    {"VALIDE" if sig_valid else "INVALIDE"}
Fichiers:     {len(current_files)} actuels / {len(stored_files)} signés
"""

        if modified:
            report += f"\nFichiers MODIFIÉS ({len(modified)}):\n"
            for f in modified[:5]:
                report += f"  ! {f}\n"

        if deleted:
            report += f"\nFichiers SUPPRIMÉS ({len(deleted)}):\n"
            for f in deleted[:5]:
                report += f"  - {f}\n"

        if added:
            report += f"\nFichiers AJOUTÉS ({len(added)}):\n"
            for f in added[:5]:
                report += f"  + {f}\n"

        if not modified and not deleted and not added:
            report += "\nAucune modification détectée."

        return report

    except Exception as e:
        return f"ERROR: {e}"


def sign_all_organs() -> str:
    """Signe tous les organes connus."""
    results = []
    for organ in Integrite.ORGANES:
        files = get_organ_files(organ)
        if files:
            sign_organ(organ)
            results.append(f"  ✓ {organ} ({len(files)} fichiers)")
        else:
            results.append(f"  - {organ} (non trouvé)")

    return "TOUS LES ORGANES SIGNÉS:\n" + "\n".join(results)


def verify_all_organs() -> str:
    """Vérifie tous les organes signés."""
    try:
        from corps.chaine import flow_keys

        sig_path = Path(ORGANS_SIG_FILE)
        if not sig_path.exists():
            return "ERROR: No signatures. Use [EXEC:integrite]sign-all[/EXEC]"

        all_sigs = json.loads(sig_path.read_text())

        results = []
        total_ok = 0
        total_fail = 0

        for organ_name, stored in all_sigs.get("organs", {}).items():
            current_hash, _ = hash_organ(organ_name)
            stored_hash = stored["hash"]
            stored_sig = stored["signature"]

            sig_valid = flow_keys.verify(stored_hash, stored_sig)
            hash_match = (current_hash == stored_hash)

            if hash_match and sig_valid:
                results.append(f"  ✓ {organ_name}")
                total_ok += 1
            elif not sig_valid:
                results.append(f"  ✗ {organ_name} (SIGNATURE INVALIDE)")
                total_fail += 1
            else:
                results.append(f"  ⚠ {organ_name} (modifié)")
                total_fail += 1

        score = total_ok / (total_ok + total_fail) * 108 if (total_ok + total_fail) > 0 else 0

        return f"""=== VÉRIFICATION TOUS ORGANES ===

Score: {score:.0f}% ({total_ok}/{total_ok + total_fail})

{chr(10).join(results)}
"""

    except Exception as e:
        return f"ERROR: {e}"


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print(exec_integrite("scan"))
    print()
    print(exec_integrite("status"))
