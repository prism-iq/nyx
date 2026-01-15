#!/usr/bin/env python3
"""
SHELL — Système nerveux moteur de Flow

Analogie biologique: Système nerveux moteur + muscles
- Motoneurones: transmettent les commandes du cerveau (cytoplasme)
- Muscles: exécutent les actions physiques (fichiers, services)
- Réflexes: actions automatiques sans passer par le cerveau

Rôle:
Flow (le LLM) génère des réponses contenant des commandes [EXEC:*].
Ce module parse ces commandes et les exécute.
C'est ainsi que Flow peut se modifier lui-même.

Sécurité:
- edit: restreint à /opt/flow-chat/ avec backup automatique
- reload: limité aux services Flow autorisés
- shell: exécution avec timeout
- test: environnement isolé pour tester du code

Commandes disponibles:
- [EXEC:shell]<cmd>[/EXEC]     Exécuter une commande bash
- [EXEC:write]<path>:::<content>[/EXEC]  Écrire un fichier
- [EXEC:edit]<path>:::<old>:::<new>[/EXEC]  Modifier un fichier
- [EXEC:reload]<service>[/EXEC]  Redémarrer un service Flow
- [EXEC:test]<code>[/EXEC]      Tester du code Python
- [EXEC:create]<name>:::<code>[/EXEC]  Créer un nouveau module
- [EXEC:inspect]<organ>[/EXEC]  Inspecter un organe
- [EXEC:list][/EXEC]            Lister les outils disponibles
- [EXEC:integrite]<cmd>[/EXEC]  Interface intégrité PQC
- [EXEC:chaine]<cmd>[/EXEC]     Interface blockchain PQC
- [EXEC:veille]<cmd>[/EXEC]     Interface système immunitaire

Communication:
- Appelé par: cytoplasme/main.py (après réponse Claude)
- Appelle: integrite, chaine, veille (via leurs exec_*)
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Tuple, List


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Configuration de l'exécuteur."""

    # Chemins
    FLOW_HOME = "/opt/flow-chat"
    TOOLS_DIR = "/opt/flow-chat/corps"

    # Services Flow autorisés pour reload
    ALLOWED_SERVICES = [
        'flow-cytoplasme',   # Cerveau LLM
        'flow-membrane',     # Gateway web
        'flow-synapse',      # Communication
        'flow-coeur',        # Émotions
        'flow-pacemaker',    # Rythme
        'flow-oreille',      # Audio
        'flow-veille',       # Système immunitaire
    ]

    # Timeouts (secondes)
    SHELL_TIMEOUT = 30
    TEST_TIMEOUT = 10
    RELOAD_TIMEOUT = 10

    # Pattern pour détecter les commandes EXEC
    EXEC_PATTERN = r'\[EXEC:(.*?)\](.*?)\[/EXEC\]'


# =============================================================================
# EXÉCUTEUR DE COMMANDES
# =============================================================================

