import os

# Automatically load local .env file if present
_env_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')
if os.path.exists(_env_file):
    try:
        with open(_env_file, 'r', encoding='utf-8') as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
    except Exception as _e:
        print(f"[WARN] Failed to load .env file: {_e}")

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'facetrack-ai-super-secret-key-185934')

    # Clerk Authentication
    CLERK_PUBLISHABLE_KEY = os.environ.get('CLERK_PUBLISHABLE_KEY') or os.environ.get('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY', '')
    CLERK_SECRET_KEY = os.environ.get('CLERK_SECRET_KEY', '')
    
    # Automatically derive Frontend API domain from publishable key
    CLERK_FRONTEND_API = ''
    if CLERK_PUBLISHABLE_KEY:
        try:
            import base64
            _parts = CLERK_PUBLISHABLE_KEY.split('_')
            if len(_parts) >= 3:
                _b64 = _parts[2].rstrip('$')
                _b64 += '=' * ((4 - len(_b64) % 4) % 4)
                CLERK_FRONTEND_API = base64.b64decode(_b64).decode('utf-8').rstrip('$')
        except Exception:
            CLERK_FRONTEND_API = ''


    IS_VERCEL = bool(os.environ.get('VERCEL'))
    
    # Store writeable files in /tmp on Vercel
    BASE_DIR = '/tmp/facetrack_data' if IS_VERCEL else os.path.abspath(os.path.dirname(__file__))
    DB_NAME = 'database.db'
    DATABASE_PATH = os.path.join(BASE_DIR, DB_NAME)

    # Directories
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    DATASET_FOLDER = os.path.join(BASE_DIR, 'dataset')
    BACKUP_FOLDER = os.path.join(BASE_DIR, 'backup')
    LOGS_FOLDER = os.path.join(BASE_DIR, 'logs')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')

    # Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS

    # AI & Face Recognition settings
    DEFAULT_TOLERANCE = 0.5  # Face matching tolerance (0.4 - 0.6)
    DEFAULT_CONFIDENCE_THRESHOLD = 60.0  # Display confidence % threshold
    
    # Liveness Detection settings
    EYE_EAR_THRESHOLD = 0.22  # Below this threshold, eye is considered closed (blink)
    SMILE_THRESHOLD = 0.45  # Above this, mouth is considered smiling
    
    # Camera index
    DEFAULT_CAMERA_INDEX = 0
