from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.target import (
    get_all_targets, get_target_by_id, delete_target, 
    get_detection_logs, get_tracker_stats
)
from models.db import get_db_connection
from utils.logger import log_event

tracker_bp = Blueprint('tracker', __name__)

@tracker_bp.route('/')
def live_tracker():
    """Main dashboard & live face tracking feed view."""
    stats = get_tracker_stats()
    targets = get_all_targets()
    recent_detections = get_detection_logs(limit=10)
    return render_template(
        'tracker.html', 
        active_page='tracker', 
        stats=stats, 
        targets=targets,
        recent_detections=recent_detections
    )

@tracker_bp.route('/targets')
def targets_list():
    """Target directory page where admins can manage and upload target input pictures."""
    targets = get_all_targets()
    return render_template('targets.html', active_page='targets', targets=targets)

@tracker_bp.route('/targets/delete/<target_id>', methods=['POST'])
def delete_target_route(target_id):
    """Deletes a target profile and its encodings."""
    delete_target(target_id)
    flash(f'Target {target_id} deleted successfully.', 'success')
    return redirect(url_for('tracker.targets_list'))

@tracker_bp.route('/detections')
def detections_history():
    """Detection logs history table view."""
    target_id = request.args.get('target_id')
    date = request.args.get('date')
    logs = get_detection_logs(limit=200, target_id=target_id, date=date)
    targets = get_all_targets()
    return render_template('detections.html', active_page='detections', logs=logs, targets=targets)

@tracker_bp.route('/settings', methods=['GET', 'POST'])
def settings_view():
    """System settings view."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            tolerance = request.form.get('tolerance', '0.5')
            audio_alert = 'true' if request.form.get('audio_alert') else 'false'
            cooldown = request.form.get('cooldown_seconds', '60')
            
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tolerance', ?)", (tolerance,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('audio_alert', ?)", (audio_alert,))
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('cooldown_seconds', ?)", (cooldown,))
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('tracker.settings_view'))
            
        cursor.execute("SELECT key, value FROM settings")
        settings_rows = cursor.fetchall()
        settings_dict = {row['key']: row['value'] for row in settings_rows}
        
    return render_template('settings.html', active_page='settings', settings=settings_dict)