class ExecuteurShell:
    """
    Exécuteur de commandes EXEC dans les réponses de Flow.

    Pattern: Command (chaque type d'EXEC est une commande)

    Usage:
        executeur = ExecuteurShell()
        clean_text, results = executeur.executer_dans_texte(response)
    """

    def __init__(self):
        """Initialise l'exécuteur."""
        self.flow_home = Config.FLOW_HOME
        self.tools_dir = Config.TOOLS_DIR
        self.allowed_services = Config.ALLOWED_SERVICES

    # -------------------------------------------------------------------------
    # COMMANDES DE BASE
    # -------------------------------------------------------------------------

    def execute_command(self, cmd: str, timeout: int = None) -> str:
        """
        Exécute une commande shell.

        Args:
            cmd: Commande bash à exécuter
            timeout: Timeout en secondes (défaut: SHELL_TIMEOUT)

        Returns:
            Sortie de la commande (stdout + stderr)
        """
        timeout = timeout or Config.SHELL_TIMEOUT

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.flow_home
            )
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            return output.strip()

        except subprocess.TimeoutExpired:
            return f"ERROR: timeout ({timeout}s)"
        except Exception as e:
            return f"ERROR: {e}"

    def write_file(self, filepath: str, content: str) -> str:
        """
        Écrit un fichier.

        Args:
            filepath: Chemin absolu du fichier
            content: Contenu à écrire

        Returns:
            Message de confirmation ou erreur
        """
        try:
            filepath = filepath.strip()
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"OK: wrote {filepath}"

        except Exception as e:
            return f"ERROR: {e}"

    def edit_file(self, filepath: str, old_str: str, new_str: str) -> str:
        """
        Modifie un fichier avec backup automatique.

        Sécurité: Restreint à /opt/flow-chat/

        Args:
            filepath: Chemin du fichier
            old_str: Texte à remplacer
            new_str: Nouveau texte

        Returns:
            Message de confirmation ou erreur
        """
        try:
            filepath = filepath.strip()

            # Sécurité: seulement /opt/flow-chat
            if not filepath.startswith('/opt/flow-chat/'):
                return "ERROR: can only edit files in /opt/flow-chat/"

            # Lire le contenu actuel
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_str not in content:
                return f"ERROR: string not found in {filepath}"

            # Backup automatique
            with open(filepath + '.bak', 'w', encoding='utf-8') as f:
                f.write(content)

            # Remplacer (première occurrence seulement)
            new_content = content.replace(old_str, new_str, 1)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"OK: edited {filepath}"

        except Exception as e:
            return f"ERROR: {e}"

    def reload_service(self, service: str) -> str:
        """
        Redémarre un service Flow via systemctl.

        Sécurité: Limité aux services de la whitelist.

        Args:
            service: Nom du service (ex: flow-cytoplasme)

        Returns:
            Message de confirmation ou erreur
        """
        try:
            service = service.strip()

            if service not in self.allowed_services:
                return f"ERROR: can only reload {self.allowed_services}"

            result = subprocess.run(
                ['systemctl', 'restart', service],
                capture_output=True,
                text=True,
                timeout=Config.RELOAD_TIMEOUT
            )

            if result.returncode == 0:
                return f"OK: reloaded {service}"
            return f"ERROR: {result.stderr}"

        except Exception as e:
            return f"ERROR: {e}"

    # -------------------------------------------------------------------------
    # COMMANDES AVANCÉES
    # -------------------------------------------------------------------------

    def test_code(self, code: str) -> str:
        """
        Teste du code Python dans un environnement isolé.

        Le code est écrit dans un fichier temporaire et exécuté
        avec le venv de cytoplasme.

        Args:
            code: Code Python à tester

        Returns:
            Sortie du code ou message d'erreur
        """
        try:
            test_file = Path(self.flow_home) / ".test_code.py"
            test_file.write_text(code)

            # Exécuter avec le venv
            result = subprocess.run(
                [f"{self.flow_home}/cytoplasme/venv/bin/python", str(test_file)],
                capture_output=True,
                text=True,
                timeout=Config.TEST_TIMEOUT,
                cwd=self.flow_home,
                env={**os.environ, "PYTHONPATH": self.flow_home}
            )

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output = f"EXIT CODE {result.returncode}\n{output}"

            # Nettoyer
            test_file.unlink(missing_ok=True)

            return output.strip() or "OK (no output)"

        except subprocess.TimeoutExpired:
            return f"ERROR: timeout ({Config.TEST_TIMEOUT}s)"
        except Exception as e:
            return f"ERROR: {e}"

    def create_tool(self, name: str, code: str, docstring: str = "") -> str:
        """
        Crée un nouveau module/outil dans corps/.

        Args:
            name: Nom du module (lowercase, underscores)
            code: Code Python du module
            docstring: Description du module

        Returns:
            Message de confirmation ou erreur
        """
        try:
            name = name.strip()

            # Validation du nom
            if not re.match(r'^[a-z_][a-z0-9_]*$', name):
                return "ERROR: invalid name (use lowercase, underscores)"

            tool_path = Path(self.tools_dir) / f"{name}.py"

            # Backup si existe déjà
            if tool_path.exists():
                backup_path = tool_path.with_suffix('.py.bak')
                tool_path.rename(backup_path)

            # Header du module
            header = f'''#!/usr/bin/env python3
"""
{name.upper()} — {docstring or 'Module généré par Flow'}

Créé automatiquement via [EXEC:create]
"""

'''
            # Écrire le module
            tool_path.write_text(header + code)
            tool_path.chmod(0o644)

            # Vérifier la syntaxe
            result = subprocess.run(
                [f"{self.flow_home}/cytoplasme/venv/bin/python", "-m", "py_compile", str(tool_path)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return f"SYNTAX ERROR: {result.stderr}"

            return f"OK: created {tool_path}"

        except Exception as e:
            return f"ERROR: {e}"

    def inspect_organ(self, organ: str) -> str:
        """
        Inspecte un organe: son code et son état.

        Args:
            organ: Nom de l'organe (ex: cytoplasme, membrane)

        Returns:
            Code source (tronqué) et statut du service
        """
        try:
            organ = organ.strip()

            # Chemins possibles pour l'organe
            paths_to_check = [
                Path(self.flow_home) / organ / "main.py",
                Path(self.flow_home) / organ / "main.go",
                Path(self.tools_dir) / f"{organ}.py",
                Path(self.flow_home) / "cytoplasme" / f"{organ}.py",
            ]

            organ_file = None
            for p in paths_to_check:
                if p.exists():
                    organ_file = p
                    break

            if not organ_file:
                return f"ERROR: organ '{organ}' not found"

            # Lire le code (limité à 3000 chars)
            content = organ_file.read_text()
            if len(content) > 3000:
                content = content[:3000] + f"\n... [truncated, {len(content)} chars total]"

            # Vérifier le service systemd
            service_name = f"flow-{organ}"
            status_result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            service_status = status_result.stdout.strip()

            return f"""ORGAN: {organ}
FILE: {organ_file}
SERVICE: {service_name} ({service_status})

--- CODE ---
{content}"""

        except Exception as e:
            return f"ERROR: {e}"

    def list_tools(self) -> str:
        """
        Liste tous les outils/modules disponibles dans corps/.

        Returns:
            Liste formatée des modules avec leur description
        """
        try:
            tools = []
            corps_path = Path(self.tools_dir)

            for f in sorted(corps_path.glob("*.py")):
                if not f.name.startswith('_'):
                    # Extraire la première ligne de docstring
                    content = f.read_text()
                    doc = ""
                    if '"""' in content:
                        start = content.find('"""') + 3
                        end = content.find('"""', start)
                        if end > start:
                            doc = content[start:end].strip().split('\n')[0]
                    tools.append(f"- {f.stem}: {doc[:50]}")

            return "TOOLS:\n" + "\n".join(tools[:30])

        except Exception as e:
            return f"ERROR: {e}"

    # -------------------------------------------------------------------------
    # PARSEUR PRINCIPAL
    # -------------------------------------------------------------------------

    def executer_dans_texte(self, text: str) -> Tuple[str, List[str]]:
        """
        Parse et exécute les commandes [EXEC:*] dans un texte.

        C'est la méthode principale appelée par cytoplasme après
        avoir reçu une réponse de Claude.

        Pattern: [EXEC:type]contenu[/EXEC]

        Args:
            text: Texte contenant potentiellement des commandes EXEC

        Returns:
            Tuple (texte_nettoyé, liste_résultats)
            - texte_nettoyé: texte sans les blocs EXEC
            - liste_résultats: résultats de chaque commande
        """
        results = []

        for match in re.finditer(Config.EXEC_PATTERN, text, re.DOTALL):
            exec_type = match.group(1).strip().lower()
            exec_content = match.group(2).strip()

            try:
                result = self._execute_single(exec_type, exec_content)
                if result:
                    results.append(result)

            except Exception as e:
                results.append(f"ERROR: {e}")
                print(f"[EXEC ERROR] {e}")

        # Supprimer les blocs EXEC du texte
        clean_text = re.sub(Config.EXEC_PATTERN, '', text, flags=re.DOTALL).strip()

        return clean_text, results

    def _execute_single(self, exec_type: str, content: str) -> str:
        """
        Exécute une seule commande EXEC.

        Args:
            exec_type: Type de commande (shell, write, edit, etc.)
            content: Contenu de la commande

        Returns:
            Résultat de l'exécution
        """
        # Shell
        if exec_type == 'shell':
            result = self.execute_command(content)
            print(f"[EXEC:shell] {content[:50]}...")
            return f"[shell] {result[:200]}"

        # Write
        elif exec_type == 'write':
            if ':::' in content:
                filepath, file_content = content.split(':::', 1)
                result = self.write_file(filepath.strip(), file_content.strip())
                print(f"[EXEC:write] {filepath}")
                return result

        # Edit
        elif exec_type == 'edit':
            parts = content.split(':::', 2)
            if len(parts) == 3:
                result = self.edit_file(parts[0], parts[1], parts[2])
                print(f"[EXEC:edit] {result}")
                return result

        # Reload
        elif exec_type == 'reload':
            result = self.reload_service(content)
            print(f"[EXEC:reload] {result}")
            return result

        # Test
        elif exec_type == 'test':
            result = self.test_code(content)
            print(f"[EXEC:test] {result[:100]}...")
            return f"[test]\n{result}"

        # Create
        elif exec_type == 'create':
            parts = content.split(':::', 2)
            if len(parts) == 2:
                result = self.create_tool(parts[0], parts[1])
            elif len(parts) == 3:
                result = self.create_tool(parts[0], parts[2], parts[1])
            else:
                result = "ERROR: format is name:::code or name:::doc:::code"
            print(f"[EXEC:create] {result}")
            return result

        # Inspect
        elif exec_type in ('inspect', 'see'):
            result = self.inspect_organ(content)
            print(f"[EXEC:inspect] {content}")
            return f"[inspect]\n{result[:500]}"

        # List
        elif exec_type in ('list', 'tools'):
            result = self.list_tools()
            print(f"[EXEC:list]")
            return result

        # Intégrité PQC
        elif exec_type in ('integrite', 'integrity'):
            from corps.integrite import exec_integrite
            result = exec_integrite(content)
            print(f"[EXEC:integrite] {content}")
            return f"[integrite]\n{result}"

        # Chaîne PQC
        elif exec_type in ('chaine', 'chain'):
            from corps.chaine import exec_chaine
            result = exec_chaine(content)
            print(f"[EXEC:chaine] {content}")
            return f"[chaine]\n{result}"

        # Veille (système immunitaire)
        elif exec_type in ('veille', 'immune'):
            from corps.veille import exec_veille
            result = exec_veille(content)
            print(f"[EXEC:veille] {content}")
            return f"[veille]\n{result}"

        # Douleur (système nerveux sensoriel + guérison)
        elif exec_type in ('douleur', 'pain', 'heal'):
            from corps.douleur import exec_douleur
            result = exec_douleur(content)
            print(f"[EXEC:douleur] {content}")
            return f"[douleur]\n{result}"

        # Paradigmes (visions du monde + synchronicité)
        elif exec_type in ('paradigmes', 'paradigm', 'vue', 'sync'):
            from corps.paradigmes import exec_paradigmes
            result = exec_paradigmes(content)
            print(f"[EXEC:paradigmes] {content}")
            return f"[paradigmes]\n{result}"

        elif exec_type in ('constantes', 'const', 'math', 'maths', 'nombres'):
            from corps.constantes import exec_constantes
            result = exec_constantes(content)
            print(f"[EXEC:constantes] {content}")
            return f"[constantes]\n{result}"

        return ""


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    executeur = ExecuteurShell()

    # Test: simuler une réponse de Flow
    test_response = """
    Je vérifie mes outils disponibles:
    [EXEC:list][/EXEC]
    """

    clean, results = executeur.executer_dans_texte(test_response)
    print("CLEAN:", clean)
    print("RESULTS:", results)
