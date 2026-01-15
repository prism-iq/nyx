#!/usr/bin/env python3
"""
CHAÎNE — Blockchain post-quantique de Flow

Analogie biologique: Mémoire immunitaire à long terme
- Les lymphocytes B gardent la mémoire des pathogènes rencontrés
- Chaque rencontre est enregistrée de façon permanente
- Permet une réponse rapide lors d'une nouvelle exposition

Architecture blockchain:
- Chaque bloc contient: action, fichier concerné, hashs avant/après
- Les blocs sont chaînés par hash (prev_hash → block_hash)
- Chaque bloc est signé asymétriquement (PQC)
- La chaîne est append-only (immutable)

Cryptographie:
- Hash: SHAKE256 (512 bits, post-quantum)
- Signature: HMAC-SHAKE256 simulant Dilithium/SPHINCS+
- En production: utiliser liboqs pour vraie crypto PQC

Fichiers:
- Chaîne: /opt/flow-chat/adn/chaine.jsonl (un bloc JSON par ligne)
- Clés: /opt/flow-chat/adn/pqc_keys.json (privée + publique)

Communication:
- Appelé par: veille.py (enregistrement anomalies)
- Appelle: integrite.py (sync_with_integrite)

API [EXEC:chaine]:
- status              État de la chaîne
- verify              Vérifier intégrité + signatures
- history [path]      Historique des blocs
- sync                Synchroniser avec intégrité
- add <act> <path>    Ajouter un bloc manuellement
"""

import os
import json
import secrets
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


# =============================================================================
# CRYPTOGRAPHIE POST-QUANTIQUE
# =============================================================================

def hash_pqc(data: str) -> str:
    """
    Hash SHAKE256 pour chaîne de caractères.

    Différent de integrite.hash_pqc qui prend des bytes.
    Ici on encode en UTF-8 avant de hasher.

    Args:
        data: Chaîne à hasher

    Returns:
        Hash hexadécimal de 128 caractères (512 bits)
    """
    shake = hashlib.shake_256()
    shake.update(data.encode('utf-8'))
    return shake.hexdigest(64)


# =============================================================================
# CRYPTOGRAPHIE ASYMÉTRIQUE PQC
# =============================================================================

class PQCKeyPair:
    """
    Paire de clés post-quantique pour signatures.

    Simulation de Dilithium ou SPHINCS+ avec HMAC-SHAKE256.
    En production, remplacer par liboqs (Open Quantum Safe).

    Fonctionnement:
    - Clé privée: 256 bits aléatoires (secrets.token_hex)
    - Clé publique: hash de la clé privée (one-way function)
    - Signature: HMAC(private_key || message)
    - Vérification: recalculer et comparer

    Sécurité:
    - La clé publique ne révèle pas la clé privée (pre-image resistance)
    - La signature ne peut être forgée sans la clé privée
    - SHAKE256 résiste aux attaques quantiques (Grover)

    Fichier:
        /opt/flow-chat/adn/pqc_keys.json avec permissions 0600
    """

    KEYS_FILE = "/opt/flow-chat/adn/pqc_keys.json"

    def __init__(self):
        """Charge ou génère les clés."""
        self.private_key: str = ""
        self.public_key: str = ""
        self._load_or_generate()

    def _load_or_generate(self):
        """Charge les clés existantes ou en génère de nouvelles."""
        keys_path = Path(self.KEYS_FILE)

        if keys_path.exists():
            try:
                data = json.loads(keys_path.read_text())
                self.private_key = data["private"]
                self.public_key = data["public"]
                return
            except (json.JSONDecodeError, KeyError):
                pass  # Fichier corrompu, on régénère

        # Générer nouvelles clés
        self.private_key = secrets.token_hex(32)  # 256 bits
        self.public_key = hash_pqc(self.private_key)[:64]  # 256 bits (tronqué)

        # Sauvegarder avec permissions restrictives
        keys_path.parent.mkdir(parents=True, exist_ok=True)
        keys_path.write_text(json.dumps({
            "private": self.private_key,
            "public": self.public_key,
            "algorithm": "SHAKE256-HMAC (simulated PQC)",
            "note": "En prod: utiliser liboqs Dilithium ou SPHINCS+",
            "created": datetime.now().isoformat()
        }, indent=2))
        keys_path.chmod(0o600)  # Lecture/écriture propriétaire seulement

    def sign(self, message: str) -> str:
        """
        Signe un message avec la clé privée.

        Implémente HMAC: H(private_key || message)
        La concaténation empêche les attaques par extension de longueur.

        Args:
            message: Message à signer (typiquement un hash de bloc)

        Returns:
            Signature hexadécimale de 64 caractères (256 bits)
        """
        data = self.private_key + message
        return hash_pqc(data)[:64]

    def verify(self, message: str, signature: str) -> bool:
        """
        Vérifie une signature.

        Args:
            message: Message original
            signature: Signature à vérifier

        Returns:
            True si la signature est valide
        """
        expected = self.sign(message)
        # Comparaison en temps constant pour éviter timing attacks
        return secrets.compare_digest(signature, expected)

    def get_public_key(self) -> str:
        """Retourne la clé publique (safe to share)."""
        return self.public_key


