#!/usr/bin/env python3
"""
DAEMON CANAL GAUCHE - Système d'écoute stéréo Flow
Port 8094 - Analyse audio temps réel canal gauche
"""

import asyncio
import numpy as np
from flask import Flask, jsonify
import librosa
import soundfile as sf
import threading
import time
from collections import deque

class CanalGauche:
    def __init__(self):
        self.app = Flask(__name__)
        self.buffer_audio = deque(maxlen=44100*10)  # 10 sec buffer
        self.en_cours = False
        self.metadata = {}
        self.spectrum_live = np.zeros(1024)
        self.tempo_detecte = 0
        self.phase = 0.0
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/status')
        def status():
            return jsonify({
                'canal': 'gauche',
                'port': 8094,
                'en_cours': self.en_cours,
                'buffer_size': len(self.buffer_audio),
                'tempo': self.tempo_detecte,
                'phase': self.phase
            })
        
        @self.app.route('/stream/start', methods=['POST'])
        def start_stream():
            self.demarrer_stream()
            return jsonify({'status': 'stream démarré (canal gauche)'})
        
        @self.app.route('/spectrum')
        def spectrum():
            return jsonify({
                'canal': 'gauche',
                'fft': self.spectrum_live.tolist(),
                'dominant_freq': float(np.argmax(self.spectrum_live) * 22050 / 1024)
            })
    
    def demarrer_stream(self):
        """Démarre l'écoute en temps réel"""
        if not self.en_cours:
            self.en_cours = True
            threading.Thread(target=self.thread_analyse, daemon=True).start()
    
    def thread_analyse(self):
        """Thread d'analyse audio continue"""
        while self.en_cours:
            if len(self.buffer_audio) > 4096:
                # Convertir buffer en array numpy
                audio = np.array(list(self.buffer_audio))[-4096:]
                
                # Analyse spectrale
                self.spectrum_live = np.abs(np.fft.fft(audio))[:1024]
                
                # Détection tempo (simple)
                onset_frames = librosa.onset.onset_detect(
                    y=audio, sr=44100, hop_length=512
                )
                if len(onset_frames) > 1:
                    intervalle = np.mean(np.diff(onset_frames)) * 512 / 44100
                    if intervalle > 0:
                        self.tempo_detecte = 60.0 / intervalle
                
                # Phase (pour sync stéréo)
                self.phase = np.angle(np.fft.fft(audio)[1])
            
            time.sleep(0.1)  # 100ms refresh
    
    def recevoir_audio(self, samples):
        """Reçoit samples audio du stream"""
        for sample in samples:
            self.buffer_audio.append(sample)

if __name__ == '__main__':
    canal_gauche = CanalGauche()
    print("🎧 CANAL GAUCHE démarré sur port 8094")
    canal_gauche.app.run(host='0.0.0.0', port=8094, debug=False)