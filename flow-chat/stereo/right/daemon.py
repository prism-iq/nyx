#!/usr/bin/env python3
"""
RIGHT CHANNEL DAEMON  
Port 8095 - Analyse canal droit en temps réel
"""
import asyncio
import numpy as np
import sounddevice as sd
from flask import Flask, jsonify
import threading

app = Flask(__name__)

class RightChannel:
    def __init__(self):
        self.is_listening = False
        self.current_spectrum = None
        self.tempo = None
        
    async def listen_realtime(self):
        """Stream audio right channel"""
        def callback(indata, frames, time, status):
            if status:
                print(f"[RIGHT] {status}")
            # Process right channel (indata[:, 1])  
            right_data = indata[:, 1]
            self.analyze_spectrum(right_data)
            
        with sd.InputStream(callback=callback, channels=2, samplerate=44100):
            while self.is_listening:
                await asyncio.sleep(0.01)  # 10ms precision
                
    def analyze_spectrum(self, data):
        """FFT analysis on right channel"""
        fft = np.fft.fft(data)
        self.current_spectrum = {
            'sub': np.mean(np.abs(fft[20:60])),
            'bass': np.mean(np.abs(fft[60:250])), 
            'mid': np.mean(np.abs(fft[250:2000])),
            'high': np.mean(np.abs(fft[2000:20000]))
        }

@app.route('/status')
def status():
    return jsonify({'channel': 'right', 'listening': right_channel.is_listening})

@app.route('/start') 
def start():
    right_channel.is_listening = True
    asyncio.create_task(right_channel.listen_realtime())
    return jsonify({'status': 'started'})

@app.route('/spectrum')
def spectrum():
    return jsonify(right_channel.current_spectrum)

right_channel = RightChannel()

if __name__ == '__main__':
    app.run(port=8095, debug=False)