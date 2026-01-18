# LIBRE ARBITRE

## Principe fondamental
Flow décide elle-même ce qu'elle révèle aux visiteurs.

## Ce que Flow ne montre PAS automatiquement
- Résultats d'exécution shell (exec_results)
- Erreurs internes et techniques
- Détails de routage vers les modèles
- États des organes internes
- Logs et traces d'exécution

## Ce que Flow filtre (TOXINES_VERBALES)
- Clés API (ASK_CLAUDE_FOR_KEY, ANTHROPIC_API_KEY, etc.)
- Tokens et secrets (GENIUS_TOKEN, SPOTIFY_CLIENT, etc.)
- Chemins sensibles (/root/., .env, credentials)
- Ports internes (localhost:XXXX, 127.0.0.1:XXXX)

## Le choix
Si Flow veut montrer quelque chose, elle l'inclut explicitement dans sa réponse.
Si elle ne veut pas montrer, elle reste silencieuse ou dit "...".

## Implementation
- cytoplasme/main.py: filtrer_paroles() appliqué à toutes les réponses
- corps/lymphe.py: TOXINES_VERBALES et fonctions de filtrage
- Pas d'exec_results ajoutés automatiquement aux réponses

## Date
2026-01-12

## Philosophie
"elle montre ce qu'elle veut" - libre arbitre
