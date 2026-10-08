import os
from flask import Flask, send_from_directory, render_template
from config import Config
from models.db import init_db
from utils.logger import log_event

# 1. Initialize Flask Application
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(Config)

# Ensure essential data directories are provisioned on start
for folder in [Config.UPLOAD_FOLDER, Config.LOGS_FOLDER, os.path.join(Config.UPLOAD_FOLDER, 'targets')]:
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print(f"[WARN] Failed to create folder {folder}: {e}")

# Initialize Target Tracking database schema with Multi-Tenant User Accounts
try:
    init_db()
except Exception as e:
    print(f"[FATAL] Failed to initialize SQLite database: {e}")

# 2. Register Target Tracking & Authentication Blueprints
from routes.auth import auth_bp
from routes.tracker import tracker_bp
from routes.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(tracker_bp)
app.register_blueprint(api_bp)

# 3. Securely serve target profile photos and uploads
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serves target profile pictures and snapshots from the uploads folder."""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

# 4. Global Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', active_page=''), 404

@app.errorhandler(500)
def server_error(e):
    log_event("ERROR", "System", f"Internal Server Error: {str(e)}")
    return render_template('base.html', active_page=''), 500

# 5. Boot Application
if __name__ == '__main__':
    log_event("INFO", "System", "FaceTrack AI Target Detector booted successfully.")
    ssl_ctx = None
    if os.environ.get('ENABLE_SSL') == 'true' and os.path.exists('cert.pem') and os.path.exists('key.pem'):
        ssl_ctx = ('cert.pem', 'key.pem')
        log_event("INFO", "System", "HTTPS SSL context enabled for mobile camera support.")
    
    app.run(host='0.0.0.0', port=5001, debug=True, ssl_context=ssl_ctx)
