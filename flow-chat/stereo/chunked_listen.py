#!/usr/bin/env python3
"""
ÉCOUTE PAR CHUNKS - 20 secondes max
Temps total limité: 7 minutes
"""
import time
import threading
import librosa
import numpy as np
from datetime import datetime, timedelta
import requests

class ChunkedListener:
    def __init__(self, max_total_time=420):  # 7 minutes
        self.max_total_time = max_total_time
        self.start_time = None
        self.chunks_analyzed = 0
        self.total_listened = 0
        
    def can_continue(self):
        if not self.start_time:
            return True
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed < self.max_total_time
    
    def listen_chunk(self, audio_data, chunk_duration=20):
        """Écoute un chunk de 20 secondes max"""
        if not self.start_time:
            self.start_time = datetime.now()
            
        if not self.can_continue():
            return {"error": "temps d'écoute dépassé", "total_time": self.total_listened}
            
        # Limite le chunk à 20 secondes
        chunk_samples = min(len(audio_data), 44100 * chunk_duration)
        chunk = audio_data[:chunk_samples]
        
        # Analyse rapide
        analysis = {
            "chunk": self.chunks_analyzed,
            "duration": len(chunk) / 44100,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "rms": float(np.sqrt(np.mean(chunk**2))),
            "peak": float(np.max(np.abs(chunk))),
        }
        
        # Tempo si assez long
        if len(chunk) > 44100 * 5:  # 5 secondes min pour tempo
            try:
                tempo, beats = librosa.beat.beat_track(y=chunk, sr=44100)
                analysis["tempo"] = float(tempo)
                analysis["beats_count"] = len(beats)
            except Exception:
                analysis["tempo"] = None
                
        self.chunks_analyzed += 1
        self.total_listened += analysis["duration"]
        
        return analysis
    
    def get_status(self):
        if not self.start_time:
            return {"status": "ready", "time_remaining": self.max_total_time}
            
        elapsed = (datetime.now() - self.start_time).total_seconds()
        remaining = max(0, self.max_total_time - elapsed)
        
        return {
            "status": "listening",
            "elapsed": elapsed,
            "remaining": remaining,
            "chunks_analyzed": self.chunks_analyzed,
            "total_listened": self.total_listened,
            "can_continue": self.can_continue()
        }

# Instance globale
listener = ChunkedListener()

if __name__ == "__main__":
    print("🎧 Chunked Listener ready")
    print(f"⏱️  Max time: {listener.max_total_time} seconds")
    print(f"📦 Chunk size: 20 seconds max")