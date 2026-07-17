from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import datetime
from models.db import get_db_connection
from utils.decorators import login_required

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance/scanner')
@login_required
def scanner():
    # Renders the WebRTC face recognition scan viewer
    from services.face_service import FACE_REC_AVAILABLE
    return render_template('attendance/scanner.html', face_rec_ready=FACE_REC_AVAILABLE, active_page='scanner')

@attendance_bp.route('/attendance/history')
@login_required
def history():
    # Filters parameters
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
    status_filter = request.args.get('status', '').strip()
    dept_filter = request.args.get('department', '').strip()
    search_query = request.args.get('search', '').strip()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build SQL query dynamically
        query = '''
            SELECT a.id, a.student_id, a.date, a.time, a.status, a.method, a.confidence, a.emotion, 
                   s.name, s.roll_number, s.department, s.semester, s.photo_path
            FROM attendance a
            INNER JOIN students s ON a.student_id = s.student_id
            WHERE 1=1
        '''
        params = []
        
        if date_filter:
            query += " AND a.date = ?"
            params.append(date_filter)
            
        if status_filter:
            query += " AND a.status = ?"
            params.append(status_filter)
            
        if dept_filter:
            query += " AND s.department = ?"
            params.append(dept_filter)
            
        if search_query:
            query += " AND (s.name LIKE ? OR s.student_id LIKE ? OR s.roll_number LIKE ?)"
            like_param = f"%{search_query}%"
            params.extend([like_param, like_param, like_param])
            
        query += " ORDER BY a.time DESC"
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Fetch stats for summary headers on history view
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) as absent
            FROM attendance
            WHERE date = ?
        ''', (date_filter,))
        daily_stats = cursor.fetchone()
        
        # Load unique values for dropdowns
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL")
        departments = [row['department'] for row in cursor.fetchall()]
        
    return render_template(
        'attendance/history.html',
        records=records,
        departments=departments,
        selected_date=date_filter,
        selected_status=status_filter,
        selected_dept=dept_filter,
        search_query=search_query,
        stats=daily_stats,
        active_page='history'
    )
