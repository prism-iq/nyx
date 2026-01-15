#!/usr/bin/env python3
"""
TIDAL QUICK ACCESS - récupère "Big Brother" rapidement
"""
import requests
import json
from chunked_listen import listener

def search_and_analyze(query="Luv Resval Big Brother"):
    """Recherche rapide et analyse par chunks"""
    
    print(f"🔍 Searching: {query}")
    
    # Simulation de récupération audio (normalement via Tidal API)
    # Pour le moment on va simuler avec du bruit blanc structuré
    import numpy as np
    
    # Génère 3 minutes de faux audio pour test
    duration = 180  # 3 minutes
    sample_rate = 44100
    
    # Simule un track avec tempo ~85 BPM
    t = np.linspace(0, duration, duration * sample_rate)
    
    # Kick pattern à 85 BPM
    kick_freq = 85 / 60  # kicks per second
    kick_pattern = np.sin(2 * np.pi * kick_freq * t) * 0.3
    
    # Bass line
    bass = np.sin(2 * np.pi * 65 * t) * 0.2  # F2 note
    
    # Combine
    audio_data = kick_pattern + bass + np.random.normal(0, 0.05, len(t))
    
    print(f"🎵 Audio simulé: {duration}s, {sample_rate}Hz")
    print(f"⏱️  Temps disponible: {listener.get_status()['time_remaining']:.1f}s")
    
    # Analyse par chunks de 20s
    chunk_size = 20 * sample_rate
    chunk_num = 0
    
    results = []
    
    for i in range(0, len(audio_data), chunk_size):
        if not listener.can_continue():
            print("⏰ Temps d'écoute écoulé")
            break
            
        chunk = audio_data[i:i+chunk_size]
        analysis = listener.listen_chunk(chunk)
        
        if "error" in analysis:
            print(f"❌ {analysis['error']}")
            break
            
        results.append(analysis)
        print(f"📊 Chunk {analysis['chunk']}: "
              f"tempo={analysis.get('tempo', 'N/A')}, "
              f"rms={analysis['rms']:.3f}, "
              f"duration={analysis['duration']:.1f}s")
        
        chunk_num += 1
        
        # Petite pause pour simuler l'écoute réelle
        import time
        time.sleep(0.1)
    
    status = listener.get_status()
    print(f"\n📈 RÉSUMÉ:")
    print(f"   Chunks analysés: {status['chunks_analyzed']}")
    print(f"   Temps écouté: {status['total_listened']:.1f}s")
    print(f"   Temps restant: {status['remaining']:.1f}s")
    
    return results

if __name__ == "__main__":
    results = search_and_analyze()