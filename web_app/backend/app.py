"""
Flask Application for mBot IoT Gateway
Main REST API server
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import os
from datetime import datetime
import threading
import time

import config
from database import Database
from serial_parser import SerialParser

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__,
            static_folder='../frontend',
            static_url_path='')

if config.CORS_ENABLED:
    CORS(app)

# Initialize database and serial parser
db = Database()
serial_parser = SerialParser()

# In-memory buffer for real-time data
data_buffer = []
MAX_BUFFER = config.MAX_BUFFER_SIZE


def on_data_received(data: dict):
    """Callback when new data is received from Arduino"""
    # Add timestamp
    data['timestamp'] = datetime.now().isoformat()

    # Add to buffer
    data_buffer.append(data)
    if len(data_buffer) > MAX_BUFFER:
        data_buffer.pop(0)

    # Save to database
    try:
        db.insert_measurement(data)
    except Exception as e:
        logger.error(f"Failed to save measurement: {e}")


# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    """Serve the main dashboard"""
    return send_from_directory(app.static_folder, 'index.html')


# ==================== API ROUTES ====================

@app.route(f'{config.API_PREFIX}/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'online',
        'serial_connected': serial_parser.is_connected(),
        'serial_port': config.SERIAL_PORT,
        'buffer_size': len(data_buffer),
        'timestamp': datetime.now().isoformat()
    })


@app.route(f'{config.API_PREFIX}/data/latest', methods=['GET'])
def get_latest_data():
    """Get the latest data point"""
    last_data = serial_parser.get_last_data()

    if last_data:
        return jsonify({
            'success': True,
            'data': last_data
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No data available'
        }), 404


@app.route(f'{config.API_PREFIX}/data/buffer', methods=['GET'])
def get_buffer_data():
    """Get all data from in-memory buffer"""
    limit = request.args.get('limit', type=int, default=100)

    return jsonify({
        'success': True,
        'count': len(data_buffer),
        'data': data_buffer[-limit:]
    })


@app.route(f'{config.API_PREFIX}/data/history', methods=['GET'])
def get_history():
    """Get historical data from database"""
    start = request.args.get('start')
    end = request.args.get('end')
    limit = request.args.get('limit', type=int, default=10000)

    try:
        data = db.get_history(start_time=start, end_time=end, limit=limit)

        return jsonify({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route(f'{config.API_PREFIX}/data/export', methods=['GET'])
def export_data():
    """Export data as CSV"""
    start = request.args.get('start')
    end = request.args.get('end')

    try:
        data = db.get_history(start_time=start, end_time=end, limit=100000)

        # Generate CSV
        csv_lines = ['time_s,phase,pwm_left,pwm_right,speed_1,speed_2,angle_x,gyro_y,timestamp']

        for row in data:
            csv_lines.append(f"{row['time_s']},{row['phase']},{row['pwm_left']},"
                           f"{row['pwm_right']},{row['speed_1']},{row['speed_2']},"
                           f"{row['angle_x']},{row['gyro_y']},{row['timestamp']}")

        csv_content = '\n'.join(csv_lines)

        return csv_content, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=mbot_data_export.csv'
        }

    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route(f'{config.API_PREFIX}/statistics', methods=['GET'])
def get_statistics():
    """Get database statistics"""
    try:
        stats = db.get_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route(f'{config.API_PREFIX}/control/start', methods=['POST'])
def start_experiment():
    """Send START command to Arduino"""
    try:
        serial_parser.send_start_command()
        db.log_event('INFO', 'Experiment started')

        return jsonify({
            'success': True,
            'message': 'START command sent to Arduino'
        })
    except Exception as e:
        logger.error(f"Error sending start command: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route(f'{config.API_PREFIX}/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'success': True,
        'config': {
            'serial_port': config.SERIAL_PORT,
            'baudrate': config.SERIAL_BAUDRATE,
            'sampling_rate': config.SAMPLING_RATE_HZ,
            'data_retention_days': config.DATA_RETENTION_DAYS
        }
    })


# ==================== BACKGROUND TASKS ====================

def cleanup_task():
    """Background task to cleanup old data"""
    while True:
        try:
            time.sleep(24 * 3600)  # Run once per day
            deleted = db.cleanup_old_data()
            logger.info(f"Cleanup task: deleted {deleted} old records")
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


# ==================== APPLICATION STARTUP ====================

def startup():
    """Initialize application on startup"""
    logger.info("Starting mBot IoT Gateway...")

    # Start serial parser
    serial_parser.start(callback=on_data_received)

    # Start cleanup task in background
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

    logger.info("mBot IoT Gateway started successfully")


def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down mBot IoT Gateway...")
    serial_parser.stop()
    logger.info("mBot IoT Gateway stopped")


# ==================== MAIN ====================

if __name__ == '__main__':
    try:
        startup()
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.FLASK_DEBUG,
            use_reloader=False  # Disable reloader to avoid double startup
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        shutdown()
