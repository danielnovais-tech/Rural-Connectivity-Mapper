"""Configuration constants for Rural Connectivity Mapper."""

# Application version
APP_VERSION = "1.0.0-beta"

# Data storage
DATA_FILE_PATH = 'src/data/pontos.json'

# API Configuration
DEFAULT_API_HOST = '0.0.0.0'
DEFAULT_API_PORT = 5000

# Known providers
KNOWN_PROVIDERS = [
    'Starlink', 'Viasat', 'HughesNet', 'Claro', 'Vivo', 
    'TIM', 'Oi', 'Various', 'Unknown', 'Other'
]
