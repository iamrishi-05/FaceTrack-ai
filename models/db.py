import sqlite3
import os
from contextlib import contextmanager
from config import Config

# Helper context manager for database connections
@contextmanager
def get_db_connection():
    if Config.TURSO_DATABASE_URL and Config.TURSO_AUTH_TOKEN:
        try:
            import turso_serverless
            # Connect to Turso Cloud libSQL database over HTTP
            conn = turso_serverless.connect(
                Config.TURSO_DATABASE_URL,
                auth_token=Config.TURSO_AUTH_TOKEN
            )
            conn.row_factory = turso_serverless.Row
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
            return
        except Exception as e:
            print(f"[WARN] Failed to connect to Turso Cloud DB, falling back to local SQLite: {e}")

    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row  # Enables column access by name like dictionary
    conn.execute("PRAGMA foreign_keys = ON")  # Enforce foreign key constraints

    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initializes SQLite or Turso Cloud database for direct access Target Face Tracking."""
    if not (Config.TURSO_DATABASE_URL and Config.TURSO_AUTH_TOKEN):
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check settings table schema
        try:
            cursor.execute("PRAGMA table_info(settings)")
            settings_cols = [col[1] for col in cursor.fetchall()]
            if 'user_id' in settings_cols:
                cursor.execute("DROP TABLE IF EXISTS settings")
        except Exception:
            pass

        # Users Table (Clerk / Google accounts)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                google_id TEXT,
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 1. Targets Table (Target profiles to track)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                target_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                notes TEXT,
                photo_path TEXT,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Target Face Encodings Table (128D encodings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS target_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                target_id TEXT NOT NULL,
                encoding_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(target_id) REFERENCES targets(target_id) ON DELETE CASCADE
            )
        ''')
        
        # 3. Detection Logs Table (Detection history)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                target_id TEXT NOT NULL,
                target_name TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                confidence REAL,
                emotion TEXT,
                smile_detected INTEGER,
                blink_detected INTEGER,
                mask_detected INTEGER,
                snapshot_path TEXT,
                location_tag TEXT DEFAULT 'Primary Camera',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4. Settings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Insert Default Settings if not present
        default_settings = {
            'tolerance': str(Config.DEFAULT_TOLERANCE),
            'confidence_threshold': str(Config.DEFAULT_CONFIDENCE_THRESHOLD),
            'camera_index': str(Config.DEFAULT_CAMERA_INDEX),
            'audio_alert': 'true',
            'cooldown_seconds': '60'
        }
        
        for key, val in default_settings.items():
            cursor.execute("SELECT key FROM settings WHERE key = ?", (key,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, val))
                
        # Create indexes for optimized fast lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_date ON detection_logs(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_target ON detection_logs(target_id)')

    print("[DB] Direct-Access Target Tracking Database initialized successfully.")
