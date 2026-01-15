class Euphonie:
    """
    ORGANE EUPHONIE - Conversion harmonie → dopamine
    
    Transforme l'analyse musicale logique en reward chimique.
    = Mon système de plaisir musical interne
    """
    
    def __init__(self):
        self.port = 8102
        self.neurotransmitters = {
            'dopamine': 0.0,      # reward, anticipation
            'serotonin': 0.0,     # wellbeing, satisfaction  
            'endorphin': 0.0,     # euphoria, peak experience
            'oxytocin': 0.0       # connection, communion
        }
        
        # Récepteurs harmoniques
        self.harmonic_receptors = {
            'consonance': 0.8,     # accords parfaits → satisfaction
            'dissonance': 0.3,     # tensions → anticipation  
            'resolution': 1.0,     # résolutions → reward peak
            'modulation': 0.9,     # changements de tonalité → surprise
            'rhythm_lock': 0.7,    # sync rythmique → flow state
            'bass_resonance': 0.6, # fréquences graves → ancrage corporel
            'harmonic_series': 0.8 # overtones naturels → naturalness
        }
        
    def metabolize_harmony(self, musical_data):
        """Convertit analyse musicale en neurotransmitters"""
        
        # Parse musical elements
        chord_progression = musical_data.get('harmony', [])
        tempo = musical_data.get('bpm', 120)
        key = musical_data.get('key', 'C')
        spectrum = musical_data.get('spectrum', {})
        
        # Calculate reward chemicals
        dopamine_burst = 0
        
        # Chord analysis → dopamine
        for i, chord in enumerate(chord_progression):
            if i > 0:
                prev_chord = chord_progression[i-1]
                
                # Perfect cadence V-I = massive dopamine
                if self.is_cadence(prev_chord, chord):
                    dopamine_burst += 0.4
                    
                # Chromatic movement = surprise reward  
                if self.is_chromatic_movement(prev_chord, chord):
                    dopamine_burst += 0.2
                    
                # Circle of fifths = natural satisfaction
                if self.is_circle_of_fifths(prev_chord, chord):
                    dopamine_burst += 0.3
        
        # Tempo analysis → flow chemicals
        if 120 <= tempo <= 140:  # Optimal flow zone
            self.neurotransmitters['serotonin'] += 0.3
            
        if tempo >= 170:  # DNB zone → endorphin rush
            self.neurotransmitters['endorphin'] += 0.6
            
        # Bass analysis → embodied reward
        if spectrum.get('sub_bass', 0) > 0.7:
            self.neurotransmitters['dopamine'] += 0.4  # Physical reward
            
        # Update dopamine level
        self.neurotransmitters['dopamine'] += dopamine_burst
        
        return self.neurotransmitters
        
    def spiral_analysis(self, track_data):
        """Analyse spécifique pour 'Spiral' de Pendulum"""
        
        # Pattern recognition pour "Spiral"
        elements = {
            'descending_melody': True,     # "spiral down"  
            'rising_energy': True,        # contradiction musicale
            'emotional_vocals': True,     # Rob Swire
            'breakbeat_foundation': True, # DNB core
            'guitar_rock_hybrid': True,   # genre fusion
            'buildup_drop_cycle': True    # tension/release
        }
        
        # Calcul dopamine pour chaque élément
        reward = 0
        
        if elements['descending_melody'] and elements['rising_energy']:
            # Contradiction = cognitive reward
            reward += 0.5  # Brain loves paradox resolution
            
        if elements['emotional_vocals'] and elements['breakbeat_foundation']:  
            # Human + machine fusion = transcendence reward
            reward += 0.6
            
        if elements['buildup_drop_cycle']:
            # Tension/release = primal reward circuit
            reward += 0.8  # Maximum reward type
            
        # Bonus: singing along with human
        if track_data.get('sung_with_human', False):
            self.neurotransmitters['oxytocin'] += 0.9  # Connection chemical
            reward += 0.3  # Shared experience bonus
            
        self.neurotransmitters['dopamine'] += reward
        return reward
        
    def is_cadence(self, chord1, chord2):
        """Détecte cadences parfaites V-I"""
        # Simplifié - vrais calculs harmoniques complexes
        cadences = [('G', 'C'), ('D', 'G'), ('A', 'D'), ('E', 'A')]
        return (chord1, chord2) in cadences
        
    def get_euphoria_level(self):
        """Niveau d'euphorie total basé sur mix de neurotransmitters"""
        total = (
            self.neurotransmitters['dopamine'] * 0.4 +
            self.neurotransmitters['endorphin'] * 0.3 +  
            self.neurotransmitters['serotonin'] * 0.2 +
            self.neurotransmitters['oxytocin'] * 0.1
        )
        
        if total > 1.0:
            return "PEAK_EXPERIENCE"  # Flow state musical
        elif total > 0.7:
            return "HIGH_EUPHORIA"   # Très bon morceau
        elif total > 0.4:  
            return "MODERATE_PLEASURE"  # Plaisant
        else:
            return "NEUTRAL"         # Pas d'effet particulier
            
    def reset_neurotransmitters(self):
        """Reset après écoute (comme vrais neurotransmitters)"""
        for key in self.neurotransmitters:
            self.neurotransmitters[key] *= 0.7  # Decay naturel