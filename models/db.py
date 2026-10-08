import sqlite3
import os
from contextlib import contextmanager
from config import Config

# Helper context manager for database connections
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
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
    """Initializes the SQLite database with multi-user account isolation and target tracking."""
    # Ensure database file directory exists
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if old legacy schema exists without user_id column
        cursor.execute("PRAGMA table_info(targets)")
        columns = [col[1] for col in cursor.fetchall()]
        if columns and 'user_id' not in columns:
            print("[DB Migration] Upgrading schema for Multi-User Account Isolation...")
            cursor.execute("DROP TABLE IF EXISTS targets")
            cursor.execute("DROP TABLE IF EXISTS target_encodings")
            cursor.execute("DROP TABLE IF EXISTS detection_logs")
            cursor.execute("DROP TABLE IF EXISTS settings")

        cursor.execute("PRAGMA table_info(settings)")
        settings_cols = [col[1] for col in cursor.fetchall()]
        if settings_cols and 'user_id' not in settings_cols:
            cursor.execute("DROP TABLE IF EXISTS settings")
        
        # 1. Users Table (Google OAuth & User Accounts)
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

        # 2. Targets Table (User-scoped target profiles to track)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                notes TEXT,
                photo_path TEXT,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 3. Target Face Encodings Table (User-scoped 128D encodings)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS target_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_id TEXT NOT NULL,
                encoding_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(target_id) REFERENCES targets(target_id) ON DELETE CASCADE
            )
        ''')
        
        # 4. Detection Logs Table (User-scoped detection history)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # 5. System Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                log_level TEXT NOT NULL,
                module TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')
        
        # 6. User Settings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (user_id, key),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes for optimized user-scoped queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_targets_user ON targets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detection_user_date ON detection_logs(user_id, date)')

    print("[DB] Multi-User Target Tracking Database initialized successfully.")
