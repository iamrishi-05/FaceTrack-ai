import logging
import os
from datetime import datetime
from config import Config

# Setup Python handlers safely
handlers = [logging.StreamHandler()]

try:
    os.makedirs(Config.LOGS_FOLDER, exist_ok=True)
    log_file_path = os.path.join(Config.LOGS_FOLDER, 'app.log')
    handlers.append(logging.FileHandler(log_file_path))
except Exception as e:
    print(f"[LOGGER WARN] Could not initialize file handler: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(module)s: %(message)s',
    handlers=handlers
)
logger = logging.getLogger("FaceTrackAI")

def log_event(level, module, message):
    """
    Logs an event to both the python standard logger and the SQLite system_logs database.
    """
    level_upper = level.upper()
    if level_upper == 'DEBUG':
        logger.debug(f"{module} - {message}")
    elif level_upper == 'WARNING':
        logger.warning(f"{module} - {message}")
    elif level_upper == 'ERROR':
        logger.error(f"{module} - {message}")
    else:
        logger.info(f"{module} - {message}")
        
    # Log to SQLite Database (Non-blocking fallback)
    try:
        from models.db import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_logs (log_level, module, message, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (level_upper, module, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    except Exception as e:
        print(f"[LOGGER ERROR] Failed to write log to DB: {e}")
