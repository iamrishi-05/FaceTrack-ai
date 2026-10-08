from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.target import (
    get_all_targets, get_target_by_id, delete_target, 
    get_detection_logs, get_tracker_stats
)
from models.db import get_db_connection
from utils.logger import log_event

tracker_bp = Blueprint('tracker', __name__)

def check_auth():
    """Helper function to enforce user login."""
    if not session.get('user_id'):
        return False
    return True

@tracker_bp.route('/')
def live_tracker():
    """Main dashboard & live face tracking feed view (User Isolated)."""
    if not check_auth():
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    stats = get_tracker_stats(user_id)
    targets = get_all_targets(user_id)
    recent_detections = get_detection_logs(user_id, limit=10)
    return render_template(
        'tracker.html', 
        active_page='tracker', 
        stats=stats, 
        targets=targets,
        recent_detections=recent_detections
    )

@tracker_bp.route('/targets')
def targets_list():
    """Target directory page where user can manage their personal target input pictures."""
    if not check_auth():
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    targets = get_all_targets(user_id)
    return render_template('targets.html', active_page='targets', targets=targets)

@tracker_bp.route('/targets/delete/<target_id>', methods=['POST'])
def delete_target_route(target_id):
    """Deletes a target profile owned by logged-in user."""
    if not check_auth():
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    delete_target(user_id, target_id)
    flash(f'Target {target_id} deleted successfully.', 'success')
    return redirect(url_for('tracker.targets_list'))

@tracker_bp.route('/detections')
def detections_history():
    """Detection logs history table view for logged-in user."""
    if not check_auth():
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    target_id = request.args.get('target_id')
    date = request.args.get('date')
    logs = get_detection_logs(user_id, limit=200, target_id=target_id, date=date)
    targets = get_all_targets(user_id)
    return render_template('detections.html', active_page='detections', logs=logs, targets=targets)

@tracker_bp.route('/settings', methods=['GET', 'POST'])
def settings_view():
    """System settings view for logged-in user."""
    if not check_auth():
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            tolerance = request.form.get('tolerance', '0.5')
            audio_alert = 'true' if request.form.get('audio_alert') else 'false'
            cooldown = request.form.get('cooldown_seconds', '60')
            
            cursor.execute("INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, 'tolerance', ?)", (user_id, tolerance))
            cursor.execute("INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, 'audio_alert', ?)", (user_id, audio_alert))
            cursor.execute("INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, 'cooldown_seconds', ?)", (user_id, cooldown))
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('tracker.settings_view'))
            
        cursor.execute("SELECT key, value FROM settings WHERE user_id = ?", (user_id,))
        settings_rows = cursor.fetchall()
        settings_dict = {row['key']: row['value'] for row in settings_rows}
        
    return render_template('settings.html', active_page='settings', settings=settings_dict)