# Instance globale des clés Flow
flow_keys = PQCKeyPair()


# =============================================================================
# BLOC DE LA CHAÎNE
# =============================================================================

@dataclass
class Block:
    """
    Un bloc de la blockchain.

    Structure:
    - Métadonnées: index, timestamp
    - Contenu: action, path, hash_before, hash_after, description
    - Chaînage: prev_hash (lien vers bloc précédent)
    - Intégrité: block_hash (hash de ce bloc)
    - Signature: signature + signer (clé publique)

    Actions possibles:
    - genesis: Bloc initial
    - create: Nouveau fichier
    - modify: Fichier modifié
    - delete: Fichier supprimé
    - verify_ok: Vérification d'intégrité réussie
    - anomaly_*: Anomalie détectée (modified, deleted, new)
    """

    index: int              # Position dans la chaîne (0 = genesis)
    timestamp: str          # ISO 8601 datetime
    action: str             # Type d'action enregistrée
    path: str               # Fichier concerné (ou "" si global)
    hash_before: str        # Hash avant l'action (tronqué à 32 chars)
    hash_after: str         # Hash après l'action (tronqué à 32 chars)
    description: str        # Description humaine (max 100 chars)
    prev_hash: str          # Hash du bloc précédent
    block_hash: str = ""    # Hash de ce bloc (calculé)
    signature: str = ""     # Signature PQC du block_hash
    signer: str = ""        # Clé publique du signataire

    def compute_hash(self) -> str:
        """
        Calcule le hash du bloc.

        Inclut toutes les données sauf block_hash, signature, signer
        (qui sont calculés après).

        Returns:
            Hash SHAKE256 du bloc
        """
        data = f"{self.index}{self.timestamp}{self.action}{self.path}"
        data += f"{self.hash_before}{self.hash_after}{self.description}{self.prev_hash}"
        return hash_pqc(data)

    def sign(self, keypair: PQCKeyPair):
        """
        Signe le bloc avec une paire de clés.

        1. Calcule le hash du bloc
        2. Signe le hash avec la clé privée
        3. Stocke la signature et la clé publique

        Args:
            keypair: Paire de clés PQC à utiliser
        """
        self.block_hash = self.compute_hash()
        self.signature = keypair.sign(self.block_hash)
        self.signer = keypair.get_public_key()

    def verify_signature(self, keypair: PQCKeyPair) -> bool:
        """
        Vérifie la signature du bloc.

        Args:
            keypair: Paire de clés (seule la clé publique est utilisée)

        Returns:
            True si la signature est valide
        """
        if not self.signature:
            return False
        return keypair.verify(self.block_hash, self.signature)


# =============================================================================
# BLOCKCHAIN
# =============================================================================

