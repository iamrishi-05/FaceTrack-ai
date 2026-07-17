import os
import sys

print("=" * 60)
print("FaceTrack AI - Environment Verification Tool")
print("=" * 60)
print(f"Python Version: {sys.version}")
print(f"Current Directory: {os.getcwd()}")

# 1. Directory Checks
print("\n[1/4] Checking System Folders...")
required_folders = ['models', 'routes', 'services', 'static/css', 'static/js', 
                    'templates', 'dataset', 'backup', 'logs', 'reports', 'uploads', 'utils']
for folder in required_folders:
    if os.path.exists(folder):
        print(f"  [✓] {folder}/ exists")
    else:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"  [+] {folder}/ created")
        except Exception as e:
            print(f"  [✗] Failed to create {folder}/: {e}")

# 2. Dependency Checks
print("\n[2/4] Verifying Package Dependencies...")
libs = {
    'Flask': 'flask',
    'OpenCV': 'cv2',
    'NumPy': 'numpy',
    'Pandas': 'pandas',
    'OpenPyXL': 'openpyxl',
    'ReportLab': 'reportlab'
}

all_ok = True
for name, import_name in libs.items():
    try:
        __import__(import_name)
        print(f"  [✓] {name} is installed")
    except ImportError:
        print(f"  [✗] {name} is NOT installed")
        all_ok = False

# Special check for face_recognition and dlib
try:
    import face_recognition
    print("  [✓] face_recognition is installed")
except ImportError:
    print("  [!] face_recognition is NOT installed (Optional fallback mode will be active)")

# 3. Database Initialization
print("\n[3/4] Initializing Database Schema...")
try:
    from models.db import init_db
    init_db()
    print("  [✓] SQLite Database initialized successfully")
except Exception as e:
    print(f"  [✗] Database initialization failed: {e}")
    all_ok = False

# 4. Settings verification
print("\n[4/4] Verification Summary")
if all_ok:
    print("  [✓] Environment setup looks solid!")
else:
    print("  [!] Some dependencies are missing. Install them via: pip install -r requirements.txt")
print("=" * 60)
