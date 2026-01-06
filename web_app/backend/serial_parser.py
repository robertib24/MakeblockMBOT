"""
Serial Parser for mBot IoT Gateway
Handles communication with Arduino and data parsing
"""

import serial
import logging
import threading
import time
from typing import Optional, Callable, Dict
import config

logger = logging.getLogger(__name__)


class SerialParser:
    def __init__(self, port: str = config.SERIAL_PORT,
                 baudrate: int = config.SERIAL_BAUDRATE,
                 timeout: float = config.SERIAL_TIMEOUT):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable] = None
        self.last_data: Optional[Dict] = None

    def connect(self) -> bool:
        """Connect to Arduino"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for Arduino to reset
            logger.info(f"Connected to Arduino on {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False

    def disconnect(self):
        """Disconnect from Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Disconnected from Arduino")

    def send_start_command(self):
        """Send START command to Arduino"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(b'S')
            logger.info("Sent START command to Arduino")

    def parse_csv_line(self, line: str) -> Optional[Dict]:
        """
        Parse CSV line from Arduino
        Format: time,phase,pwm_left,pwm_right,speed_1,speed_2,angleX,gyroY
        """
        try:
            # Skip comments and headers
            if line.startswith('#') or line.startswith('=') or 'CSV Header' in line:
                return None

            parts = line.strip().split(',')

            if len(parts) != 8:
                return None

            data = {
                'time_s': float(parts[0]),
                'phase': int(parts[1]),
                'pwm_left': int(parts[2]),
                'pwm_right': int(parts[3]),
                'speed_1': float(parts[4]),
                'speed_2': float(parts[5]),
                'angle_x': float(parts[6]),
                'gyro_y': float(parts[7])
            }

            return data

        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse line: {line} - Error: {e}")
            return None

    def read_loop(self):
        """Main read loop running in separate thread"""
        logger.info("Serial read loop started")

        while self.is_running:
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    if self.serial_conn.in_waiting > 0:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()

                        if line:
                            # Log raw line for debugging
                            if not line.startswith('#') and 'CSV Header' not in line:
                                data = self.parse_csv_line(line)

                                if data:
                                    self.last_data = data

                                    # Call callback if registered
                                    if self.callback:
                                        self.callback(data)
                            else:
                                logger.debug(f"Arduino: {line}")

                else:
                    logger.warning("Serial connection lost, attempting to reconnect...")
                    time.sleep(5)
                    self.connect()

            except serial.SerialException as e:
                logger.error(f"Serial exception: {e}")
                time.sleep(5)
                try:
                    self.connect()
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Unexpected error in read loop: {e}")
                time.sleep(1)

        logger.info("Serial read loop stopped")

    def start(self, callback: Optional[Callable] = None):
        """Start reading from serial port in background thread"""
        if self.is_running:
            logger.warning("Serial parser already running")
            return

        self.callback = callback
        self.is_running = True

        if not self.serial_conn or not self.serial_conn.is_open:
            if not self.connect():
                logger.error("Cannot start serial parser - connection failed")
                self.is_running = False
                return

        self.thread = threading.Thread(target=self.read_loop, daemon=True)
        self.thread.start()
        logger.info("Serial parser started")

    def stop(self):
        """Stop reading from serial port"""
        self.is_running = False

        if self.thread:
            self.thread.join(timeout=5)

        self.disconnect()
        logger.info("Serial parser stopped")

    def get_last_data(self) -> Optional[Dict]:
        """Get the last received data"""
        return self.last_data

    def is_connected(self) -> bool:
        """Check if connected to Arduino"""
        return self.serial_conn is not None and self.serial_conn.is_open
