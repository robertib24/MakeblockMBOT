"""
Database module for mBot IoT Gateway
Handles SQLite operations for data storage and retrieval
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create measurements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                time_s REAL,
                phase INTEGER,
                pwm_left INTEGER,
                pwm_right INTEGER,
                speed_1 REAL,
                speed_2 REAL,
                angle_x REAL,
                gyro_y REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index on timestamp for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON measurements(timestamp)
        ''')

        # Create system log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                level VARCHAR(10),
                message TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def insert_measurement(self, data: Dict) -> int:
        """Insert a single measurement"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO measurements
            (time_s, phase, pwm_left, pwm_right, speed_1, speed_2, angle_x, gyro_y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('time_s'),
            data.get('phase'),
            data.get('pwm_left'),
            data.get('pwm_right'),
            data.get('speed_1'),
            data.get('speed_2'),
            data.get('angle_x'),
            data.get('gyro_y')
        ))

        last_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return last_id

    def get_latest(self, limit: int = 100) -> List[Dict]:
        """Get latest measurements"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM measurements
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_history(self, start_time: Optional[str] = None,
                   end_time: Optional[str] = None,
                   limit: int = 10000) -> List[Dict]:
        """Get historical data within time range"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM measurements WHERE 1=1'
        params = []

        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)

        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM measurements')
        total_count = cursor.fetchone()['count']

        cursor.execute('''
            SELECT MIN(timestamp) as first, MAX(timestamp) as last
            FROM measurements
        ''')
        time_range = cursor.fetchone()

        cursor.execute('''
            SELECT
                AVG(angle_x) as avg_angle,
                AVG(speed_1) as avg_speed_1,
                AVG(speed_2) as avg_speed_2
            FROM measurements
            WHERE timestamp > datetime('now', '-1 hour')
        ''')
        averages = cursor.fetchone()

        conn.close()

        return {
            'total_measurements': total_count,
            'first_measurement': time_range['first'],
            'last_measurement': time_range['last'],
            'avg_angle_1h': averages['avg_angle'],
            'avg_speed_1_1h': averages['avg_speed_1'],
            'avg_speed_2_1h': averages['avg_speed_2']
        }

    def cleanup_old_data(self, days: int = config.DATA_RETENTION_DAYS):
        """Remove data older than specified days"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute('''
            DELETE FROM measurements
            WHERE timestamp < ?
        ''', (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {deleted_count} old measurements")
        return deleted_count

    def log_event(self, level: str, message: str):
        """Log system event to database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO system_log (level, message)
            VALUES (?, ?)
        ''', (level, message))

        conn.commit()
        conn.close()
