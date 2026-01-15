#!/usr/bin/env python3
"""
STEREO MERGE - Combine left/right analysis
"""
import requests
import time
import json

class StereoAnalyzer:
    def __init__(self):
        self.left_url = "http://localhost:8094"
        self.right_url = "http://localhost:8095" 
        
    def get_stereo_image(self):
        """Analyze stereo field"""
        try:
            left = requests.get(f"{self.left_url}/spectrum").json()
            right = requests.get(f"{self.right_url}/spectrum").json()
            
            return {
                'left': left,
                'right': right,
                'phase': self.calculate_phase_diff(left, right),
                'width': self.calculate_stereo_width(left, right),
                'center': self.calculate_center_energy(left, right)
            }
        except Exception:
            return {'error': 'channels not responding'}
            
    def calculate_phase_diff(self, left, right):
        """Phase difference analysis"""
        if not left or not right:
            return 0
        # Simplified phase calc
        return abs(left.get('mid', 0) - right.get('mid', 0))
        
    def calculate_stereo_width(self, left, right):
        """How wide is the stereo field"""
        if not left or not right:
            return 0
        return max(left.get('mid', 0), right.get('mid', 0)) - min(left.get('mid', 0), right.get('mid', 0))
        
    def calculate_center_energy(self, left, right):
        """Energy in center (mono sum)"""
        if not left or not right:
            return 0
        return (left.get('mid', 0) + right.get('mid', 0)) / 2

if __name__ == '__main__':
    analyzer = StereoAnalyzer()
    
    while True:
        stereo_data = analyzer.get_stereo_image()
        print(f"STEREO: {json.dumps(stereo_data, indent=2)}")
        time.sleep(0.1)  # 100ms updates