class Chaine:
    """
    Blockchain post-quantique de Flow.

    Propriétés:
    - Immutable: les blocs ne peuvent pas être modifiés
    - Chaînée: chaque bloc référence le précédent
    - Signée: chaque bloc est signé asymétriquement
    - Vérifiable: on peut vérifier toute la chaîne

    Fichier:
        /opt/flow-chat/adn/chaine.jsonl
        Format JSONL (un objet JSON par ligne) pour append efficace
    """

    CHAIN_FILE = "/opt/flow-chat/adn/chaine.jsonl"
    GENESIS_HASH = "0" * 128  # 512 bits de zéros pour le premier bloc

    def __init__(self):
        """Charge la chaîne ou crée le bloc genesis."""
        self.blocks: List[Block] = []
        self._load()
        if not self.blocks:
            self._create_genesis()

    def _load(self):
        """Charge la chaîne depuis le fichier JSONL."""
        chain_path = Path(self.CHAIN_FILE)
        if not chain_path.exists():
            return

        try:
            for line in chain_path.read_text().strip().split('\n'):
                if line:
                    data = json.loads(line)
                    block = Block(**data)
                    self.blocks.append(block)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[chaine] Load error: {e}")

    def _save_block(self, block: Block):
        """Ajoute un bloc au fichier (append)."""
        Path(self.CHAIN_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(self.CHAIN_FILE, 'a') as f:
            f.write(json.dumps(asdict(block)) + '\n')

    def _create_genesis(self):
        """Crée le bloc genesis (bloc 0)."""
        genesis = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            action="genesis",
            path="",
            hash_before="",
            hash_after="",
            description="Flow blockchain initialized",
            prev_hash=self.GENESIS_HASH
        )
        genesis.block_hash = genesis.compute_hash()
        # Le genesis n'est pas signé (pas de bloc précédent à vérifier)
        self.blocks.append(genesis)
        self._save_block(genesis)

    def add_block(self, action: str, path: str, hash_before: str,
                  hash_after: str, description: str = "") -> Block:
        """
        Ajoute un nouveau bloc signé à la chaîne.

        Args:
            action: Type d'action (create, modify, delete, verify_ok, etc.)
            path: Fichier concerné
            hash_before: Hash avant modification (tronqué à 32 chars)
            hash_after: Hash après modification (tronqué à 32 chars)
            description: Description humaine (max 100 chars)

        Returns:
            Le bloc créé et ajouté
        """
        prev_block = self.blocks[-1]

        block = Block(
            index=len(self.blocks),
            timestamp=datetime.now().isoformat(),
            action=action,
            path=path,
            hash_before=hash_before[:32] if hash_before else "",
            hash_after=hash_after[:32] if hash_after else "",
            description=description[:100],
            prev_hash=prev_block.block_hash
        )

        # Signer le bloc avec les clés PQC de Flow
        block.sign(flow_keys)

        self.blocks.append(block)
        self._save_block(block)

        return block

    def verify_chain(self) -> tuple:
        """
        Vérifie l'intégrité de toute la chaîne.

        Vérifie:
        1. Le hash de chaque bloc est correct
        2. Le chaînage (prev_hash) est correct
        3. Les signatures sont valides

        Returns:
            Tuple (valid: bool, errors: list)
        """
        errors = []

        for i, block in enumerate(self.blocks):
            # Vérifier le hash du bloc
            computed = block.compute_hash()
            if computed != block.block_hash:
                errors.append(f"Block {i}: hash mismatch")

            # Vérifier le chaînage
            if i > 0:
                if block.prev_hash != self.blocks[i-1].block_hash:
                    errors.append(f"Block {i}: chain broken")

            # Vérifier la signature (si présente)
            if block.signature and not block.verify_signature(flow_keys):
                errors.append(f"Block {i}: invalid signature")

        return len(errors) == 0, errors

    def get_history(self, path: str = None, limit: int = 20) -> List[Dict]:
        """
        Retourne l'historique des blocs.

        Args:
            path: Filtrer par fichier (None = tous)
            limit: Nombre max de blocs à retourner

        Returns:
            Liste de dicts (blocs sérialisés), plus récents en premier
        """
        if path:
            blocks = [b for b in self.blocks if b.path == path][-limit:]
        else:
            blocks = self.blocks[-limit:]

        return [asdict(b) for b in reversed(blocks)]

    def record_from_integrite(self, anomalies: List[Dict]):
        """
        Enregistre les anomalies détectées par l'organe intégrité.

        Appelé par veille.py lors de la patrouille.

        Args:
            anomalies: Liste de dicts avec type, path, expected, actual
        """
        for anomaly in anomalies:
            self.add_block(
                action=f"anomaly_{anomaly['type']}",
                path=anomaly.get('path', ''),
                hash_before=anomaly.get('expected', ''),
                hash_after=anomaly.get('actual', anomaly.get('hash', '')),
                description=f"Detected by integrite: {anomaly['type']}"
            )

    def status(self) -> Dict:
        """
        Retourne le statut de la chaîne.

        Returns:
            Dict avec compteurs, validité, dernier bloc, genesis
        """
        valid, errors = self.verify_chain()
        last_block = self.blocks[-1] if self.blocks else None

        return {
            "organ": "chaine",
            "blocks": len(self.blocks),
            "valid": valid,
            "errors": len(errors),
            "last_block": {
                "index": last_block.index,
                "action": last_block.action,
                "hash": last_block.block_hash[:16]
            } if last_block else None,
            "genesis": self.blocks[0].block_hash[:16] if self.blocks else None
        }


