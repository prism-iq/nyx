# Configuration stéréo
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024
CHANNELS = 2
FORMAT = 'float32'

# Limites temporelles
MAX_ANALYSE_DURATION = 30  # secondes max d'analyse
REAL_TIME_BUFFER = 5      # secondes de buffer temps réel

# Ports
PORT_GAUCHE = 8094
PORT_DROIT = 8095
PORT_FUSION = 8096

# DSP
WINDOW_SIZE = 2048
HOP_LENGTH = 512
N_MELS = 128