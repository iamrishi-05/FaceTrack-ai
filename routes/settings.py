from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection
from models.admin import get_admin_by_id, update_admin_profile, change_admin_password
from services.backup_service import BackupService
from utils.decorators import login_required
from utils.logger import log_event

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    admin = get_admin_by_id(session['admin_id'])
    
    # Fetch active settings
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings_rows = cursor.fetchall()
        
    system_settings = {r['key']: r['value'] for r in settings_rows}
    
    # List backups
    backups = BackupService.list_backups()
    
    return render_template(
        'settings/index.html',
        admin=admin,
        settings=system_settings,
        backups=backups,
        active_page='settings'
    )

@settings_bp.route('/settings/profile', methods=['POST'])
@login_required
def profile():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    
    if not name or not email:
        flash("Name and email are mandatory fields.", "error")
        return redirect(url_for('settings.index'))
        
    success, msg = update_admin_profile(session['admin_id'], name, email)
    if success:
        session['name'] = name  # Update current session cache
        flash(msg, "success")
    else:
        flash(msg, "error")
        
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/password', methods=['POST'])
@login_required
def password():
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not old_password or not new_password or not confirm_password:
        flash("All password fields are required.", "error")
        return redirect(url_for('settings.index'))
        
    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for('settings.index'))
        
    success, msg = change_admin_password(session['admin_id'], old_password, new_password)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "error")
        
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/system', methods=['POST'])
@login_required
def system():
    # Capture settings keys
    tolerance = request.form.get('tolerance', '0.5').strip()
    confidence = request.form.get('confidence_threshold', '60.0').strip()
    camera = request.form.get('camera_index', '0').strip()
    theme = request.form.get('theme', 'dark').strip()
    start_time = request.form.get('attendance_start', '09:00').strip()
    
    updates = {
        'tolerance': tolerance,
        'confidence_threshold': confidence,
        'camera_index': camera,
        'theme': theme,
        'attendance_start': start_time
    }
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for key, val in updates.items():
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val))
        
        log_event("INFO", "Settings", "System settings updated successfully.")
        flash("System settings saved successfully.", "success")
    except Exception as e:
        log_event("ERROR", "Settings", f"Failed to save system settings: {str(e)}")
        flash(f"Failed to update settings: {str(e)}", "error")
        
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/backup', methods=['POST'])
@login_required
def backup():
    success, result = BackupService.backup_database()
    if success:
        flash(f"Database checkpoint '{result}' created successfully.", "success")
    else:
        flash(f"Database backup failed: {result}", "error")
    return redirect(url_for('settings.index'))

@settings_bp.route('/settings/restore/<filename>')
@login_required
def restore(filename):
    success, msg = BackupService.restore_database(filename)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect(url_for('settings.index'))
