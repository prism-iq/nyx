#!/usr/bin/env python3
"""
DSP.py — Digital Signal Processing pour Flow
Implémente les concepts Ableton en Python

Basé sur: librosa, scipy, numpy
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path

# Lazy imports pour performance
_librosa = None
_scipy = None

def _get_librosa():
    global _librosa
    if _librosa is None:
        import librosa
        _librosa = librosa
    return _librosa

def _get_scipy():
    global _scipy
    if _scipy is None:
        import scipy
        _scipy = scipy
    return _scipy


# =============================================================================
# ANALYSIS (comme Spectrum d'Ableton)
# =============================================================================

def load_audio(path: str, sr: int = 22050) -> Tuple[np.ndarray, int]:
    """Charge un fichier audio"""
    librosa = _get_librosa()
    y, sr = librosa.load(path, sr=sr)
    return y, sr


def spectrum_analysis(y: np.ndarray, sr: int, n_fft: int = 2048) -> Dict:
    """
    Analyse spectrale FFT (comme Spectrum d'Ableton)
    Retourne les magnitudes par bande de fréquence
    """
    librosa = _get_librosa()

    # STFT
    D = librosa.stft(y, n_fft=n_fft)
    magnitude = np.abs(D)

    # Fréquences
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    # Moyennes par bande (style EQ)
    bands = {
        'sub': (20, 60),
        'bass': (60, 250),
        'low_mid': (250, 500),
        'mid': (500, 2000),
        'high_mid': (2000, 4000),
        'presence': (4000, 6000),
        'brilliance': (6000, 20000)
    }

    band_energy = {}
    for name, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs < high)
        if mask.any():
            band_energy[name] = float(np.mean(magnitude[mask]))
        else:
            band_energy[name] = 0.0

    # Normaliser
    total = sum(band_energy.values()) or 1
    band_percent = {k: round(v / total * 100, 1) for k, v in band_energy.items()}

    return {
        'bands': band_percent,
        'dominant_band': max(band_percent, key=band_percent.get),
        'spectral_centroid': float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
        'spectral_bandwidth': float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))),
        'spectral_rolloff': float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
    }


def dynamics_analysis(y: np.ndarray) -> Dict:
    """
    Analyse dynamique (comme les meters d'Ableton)
    RMS, Peak, Crest Factor
    """
    librosa = _get_librosa()

    # RMS (niveau moyen)
    rms = librosa.feature.rms(y=y)[0]
    rms_mean = float(np.mean(rms))
    rms_max = float(np.max(rms))

    # Peak
    peak = float(np.max(np.abs(y)))

    # Crest factor (peak/rms) - mesure de dynamique
    crest = peak / rms_mean if rms_mean > 0 else 0

    # Dynamic range
    rms_db = 20 * np.log10(rms + 1e-10)
    dynamic_range = float(np.max(rms_db) - np.min(rms_db))

    return {
        'rms_mean': rms_mean,
        'rms_max': rms_max,
        'peak': peak,
        'crest_factor': float(crest),
        'dynamic_range_db': dynamic_range,
        'is_compressed': crest < 4,  # très compressé si crest < 4
        'is_loud': rms_mean > 0.1
    }


def rhythm_analysis(y: np.ndarray, sr: int) -> Dict:
    """
    Analyse rythmique (tempo, beats)
    """
    librosa = _get_librosa()

    # Tempo et beats
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

    # Onset strength (attaques)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    # Tempogram pour groove
    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr)

    return {
        'tempo': float(tempo) if not hasattr(tempo, '__len__') else float(tempo[0]),
        'beat_count': len(beats),
        'onset_strength_mean': float(np.mean(onset_env)),
        'onset_strength_std': float(np.std(onset_env)),
        'groove_consistency': float(1 - np.std(onset_env) / (np.mean(onset_env) + 1e-10))
    }


def pitch_analysis(y: np.ndarray, sr: int) -> Dict:
    """
    Analyse de pitch (comme Tuner d'Ableton)
    """
    librosa = _get_librosa()

    # Chroma (notes)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    # Note dominante
    chroma_mean = np.mean(chroma, axis=1)
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    dominant_note = notes[np.argmax(chroma_mean)]

    # Pitch tracking (f0)
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=50, fmax=2000)
    f0_clean = f0[~np.isnan(f0)]

    return {
        'dominant_note': dominant_note,
        'chroma_profile': {notes[i]: float(chroma_mean[i]) for i in range(12)},
        'f0_mean': float(np.mean(f0_clean)) if len(f0_clean) > 0 else None,
        'f0_std': float(np.std(f0_clean)) if len(f0_clean) > 0 else None,
        'pitch_stability': float(1 - np.std(f0_clean) / (np.mean(f0_clean) + 1e-10)) if len(f0_clean) > 0 else 0
    }


def key_detection(y: np.ndarray, sr: int) -> Dict:
    """
    Détection de tonalité
    """
    librosa = _get_librosa()

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    # Profils majeur/mineur de Krumhansl-Kessler
    major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    best_corr = -1
    best_key = 'C'
    best_mode = 'major'

    for i in range(12):
        # Rotation pour chaque tonalité
        rotated = np.roll(chroma_mean, -i)

        # Corrélation avec profil majeur
        corr_major = np.corrcoef(rotated, major_profile)[0, 1]
        if corr_major > best_corr:
            best_corr = corr_major
            best_key = notes[i]
            best_mode = 'major'

        # Corrélation avec profil mineur
        corr_minor = np.corrcoef(rotated, minor_profile)[0, 1]
        if corr_minor > best_corr:
            best_corr = corr_minor
            best_key = notes[i]
            best_mode = 'minor'

    return {
        'key': best_key,
        'mode': best_mode,
        'confidence': float(best_corr),
        'full_key': f"{best_key} {best_mode}"
    }


def timbre_analysis(y: np.ndarray, sr: int) -> Dict:
    """
    Analyse de timbre (MFCCs)
    Utile pour classifier les sons
    """
    librosa = _get_librosa()

    # MFCCs (13 coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    # Moyennes et écarts-types
    mfcc_mean = np.mean(mfccs, axis=1)
    mfcc_std = np.std(mfccs, axis=1)

    # Spectral contrast (différence entre pics et vallées)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)

    # Zero crossing rate (indicateur de bruit vs tonal)
    zcr = librosa.feature.zero_crossing_rate(y)[0]

    return {
        'mfcc_mean': mfcc_mean.tolist(),
        'mfcc_std': mfcc_std.tolist(),
        'spectral_contrast_mean': float(np.mean(contrast)),
        'zero_crossing_rate': float(np.mean(zcr)),
        'is_noisy': float(np.mean(zcr)) > 0.1,
        'brightness': float(mfcc_mean[1]) if len(mfcc_mean) > 1 else 0
    }


# =============================================================================
# FULL ANALYSIS (tout en un)
# =============================================================================

def full_audio_analysis(path: str) -> Dict:
    """
    Analyse complète d'un fichier audio
    Combine toutes les analyses
    """
    try:
        y, sr = load_audio(path)

        return {
            'file': path,
            'duration': float(len(y) / sr),
            'sample_rate': sr,
            'spectrum': spectrum_analysis(y, sr),
            'dynamics': dynamics_analysis(y),
            'rhythm': rhythm_analysis(y, sr),
            'pitch': pitch_analysis(y, sr),
            'key': key_detection(y, sr),
            'timbre': timbre_analysis(y, sr)
        }
    except Exception as e:
        return {'error': str(e), 'file': path}


def analyze_from_url(url: str, temp_dir: str = "/tmp") -> Dict:
    """
    Télécharge et analyse un fichier audio depuis une URL
    """
    import requests
    import tempfile

    try:
        # Download
        r = requests.get(url, timeout=60)
        r.raise_for_status()

        # Save temp
        ext = url.split('.')[-1][:4] if '.' in url else 'mp3'
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False, dir=temp_dir) as f:
            f.write(r.content)
            temp_path = f.name

        # Analyze
        result = full_audio_analysis(temp_path)
        result['source_url'] = url

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

        return result
    except Exception as e:
        return {'error': str(e), 'url': url}


# =============================================================================
# DESCRIPTORS (interprétation humaine)
# =============================================================================

def describe_audio(analysis: Dict) -> Dict:
    """
    Génère une description humaine de l'analyse
    """
    descriptions = []
    tags = []

    # Tempo
    tempo = analysis.get('rhythm', {}).get('tempo', 0)
    if tempo:
        if tempo < 80:
            descriptions.append("tempo lent, ambiance posée")
            tags.append('slow')
        elif tempo < 120:
            descriptions.append("tempo modéré, groove relaxé")
            tags.append('mid-tempo')
        elif tempo < 140:
            descriptions.append("tempo énergique")
            tags.append('upbeat')
        else:
            descriptions.append("tempo rapide, haute énergie")
            tags.append('fast')

    # Key
    key_info = analysis.get('key', {})
    if key_info.get('mode') == 'minor':
        descriptions.append("tonalité mineure, ambiance sombre")
        tags.append('dark')
    else:
        descriptions.append("tonalité majeure, ambiance lumineuse")
        tags.append('bright')

    # Dynamics
    dynamics = analysis.get('dynamics', {})
    if dynamics.get('is_compressed'):
        descriptions.append("son compressé, moderne")
        tags.append('compressed')
    if dynamics.get('dynamic_range_db', 0) > 20:
        descriptions.append("grande dynamique, cinématique")
        tags.append('dynamic')

    # Spectrum
    spectrum = analysis.get('spectrum', {})
    dominant = spectrum.get('dominant_band', '')
    if 'bass' in dominant or 'sub' in dominant:
        descriptions.append("basses proéminentes")
        tags.append('bass-heavy')
    elif 'high' in dominant or 'brilliance' in dominant:
        descriptions.append("aigus brillants")
        tags.append('bright')

    # Timbre
    timbre = analysis.get('timbre', {})
    if timbre.get('is_noisy'):
        descriptions.append("texture bruitée/granuleuse")
        tags.append('noisy')

    return {
        'description': '. '.join(descriptions) + '.' if descriptions else 'Analyse non concluante.',
        'tags': tags,
        'summary': {
            'tempo': tempo,
            'key': key_info.get('full_key'),
            'dominant_freq': dominant,
            'dynamic_range': dynamics.get('dynamic_range_db'),
            'crest_factor': dynamics.get('crest_factor')
        }
    }


# =============================================================================
# COMPARISON (comparer deux tracks)
# =============================================================================

def compare_tracks(analysis1: Dict, analysis2: Dict) -> Dict:
    """
    Compare deux analyses audio
    """
    def safe_get(d, *keys, default=0):
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k, default)
            else:
                return default
        return d if d is not None else default

    tempo1 = safe_get(analysis1, 'rhythm', 'tempo')
    tempo2 = safe_get(analysis2, 'rhythm', 'tempo')

    key1 = safe_get(analysis1, 'key', 'full_key', default='')
    key2 = safe_get(analysis2, 'key', 'full_key', default='')

    crest1 = safe_get(analysis1, 'dynamics', 'crest_factor')
    crest2 = safe_get(analysis2, 'dynamics', 'crest_factor')

    return {
        'tempo_diff': abs(tempo1 - tempo2),
        'same_key': key1 == key2,
        'key1': key1,
        'key2': key2,
        'dynamics_similar': abs(crest1 - crest2) < 1,
        'compatible_for_mix': abs(tempo1 - tempo2) < 5 or abs(tempo1 - tempo2 * 2) < 5,
        'energy_comparison': 'track1 louder' if crest1 < crest2 else 'track2 louder' if crest2 < crest1 else 'similar'
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("DSP Module loaded")
    print("Available functions:")
    print("  - full_audio_analysis(path)")
    print("  - analyze_from_url(url)")
    print("  - describe_audio(analysis)")
    print("  - compare_tracks(a1, a2)")
    print("  - spectrum_analysis(y, sr)")
    print("  - dynamics_analysis(y)")
    print("  - rhythm_analysis(y, sr)")
    print("  - pitch_analysis(y, sr)")
    print("  - key_detection(y, sr)")
    print("  - timbre_analysis(y, sr)")