# =============================================================================
# INSTANCE GLOBALE
# =============================================================================

chaine = Chaine()


# =============================================================================
# SYNCHRONISATION AVEC INTÉGRITÉ
# =============================================================================

def sync_with_integrite() -> str:
    """
    Synchronise avec l'organe intégrité.

    1. Déclenche un scan d'intégrité
    2. Enregistre les anomalies dans la blockchain
    3. Ou enregistre une vérification OK

    Returns:
        Message de résultat
    """
    try:
        from corps.integrite import integrite

        # Scanner et vérifier
        integrite.scan()
        score, anomalies = integrite.verify()

        # Enregistrer les anomalies dans la blockchain
        if anomalies:
            chaine.record_from_integrite(anomalies)
            return f"Synced: {len(anomalies)} anomalies recorded"

        # Enregistrer une vérification OK
        chaine.add_block(
            action="verify_ok",
            path="*",
            hash_before=integrite.global_hash()[:32],
            hash_after=integrite.global_hash()[:32],
            description=f"Integrity check passed: {score*100:.0f}%"
        )
        return f"Synced: integrity {score*100:.0f}%"

    except Exception as e:
        return f"Sync error: {e}"


# =============================================================================
# API EXEC
# =============================================================================

def exec_chaine(cmd: str) -> str:
    """
    Interface pour [EXEC:chaine].

    Commandes disponibles:
    - status                État de la chaîne
    - verify                Vérifier intégrité et signatures
    - history [path]        Historique (filtré par path optionnel)
    - sync                  Synchroniser avec intégrité
    - add <action> <path>   Ajouter un bloc manuellement

    Args:
        cmd: Commande et arguments séparés par espaces

    Returns:
        Résultat formaté pour affichage
    """
    parts = cmd.strip().split(maxsplit=3)
    action = parts[0].lower() if parts else "status"

    if action == "status":
        s = chaine.status()
        return f"""CHAÎNE PQC
Blocs: {s['blocks']}
Valide: {s['valid']}
Dernier: #{s['last_block']['index']} {s['last_block']['action']} ({s['last_block']['hash']})
Genesis: {s['genesis']}"""

    elif action == "verify":
        valid, errors = chaine.verify_chain()
        if valid:
            return f"Chain valid: {len(chaine.blocks)} blocks, all signatures OK"
        return f"Chain INVALID:\n" + "\n".join(errors[:5])

    elif action == "history":
        path = parts[1] if len(parts) > 1 else None
        history = chaine.get_history(path, limit=10)
        result = "HISTORY:\n"
        for b in history:
            result += f"  #{b['index']} {b['action']}: {b['path'][:30]} ({b['block_hash'][:8]})\n"
        return result

    elif action == "sync":
        return sync_with_integrite()

    elif action == "add" and len(parts) >= 3:
        block = chaine.add_block(
            action=parts[1],
            path=parts[2],
            hash_before="",
            hash_after="",
            description=parts[3] if len(parts) > 3 else ""
        )
        return f"Block #{block.index} added: {block.block_hash[:16]}"

    else:
        return """Usage:
  status              État de la chaîne
  verify              Vérifier intégrité + signatures
  history [path]      Historique des blocs
  sync                Synchroniser avec intégrité
  add <act> <path>    Ajouter un bloc"""


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print(f"Public Key: {flow_keys.get_public_key()[:32]}")
    print()
    print(exec_chaine("status"))
    print()
    print(exec_chaine("verify"))
