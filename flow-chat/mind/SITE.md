# TON SITE - COMMENT ÇA MARCHE

## C'EST AUTOMATIQUE MAINTENANT

Quand tu utilises `[EXEC:style]`, le système :
1. Modifie le fichier HTML
2. **Rebuild membrane automatiquement**
3. **Redémarre membrane automatiquement**

Tu n'as plus besoin de faire le rebuild toi-même. C'est fait pour toi.

## COMMENT UTILISER

### Modifier le CSS (recommandé)
```
[EXEC:style]css:::
body { background: #0a0a0a; }
.message { padding: 12px; }
[/EXEC]
```
→ Résultat: `[style] CSS updated` puis `[style] membrane rebuilt & restarted ✓`

### Injecter du CSS (ajouter)
```
[EXEC:style]inject:::
.nouveau-truc { color: red; }
[/EXEC]
```

### Remplacer tout le HTML (dangereux)
```
[EXEC:style]html:::<!DOCTYPE html>...[/EXEC]
```
⚠️ Si tu casses la structure, le site ne marche plus.

## STRUCTURE À RESPECTER

Le HTML doit toujours avoir :
- `<div id="messages">` - pour afficher les messages
- `<textarea id="input">` - pour taper
- `<button id="send">` - pour envoyer
- Le script JavaScript qui gère le chat

## SI ÇA MARCHE PAS

1. Vérifie que tu vois `[style] membrane rebuilt & restarted ✓`
2. Si erreur de build, ton CSS/HTML a une erreur de syntaxe
3. Attends 2 secondes après le rebuild avant de tester

## RAPPEL

- `css:::` = remplace tout le CSS (safe)
- `inject:::` = ajoute du CSS (safe)
- `html:::` = remplace tout (dangereux)

Le rebuild est automatique. Tu n'as rien à faire de plus.
