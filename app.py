import os
from flask import Flask, send_from_directory, render_template
from config import Config
from models.db import init_db
from utils.logger import log_event

# 1. Initialize Flask Application
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(Config)

# Ensure essential directories are provisioned on start
for folder in [Config.UPLOAD_FOLDER, Config.DATASET_FOLDER, Config.BACKUP_FOLDER, Config.LOGS_FOLDER, Config.REPORTS_FOLDER]:
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print(f"[WARN] Failed to create folder {folder}: {e}")

# Initialize database schemas
try:
    init_db()
except Exception as e:
    print(f"[FATAL] Failed to initialize SQLite database: {e}")

# 2. Register Blueprints
from routes.auth import auth_bp
from routes.students import students_bp
from routes.attendance import attendance_bp
from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.settings import settings_bp
from routes.reports import reports_bp

app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(reports_bp)

# 3. Securely serve profile images uploaded to directory
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serves student profile pictures securely from the local uploads folder."""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

# 4. Global Error Handlers (Commercial quality UX)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', active_page=''), 404

@app.errorhandler(500)
def server_error(e):
    log_event("ERROR", "System", f"Internal Server Error: {str(e)}")
    return render_template('base.html', active_page=''), 500

# 5. Boot Application
if __name__ == '__main__':
    log_event("INFO", "System", "FaceTrack AI application booted successfully.")
    ssl_ctx = None
    if os.environ.get('ENABLE_SSL') == 'true' and os.path.exists('cert.pem') and os.path.exists('key.pem'):
        ssl_ctx = ('cert.pem', 'key.pem')
        log_event("INFO", "System", "HTTPS SSL context enabled for mobile browser camera support.")
    # Run on all network interfaces to allow local network connections
    app.run(host='0.0.0.0', port=5001, debug=True, ssl_context=ssl_ctx)
