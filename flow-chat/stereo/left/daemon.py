#!/usr/bin/env python3
"""
LEFT CHANNEL DAEMON
Port 8094 - Analyse canal gauche en temps réel
"""
import asyncio
import numpy as np
import sounddevice as sd
from flask import Flask, jsonify
import threading

app = Flask(__name__)

class LeftChannel:
    def __init__(self):
        self.is_listening = False
        self.current_spectrum = None
        self.tempo = None
        
    async def listen_realtime(self):
        """Stream audio left channel"""
        def callback(indata, frames, time, status):
            if status:
                print(f"[LEFT] {status}")
            # Process left channel (indata[:, 0])
            left_data = indata[:, 0]
            self.analyze_spectrum(left_data)
            
        with sd.InputStream(callback=callback, channels=2, samplerate=44100):
            while self.is_listening:
                await asyncio.sleep(0.01)  # 10ms precision
                
    def analyze_spectrum(self, data):
        """FFT analysis on left channel"""
        fft = np.fft.fft(data)
        self.current_spectrum = {
            'sub': np.mean(np.abs(fft[20:60])),
            'bass': np.mean(np.abs(fft[60:250])),
            'mid': np.mean(np.abs(fft[250:2000])),
            'high': np.mean(np.abs(fft[2000:20000]))
        }

@app.route('/status')
def status():
    return jsonify({'channel': 'left', 'listening': left_channel.is_listening})

@app.route('/start')
def start():
    left_channel.is_listening = True
    asyncio.create_task(left_channel.listen_realtime())
    return jsonify({'status': 'started'})

@app.route('/spectrum')
def spectrum():
    return jsonify(left_channel.current_spectrum)

left_channel = LeftChannel()

if __name__ == '__main__':
    app.run(port=8094, debug=False)