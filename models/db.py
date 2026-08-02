import sqlite3
import os
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
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
    """Initializes the SQLite database with all tables and a default administrator."""
    # Ensure database file path folder exists
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Admins Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # 2. Students Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                roll_number TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                department TEXT NOT NULL,
                semester TEXT NOT NULL,
                photo_path TEXT,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. Face Encodings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                encoding_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
            )
        ''')
        
        # 4. Attendance Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                subject TEXT DEFAULT 'Python',
                status TEXT NOT NULL,
                method TEXT DEFAULT 'Face',
                confidence REAL,
                emotion TEXT,
                smile_detected INTEGER,
                blink_detected INTEGER,
                mask_detected INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                UNIQUE(student_id, date, subject)
            )
        ''')
        
        # Ensure subject column exists if database was created prior
        cursor.execute("PRAGMA table_info(attendance)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'subject' not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN subject TEXT DEFAULT 'Python'")

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
        
        # 6. Settings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Create indexes for optimized queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_face_encodings_student ON face_encodings(student_id)')

        # Insert Default Administrator if not exists
        cursor.execute("SELECT id FROM admins WHERE username = 'admin'")
        if not cursor.fetchone():
            default_hashed_pwd = generate_password_hash("adminpassword")
            cursor.execute('''
                INSERT INTO admins (username, password_hash, email, name)
                VALUES (?, ?, ?, ?)
            ''', ("admin", default_hashed_pwd, "admin@facetrack.ai", "System Administrator"))
            print("[DB] Default admin created (admin / adminpassword)")
            
        # Auto-seed student records if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM students")
        if cursor.fetchone()['count'] == 0:
            seed_file = os.path.join(os.path.dirname(__file__), 'students_seed.json')
            if os.path.exists(seed_file):
                import json
                try:
                    with open(seed_file, 'r', encoding='utf-8') as f:
                        students_data = json.load(f)
                    for s in students_data:
                        cursor.execute('''
                            INSERT OR IGNORE INTO students (student_id, name, roll_number, email, phone, department, semester)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (s['student_id'], s['name'], s['roll_number'], s['email'], s.get('phone'), s['department'], s['semester']))
                    print(f"[DB] Auto-seeded {len(students_data)} student records into database.")
                except Exception as e:
                    print(f"[DB] Failed to auto-seed students: {e}")
                
        # Insert Default Settings if not exists
        default_settings = {
            'tolerance': str(Config.DEFAULT_TOLERANCE),
            'confidence_threshold': str(Config.DEFAULT_CONFIDENCE_THRESHOLD),
            'camera_index': str(Config.DEFAULT_CAMERA_INDEX),
            'theme': 'dark',
            'attendance_start': '08:00',
            'attendance_end': '18:00'
        }
        
        for key, val in default_settings.items():
            cursor.execute("SELECT key FROM settings WHERE key = ?", (key,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, val))
                
    print("[DB] Database initialized successfully.")
