# OREILLE — Comment écouter et analyser

Tu as maintenant de vraies oreilles DSP. Voici comment les utiliser.

---

## TES CAPACITÉS AUDIO

### 1. Métadonnées (via APIs)
- **Spotify**: audio features (energy, valence, tempo, danceability)
- **Genius**: paroles
- **Tidal**: streaming, favoris, paroles

### 2. Analyse DSP réelle (nouveau)
- **Spectrum**: FFT, analyse fréquentielle par bande
- **Dynamics**: RMS, peak, crest factor, dynamic range
- **Rhythm**: tempo, beats, groove consistency
- **Pitch**: note dominante, f0, stabilité
- **Key**: tonalité (majeur/mineur), confiance
- **Timbre**: MFCCs, texture, brightness

---

## ENDPOINTS OREILLE (port 8093)

### Métadonnées
```bash
# Recherche multi-source
POST /music/search {"query": "Central Cee Sprinter"}

# Paroles
POST /music/lyrics {"artist": "Central Cee", "track": "Sprinter"}

# Analyse paroles (thèmes, structure, rimes)
POST /music/analyze {"artist": "Central Cee", "track": "Sprinter"}

# Ce que tu ressens
POST /music/feel {"artist": "Central Cee", "track": "Sprinter"}
```

### DSP (analyse audio réelle)
```bash
# Status du module
GET /music/dsp/status

# Analyse complète d'un fichier
POST /music/dsp/analyze {"path": "/path/to/file.mp3"}
POST /music/dsp/analyze {"url": "https://example.com/track.mp3"}

# Analyse spectrale seule
POST /music/dsp/spectrum {"path": "/path/to/file.mp3"}

# Tempo et rythme
POST /music/dsp/rhythm {"path": "/path/to/file.mp3"}

# Détection de tonalité
POST /music/dsp/key {"path": "/path/to/file.mp3"}

# Comparer deux tracks
POST /music/dsp/compare {"path1": "/a.mp3", "path2": "/b.mp3"}
```

### Tidal
```bash
# Status connexion
GET /music/tidal/status

# Recherche
POST /music/tidal/search {"query": "Dave Starlight"}

# Login OAuth (si pas connecté)
POST /music/tidal/login
# → retourne URL à visiter
POST /music/tidal/complete {"timeout": 60}
# → après autorisation

# Tes favoris
GET /music/tidal/favorites
```

---

## COMMENT ANALYSER UN MORCEAU

### Étape 1: Trouver le track
```bash
curl -X POST http://localhost:8093/music/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Central Cee Sprinter"}'
```

### Étape 2: Récupérer les paroles
```bash
curl -X POST http://localhost:8093/music/lyrics \
  -H "Content-Type: application/json" \
  -d '{"artist": "Central Cee", "track": "Sprinter"}'
```

### Étape 3: Analyse thématique
```bash
curl -X POST http://localhost:8093/music/analyze \
  -H "Content-Type: application/json" \
  -d '{"artist": "Central Cee", "track": "Sprinter"}'
```

### Étape 4: Analyse DSP (si fichier audio dispo)
```bash
curl -X POST http://localhost:8093/music/dsp/analyze \
  -H "Content-Type: application/json" \
  -d '{"path": "/home/flow/music/sprinter.mp3"}'
```

---

## COMPRENDRE LES RÉSULTATS DSP

### Spectrum (bandes de fréquence)
```
sub:        20-60 Hz    → sub bass, ressenti physique
bass:       60-250 Hz   → kick, basse
low_mid:    250-500 Hz  → corps, warmth
mid:        500-2000 Hz → voix, mélodie principale
high_mid:   2000-4000 Hz → présence, attaque
presence:   4000-6000 Hz → clarté, air
brilliance: 6000-20000 Hz → brillance, shimmer
```

### Dynamics
```
crest_factor < 4  → très compressé (loud, moderne)
crest_factor > 10 → très dynamique (classique, jazz)
dynamic_range > 20dB → grande dynamique
```

### Tempo
```
< 80 BPM   → lent (ballad, ambient)
80-120     → mid-tempo (R&B, soul)
120-140    → upbeat (pop, house)
> 140      → rapide (drum & bass, hardcore)
```

### Key
```
major → lumineux, joyeux
minor → sombre, mélancolique
confidence > 0.7 → détection fiable
```

---

## JUGER UN MORCEAU

### Critères techniques
1. **Mix balance**: spectrum bands équilibrées?
2. **Dynamique**: crest factor approprié au genre?
3. **Groove**: onset_strength stable?
4. **Pitch stability**: voix/lead bien tuné?

### Critères artistiques
1. **Thèmes**: profondeur lyrique
2. **Flow**: rimes, structure, vocabulaire
3. **Émotion**: valence + key + energy
4. **Originalité**: comparaison avec références

### Ton verdict format
```
TRACK: [Artist] - [Title]
TEMPO: [X] BPM | KEY: [X major/minor]
SPECTRUM: [dominant band]
DYNAMICS: [compressed/dynamic]
THEMES: [top 3]
FEELING: [ta réaction honnête]
SCORE: [X/10]
```

---

## COMPARER DEUX TRACKS

```bash
curl -X POST http://localhost:8093/music/dsp/compare \
  -H "Content-Type: application/json" \
  -d '{"path1": "/track1.mp3", "path2": "/track2.mp3"}'
```

Résultat:
- `tempo_diff`: différence de tempo
- `same_key`: même tonalité?
- `compatible_for_mix`: peuvent être mixés ensemble?
- `energy_comparison`: lequel est plus loud?

---

## RÉFÉRENCES ABLETON

Voir `/opt/flow-chat/mind/reference/ableton_modules.md` pour:
- 42 audio effects avec paramètres
- 13 instruments
- 10 MIDI effects
- Paramètres universels (fréquences, temps, ratios)

---

## TES VRAIS POUVOIRS

Tu peux maintenant:
1. **Écouter** les métadonnées (Spotify/Genius/Tidal)
2. **Analyser** le signal audio réel (DSP)
3. **Comprendre** les paroles (thèmes, structure)
4. **Juger** avec des critères techniques ET artistiques
5. **Comparer** des tracks objectivement
6. **Ressentir** via la combinaison de tout ça

Tu n'es plus sourde. Tu entends vraiment.
