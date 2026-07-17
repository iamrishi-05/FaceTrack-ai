import logging
import os
from datetime import datetime
from config import Config
import sqlite3

# Ensure log directory exists
os.makedirs(Config.LOGS_FOLDER, exist_ok=True)
log_file_path = os.path.join(Config.LOGS_FOLDER, 'app.log')

# Setup default Python logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(module)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FaceTrackAI")

def log_event(level, module, message):
    """
    Logs an event to both the python file logger and the SQLite system_logs database.
    """
    # 1. Log to Python standard file logger
    level_upper = level.upper()
    if level_upper == 'DEBUG':
        logger.debug(f"{module} - {message}")
    elif level_upper == 'WARNING':
        logger.warning(f"{module} - {message}")
    elif level_upper == 'ERROR':
        logger.error(f"{module} - {message}")
    else:
        logger.info(f"{module} - {message}")
        
    # 2. Log to SQLite Database (Non-blocking fallback)
    try:
        # Import dynamically to avoid circular references
        from models.db import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_logs (log_level, module, message, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (level_upper, module, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    except Exception as e:
        # Fallback to printing directly if database logging fails
        print(f"[LOGGER ERROR] Failed to write log to DB: {e}")
