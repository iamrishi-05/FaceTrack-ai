import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'facetrack-ai-super-secret-key-185934')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')

    # Check if running on Vercel (read-only filesystem)
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
