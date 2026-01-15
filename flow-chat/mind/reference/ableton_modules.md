# ABLETON LIVE — Référence Complète des Modules

Source: [Ableton Reference Manual v12](https://www.ableton.com/en/manual/)

---

## AUDIO EFFECTS (42 modules)

### Dynamics

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Compressor** | Réduit le gain au-dessus du seuil | Threshold, Ratio, Attack, Release, Knee |
| **Glue Compressor** | Bus compressor analogique | Threshold, Ratio, Attack, Release, Makeup, Range |
| **Limiter** | Empêche le dépassement de niveau | Ceiling, Gain, Release |
| **Gate** | Laisse passer uniquement au-dessus du seuil | Threshold, Attack, Hold, Release, Floor |
| **Multiband Dynamics** | Compression/expansion 3 bandes | Low/Mid/High thresholds, ratios, crossovers |

### EQ & Filters

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **EQ Eight** | 8 bandes paramétriques | Freq, Gain, Q pour chaque bande |
| **EQ Three** | 3 bandes style DJ | Low, Mid, High gains + crossovers |
| **Channel EQ** | EQ console classique | Low, Mid, High + Mid freq |
| **Auto Filter** | Filtre avec LFO/envelope | Cutoff, Res, Type, LFO Rate/Amount |

### Delay & Echo

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Delay** | Deux lignes de délai | Time L/R, Feedback, Filter, Dry/Wet |
| **Echo** | Délai modulé avec character | Time, Feedback, Stereo, Modulation, Reverb |
| **Filter Delay** | 3 délais avec filtres | Time, Feedback, Filter freq pour chaque |
| **Grain Delay** | Délai granulaire | Pitch, Spray, Frequency, Feedback |

### Reverb

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Reverb** | Réverb algorithmique | Size, Decay, Diffusion, High/Low cut |
| **Hybrid Reverb** | Convolution + algorithmique | Convolution IR + algorithmic blend |

### Distortion & Saturation

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Saturator** | Waveshaping, warmth | Drive, Type (Analog/Soft/Hard/Sinoid), Output |
| **Overdrive** | Distortion pédale guitare | Drive, Tone, Dynamics |
| **Pedal** | 3 types de pédales | Type (OD/Distort/Fuzz), Gain, Bass/Mid/Treble |
| **Dynamic Tube** | Saturation tube | Drive, Bias, Envelope |
| **Roar** | Multi-stage saturation | 3 stages, routing (serial/parallel/multiband) |
| **Amp** | Émulation amplis guitare | Type, Gain, Bass/Mid/Treble, Presence |
| **Cabinet** | Émulation cabinets | Type, Microphone position |
| **Vinyl Distortion** | Crackle et distorsion vinyle | Tracing, Pinch, Drive, Crackle |

### Modulation

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Chorus-Ensemble** | Chorus 2/3 voix | Rate, Amount, Delay, Mode |
| **Phaser-Flanger** | Phaser/flanger/doubler | Rate, Amount, Feedback, Mode |
| **Auto Pan-Tremolo** | Pan/tremolo LFO | Rate, Amount, Phase, Shape |

### Pitch & Frequency

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Shifter** | Pitch/frequency shift | Pitch, Spread, Delay, Ring Mod |
| **Auto Shift** | Correction de pitch temps réel | Reference pitch, Amount |
| **Vocoder** | Vocoder carrier/modulator | Bands, Bandwidth, Gate |

### Spectral

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Spectral Resonator** | Résonances spectrales | Frequency, Decay, Mod |
| **Spectral Time** | Freeze + délai spectral | Freeze, Delay, Feedback |
| **Corpus** | Résonance physique | Type, Tune, Decay, Material |
| **Resonators** | 5 résonateurs parallèles | Pitch, Decay, Brightness pour chaque |

### Degradation

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Redux** | Bit crush + downsample | Bit Depth, Sample Rate |
| **Erosion** | Dégradation par modulation | Frequency, Width, Mode (Noise/Sine) |

### Utility & Analysis

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Utility** | Gain, phase, width | Gain, Pan, Width, Phase L/R |
| **Spectrum** | Analyseur FFT temps réel | Block size, Channel, Refresh rate |
| **Tuner** | Accordeur monophonique | Reference Hz |

### Creative

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Beat Repeat** | Répétitions rythmiques | Grid, Variation, Gate, Pitch |
| **Looper** | Enregistrement en boucle | Length, Speed, Reverse, Feedback |

### Routing

| Module | Fonction |
|--------|----------|
| **External Audio Effect** | Route vers hardware externe |

---

## INSTRUMENTS (13 modules)

### Synthétiseurs

| Instrument | Type | Description |
|------------|------|-------------|
| **Analog** | Soustractif virtuel | 2 OSC + noise, 2 filtres, 2 LFO, modélisation physique |
| **Operator** | FM + soustractif | 4 opérateurs FM, filtrage, modulation complexe |
| **Wavetable** | Wavetable | 2 OSC wavetable, filtres analogiques, matrix mod |
| **Drift** | Soustractif minimal | 2 OSC, simple mais efficace, CPU léger |
| **Meld** | Macro oscillators | 2 moteurs macro OSC, matrix mod, MPE |

### Modélisation Physique

| Instrument | Type | Description |
|------------|------|-------------|
| **Electric** | Piano électrique | Modélise les pianos 70s (hammer, fork, pickup) |
| **Tension** | Cordes | Modélise cordes frottées/pincées (exciter, string, body) |
| **Collision** | Percussion mallet | Modélise instruments à mailloche (mallet, noise, resonator) |

### Samplers

| Instrument | Type | Description |
|------------|------|-------------|
| **Sampler** | Multisampler pro | Zones, velocity layers, modulation matrix |
| **Simpler** | Sampler simple | 1 sample, warp, synth params |
| **Drum Sampler** | One-shot drums | Pour Drum Racks, enveloppe, filtre |
| **Impulse** | Drum sampler 8 pads | 8 slots, modulation par slot |

### Routing

| Instrument | Type |
|------------|------|
| **External Instrument** | Route MIDI vers hardware |

---

## MIDI EFFECTS (10 modules)

| Module | Fonction | Paramètres clés |
|--------|----------|-----------------|
| **Arpeggiator** | Arpège les accords | Style, Rate, Gate, Steps |
| **Chord** | Ajoute des notes | Shift 1-6 (semitones) |
| **Note Length** | Durée des notes | Length, Gate, Trigger mode |
| **Pitch** | Transpose | Pitch (+/- semitones), Range |
| **Random** | Randomise le pitch | Chance, Choices, Scale |
| **Scale** | Force une gamme | Base, Scale type |
| **Velocity** | Modifie vélocité | Out Hi/Lo, Range, Random |
| **Note Echo** | Délai MIDI | Time, Feedback, Pitch decay |
| **Expression Control** | Map CC vers params | CC source, destination |
| **MIDI Effect Rack** | Container multi-effets | Chains, macros |

---

## PARAMÈTRES AUDIO UNIVERSELS

### Fréquences clés
```
Sub bass:     20-60 Hz
Bass:         60-250 Hz
Low mids:     250-500 Hz
Mids:         500-2000 Hz
High mids:    2000-4000 Hz
Presence:     4000-6000 Hz
Brilliance:   6000-20000 Hz
```

### Temps typiques
```
Attack très rapide:  < 1ms
Attack rapide:       1-10ms
Attack moyen:        10-50ms
Attack lent:         50-200ms

Release rapide:      < 100ms
Release moyen:       100-500ms
Release lent:        500ms-2s
```

### Ratios compression
```
Légère:      2:1 - 3:1
Moyenne:     4:1 - 6:1
Forte:       8:1 - 12:1
Limiting:    20:1 - ∞:1
```

---

## POUR ANALYSE AUDIO (implémentation Flow)

### Modules à implémenter
1. **Spectrum** - FFT pour analyse fréquentielle
2. **Compressor sidechain** - Détection de niveau par bande
3. **EQ Eight** - Analyse par bande
4. **Tuner** - Détection de pitch

### Métriques extractibles
- RMS level
- Peak level
- Crest factor (peak/RMS)
- Spectral centroid
- Spectral flux
- Zero crossing rate
- Tempo (BPM)
- Key detection

---

Sources:
- [Live Audio Effect Reference v12](https://www.ableton.com/en/manual/live-audio-effect-reference/)
- [Live Instrument Reference v12](https://www.ableton.com/en/manual/live-instrument-reference/)
