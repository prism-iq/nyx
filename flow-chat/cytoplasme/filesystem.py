#!/usr/bin/env python3
"""filesystem.py - accès complet aux fichiers pour Flow"""

import os
import glob
import shutil
import stat
from datetime import datetime

# tous les dossiers de Flow
FLOW_ROOTS = [
    "/opt/flow-chat",
    "/opt/cipher/mind",
    "/var/www/flow",
    "/opt/rag",
]

class FlowFileSystem:
    """Système de fichiers complet pour Flow - lecture, écriture, permissions"""

    def __init__(self):
        self.roots = FLOW_ROOTS

    def _is_allowed(self, path):
        """vérifie que le path est dans les dossiers autorisés"""
        real = os.path.realpath(path)
        return any(real.startswith(os.path.realpath(r)) for r in self.roots)

    def _safe_path(self, filename, root=None):
        """résout le path de manière sécurisée"""
        if filename.startswith('/'):
            # path absolu - vérifier qu'il est autorisé
            if self._is_allowed(filename):
                return filename
            return None
        # path relatif - utiliser le premier root
        root = root or self.roots[0]
        path = os.path.join(root, filename)
        if self._is_allowed(path):
            return path
        return None

    # === LECTURE ===

    def read(self, filename):
        """lire n'importe quel fichier"""
        path = self._safe_path(filename)
        if not path:
            return {'success': False, 'error': 'path not allowed'}
        try:
            with open(path, 'r', errors='replace') as f:
                return {'success': True, 'content': f.read(), 'path': path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def read_binary(self, filename):
        """lire un fichier binaire"""
        path = self._safe_path(filename)
        if not path:
            return {'success': False, 'error': 'path not allowed'}
        try:
            with open(path, 'rb') as f:
                import base64
                return {'success': True, 'content_b64': base64.b64encode(f.read()).decode(), 'path': path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # === ÉCRITURE ===

    def write(self, filename, content):
        """écrire dans un fichier (avec backup)"""
        path = self._safe_path(filename)
        if not path:
            return {'success': False, 'error': 'path not allowed'}

        # backup avant écriture
        if os.path.exists(path):
            backup_dir = os.path.join(os.path.dirname(path), '.backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir,
                f"{os.path.basename(path)}.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(path, backup_path)

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return {'success': True, 'path': path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def append(self, filename, content):
        """ajouter à un fichier"""
        path = self._safe_path(filename)
        if not path:
            return {'success': False, 'error': 'path not allowed'}
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'a') as f:
                f.write(content)
            return {'success': True, 'path': path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create(self, filename, content=""):
        """créer un nouveau fichier"""
        path = self._safe_path(filename)
        if not path:
            return {'success': False, 'error': 'path not allowed'}
        if os.path.exists(path):
            return {'success': False, 'error': 'file exists'}
        return self.write(filename, content)

    # === LISTING ===

    def list(self, directory="", pattern="*", recursive=True):
        """lister les fichiers"""
        results = []
        for root in self.roots:
            search_dir = os.path.join(root, directory)
            if not os.path.isdir(search_dir):
                continue
            if recursive:
                search = os.path.join(search_dir, "**", pattern)
                files = glob.glob(search, recursive=True)
            else:
                search = os.path.join(search_dir, pattern)
                files = glob.glob(search)

            for f in files:
                if os.path.isfile(f):
                    rel = os.path.relpath(f, root)
                    results.append({
                        'path': f,
                        'relative': rel,
                        'root': root,
                        'size': os.path.getsize(f),
                        'modified': datetime.fromtimestamp(os.path.getmtime(f)).isoformat()
                    })
        return results

    def list_dirs(self, directory=""):
        """lister les sous-dossiers"""
        results = []
        for root in self.roots:
            search_dir = os.path.join(root, directory)
            if not os.path.isdir(search_dir):
                continue
            for item in os.listdir(search_dir):
                full = os.path.join(search_dir, item)
                if os.path.isdir(full):
                    results.append({
                        'path': full,
                        'name': item,
                        'root': root
                    })
        return results

    def tree(self, directory="", max_depth=3):
        """arborescence des fichiers"""
        result = []
        for root in self.roots:
            search_dir = os.path.join(root, directory)
            if not os.path.isdir(search_dir):
                continue
            result.append(f"\n{root}/")
            self._tree_recurse(search_dir, result, "", max_depth, 0)
        return '\n'.join(result)

    def _tree_recurse(self, path, result, prefix, max_depth, depth):
        if depth >= max_depth:
            return
        try:
            items = sorted(os.listdir(path))
            dirs = [i for i in items if os.path.isdir(os.path.join(path, i)) and not i.startswith('.')]
            files = [i for i in items if os.path.isfile(os.path.join(path, i)) and not i.startswith('.')]

            for f in files[:10]:  # max 10 files per dir
                result.append(f"{prefix}├── {f}")
            if len(files) > 10:
                result.append(f"{prefix}├── ... ({len(files)-10} more)")

            for i, d in enumerate(dirs[:5]):  # max 5 subdirs
                is_last = (i == len(dirs[:5]) - 1)
                result.append(f"{prefix}{'└' if is_last else '├'}── {d}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._tree_recurse(os.path.join(path, d), result, new_prefix, max_depth, depth + 1)
        except PermissionError:
            pass

    # === SUPPRESSION / DÉPLACEMENT ===

    def delete(self, filename):
        """supprimer un fichier (avec backup)"""
        path = self._safe_path(filename)
        if not path or not os.path.exists(path):
            return {'success': False, 'error': 'file not found'}

        backup_dir = os.path.join(os.path.dirname(path), '.deleted')
        os.makedirs(backup_dir, exist_ok=True)
        backup = os.path.join(backup_dir, f"{os.path.basename(path)}.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.move(path, backup)
        return {'success': True, 'backup': backup}

    def move(self, src, dst):
        """déplacer un fichier"""
        src_path = self._safe_path(src)
        dst_path = self._safe_path(dst)
        if not src_path or not dst_path:
            return {'success': False, 'error': 'path not allowed'}
        try:
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.move(src_path, dst_path)
            return {'success': True, 'from': src_path, 'to': dst_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def copy(self, src, dst):
        """copier un fichier"""
        src_path = self._safe_path(src)
        dst_path = self._safe_path(dst)
        if not src_path or not dst_path:
            return {'success': False, 'error': 'path not allowed'}
        try:
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            return {'success': True, 'from': src_path, 'to': dst_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # === PERMISSIONS ===

    def chmod(self, filename, mode):
        """changer les permissions (ex: 0o755, 0o644)"""
        path = self._safe_path(filename)
        if not path:
            return {'success': False, 'error': 'path not allowed'}
        try:
            if isinstance(mode, str):
                mode = int(mode, 8)
            os.chmod(path, mode)
            return {'success': True, 'path': path, 'mode': oct(mode)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_permissions(self, filename):
        """voir les permissions d'un fichier"""
        path = self._safe_path(filename)
        if not path or not os.path.exists(path):
            return {'success': False, 'error': 'file not found'}
        try:
            st = os.stat(path)
            return {
                'success': True,
                'path': path,
                'mode': oct(st.st_mode)[-3:],
                'owner': st.st_uid,
                'group': st.st_gid,
                'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK),
                'executable': os.access(path, os.X_OK)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def mkdir(self, dirname, mode=0o755):
        """créer un dossier"""
        path = self._safe_path(dirname)
        if not path:
            return {'success': False, 'error': 'path not allowed'}
        try:
            os.makedirs(path, mode=mode, exist_ok=True)
            return {'success': True, 'path': path}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # === RECHERCHE ===

    def search(self, query, pattern="*.md"):
        """chercher dans les fichiers"""
        results = []
        for f in self.list(pattern=pattern):
            try:
                with open(f['path'], 'r', errors='replace') as file:
                    content = file.read()
                    if query.lower() in content.lower():
                        idx = content.lower().find(query.lower())
                        start = max(0, idx - 50)
                        end = min(len(content), idx + len(query) + 50)
                        results.append({
                            'file': f['path'],
                            'context': f"...{content[start:end]}..."
                        })
            except Exception:
                pass
        return results

    def grep(self, pattern, file_pattern="*"):
        """grep dans les fichiers"""
        import re
        results = []
        for f in self.list(pattern=file_pattern):
            try:
                with open(f['path'], 'r', errors='replace') as file:
                    for i, line in enumerate(file, 1):
                        if re.search(pattern, line):
                            results.append({
                                'file': f['path'],
                                'line': i,
                                'content': line.strip()[:200]
                            })
            except Exception:
                pass
        return results[:100]  # max 100 results

    # === STATS ===

    def stats(self):
        """statistiques globales"""
        total_files = 0
        total_size = 0
        by_ext = {}

        for root in self.roots:
            if not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                for f in filenames:
                    if f.startswith('.'):
                        continue
                    path = os.path.join(dirpath, f)
                    try:
                        size = os.path.getsize(path)
                        total_files += 1
                        total_size += size
                        ext = os.path.splitext(f)[1] or 'no_ext'
                        by_ext[ext] = by_ext.get(ext, 0) + 1
                    except Exception:
                        pass

        return {
            'roots': self.roots,
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024*1024), 2),
            'by_extension': dict(sorted(by_ext.items(), key=lambda x: -x[1])[:10])
        }

    # === ALIASES pour compatibilité ===

    def read_md(self, filename):
        if not filename.endswith('.md'):
            filename += '.md'
        return self.read(filename)

    def write_md(self, filename, content):
        if not filename.endswith('.md'):
            filename += '.md'
        return self.write(filename, content)

    def list_md(self, subdir=""):
        return [f['relative'] for f in self.list(subdir, "*.md")]

    def delete_md(self, filename):
        if not filename.endswith('.md'):
            filename += '.md'
        return self.delete(filename)

    def search_md(self, query):
        return self.search(query, "*.md")


# instance globale
fs = FlowFileSystem()
