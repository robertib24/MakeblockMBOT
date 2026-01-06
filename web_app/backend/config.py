"""
Configuration file for mBot IoT Gateway
"""

import os

# Serial Configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change to your Arduino port (COM3 on Windows)
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '../data/mbot_data.db')
DATA_RETENTION_DAYS = 30  # Keep data for 30 days

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Data Collection
SAMPLING_RATE_HZ = 10  # 10 Hz logging from Arduino
MAX_BUFFER_SIZE = 1000  # Maximum data points in memory buffer

# API Configuration
API_PREFIX = '/api'
CORS_ENABLED = True  # Enable CORS for local development

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FILE = os.path.join(os.path.dirname(__file__), '../data/gateway.log')
