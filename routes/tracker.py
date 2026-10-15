from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, Response
from datetime import datetime
from models.target import (
    get_all_targets, get_target_by_id, delete_target, 
    get_detection_logs, get_tracker_stats
)
from models.db import get_db_connection
from utils.logger import log_event
from services.report_service import ReportService

tracker_bp = Blueprint('tracker', __name__)

@tracker_bp.before_request
def require_authentication():
    if not session.get('user_id') and not session.get('admin_id'):
        return redirect(url_for('auth.login'))

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

@tracker_bp.route('/reports', methods=['GET', 'POST'])
def reports_view():
    """Reports & export dashboard for biometric detection logs."""
    targets = get_all_targets()
    stats = get_tracker_stats()
    
    if request.method == 'POST':
        export_format = request.form.get('format', 'pdf').strip().lower()
        target_id = request.form.get('target_id', '').strip() or None
        start_date = request.form.get('start_date', '').strip() or None
        end_date = request.form.get('end_date', '').strip() or None
        min_confidence = request.form.get('min_confidence', '').strip() or None
        
        records = get_detection_logs(
            limit=None, 
            target_id=target_id, 
            start_date=start_date, 
            end_date=end_date,
            min_confidence=min_confidence
        )
        
        if not records:
            flash("No detection records found matching the chosen filter criteria.", "warning")
            return redirect(url_for('tracker.reports_view'))
            
        now_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        desc_parts = []
        if target_id:
            tgt_match = next((t['name'] for t in targets if t['target_id'] == target_id), target_id)
            desc_parts.append(f"Target: {tgt_match} ({target_id})")
        else:
            desc_parts.append("All Targets")
        if start_date and end_date:
            desc_parts.append(f"Date Range: {start_date} to {end_date}")
        elif start_date:
            desc_parts.append(f"Since: {start_date}")
        elif end_date:
            desc_parts.append(f"Until: {end_date}")
        if min_confidence:
            desc_parts.append(f"Min Conf: {min_confidence}%")
        filter_desc = " | ".join(desc_parts)

        if export_format == 'excel':
            excel_bytes = ReportService.generate_detection_excel(records)
            return Response(
                excel_bytes,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition": f"attachment; filename=facetrack_intelligence_logs_{now_ts}.xlsx"}
            )
        else:
            pdf_bytes = ReportService.generate_detection_pdf(records, filter_desc)
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={"Content-disposition": f"attachment; filename=facetrack_intelligence_dossier_{now_ts}.pdf"}
            )

    # GET request - load preview logs
    target_id_filter = request.args.get('target_id')
    date_filter = request.args.get('date')
    preview_logs = get_detection_logs(limit=25, target_id=target_id_filter, date=date_filter)
    
    return render_template(
        'reports.html',
        active_page='reports',
        targets=targets,
        stats=stats,
        preview_logs=preview_logs
    )

@tracker_bp.route('/detections/export')
def export_logs():
    """One-click export endpoint for detection logs."""
    export_format = request.args.get('format', 'pdf').strip().lower()
    target_id = request.args.get('target_id', '').strip() or None
    date = request.args.get('date', '').strip() or None
    start_date = request.args.get('start_date', '').strip() or None
    end_date = request.args.get('end_date', '').strip() or None
    min_confidence = request.args.get('min_confidence', '').strip() or None
    
    # If a single date was specified
    if date and not start_date and not end_date:
        start_date = date
        end_date = date
        
    records = get_detection_logs(
        limit=None,
        target_id=target_id,
        date=date if not (start_date and end_date) else None,
        start_date=start_date,
        end_date=end_date,
        min_confidence=min_confidence
    )
    
    if not records:
        flash("No detection records found for download.", "warning")
        return redirect(url_for('tracker.detections_history'))
        
    targets = get_all_targets()
    now_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    desc_parts = []
    if target_id:
        tgt_match = next((t['name'] for t in targets if t['target_id'] == target_id), target_id)
        desc_parts.append(f"Target: {tgt_match} ({target_id})")
    else:
        desc_parts.append("All Targets")
    if date:
        desc_parts.append(f"Date: {date}")
    elif start_date and end_date:
        desc_parts.append(f"Dates: {start_date} to {end_date}")
    filter_desc = " | ".join(desc_parts)

    if export_format == 'excel':
        excel_bytes = ReportService.generate_detection_excel(records)
        return Response(
            excel_bytes,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-disposition": f"attachment; filename=facetrack_detection_logs_{now_ts}.xlsx"}
        )
    else:
        pdf_bytes = ReportService.generate_detection_pdf(records, filter_desc)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-disposition": f"attachment; filename=facetrack_detection_dossier_{now_ts}.pdf"}
        )

