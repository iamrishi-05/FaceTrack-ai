from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime, timedelta
from models.db import get_db_connection
from utils.decorators import login_required
from utils.logger import log_event

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Total Students Count
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE status='Active'")
        total_students = cursor.fetchone()['count']
        
        # 2. Present Today Count (Present + Late)
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE date = ? AND status IN ('Present', 'Late')", (today_str,))
        present_today = cursor.fetchone()['count']
        
        # 3. Absent Today
        absent_today = max(0, total_students - present_today)
        
        # 4. Attendance Percentage
        attendance_percentage = (present_today / total_students * 100) if total_students > 0 else 0.0
        
        # 5. Recent Logs marked today
        cursor.execute('''
            SELECT a.time, a.status, a.confidence, s.name, s.roll_number, s.department
            FROM attendance a
            INNER JOIN students s ON a.student_id = s.student_id
            WHERE a.date = ?
            ORDER BY a.time DESC
            LIMIT 5
        ''', (today_str,))
        recent_logs = cursor.fetchall()
        
        # 6. System Warnings (Unknown face warnings, low attendance)
        cursor.execute('''
            SELECT timestamp, message, log_level FROM system_logs
            WHERE log_level IN ('WARNING', 'ERROR')
            ORDER BY timestamp DESC
            LIMIT 3
        ''')
        warnings = cursor.fetchall()
        
        # 7. Donut Chart Data (Present vs Absent today)
        donut_data = {
            'present': present_today,
            'absent': absent_today
        }
        
    return render_template(
        'dashboard/index.html',
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        attendance_percentage=round(attendance_percentage, 1),
        recent_logs=recent_logs,
        warnings=warnings,
        donut_data=donut_data,
        active_page='dashboard'
    )

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Weekly Trend (Last 7 days of attendance counts)
        weekly_trend = []
        for i in range(6, -1, -1):
            date_n = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_label = (datetime.now() - timedelta(days=i)).strftime('%a')
            
            cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE date = ?", (date_n,))
            count = cursor.fetchone()['count']
            weekly_trend.append({'label': day_label, 'count': count})
            
        # 2. Department Wise Distribution (Present students count today grouped by department)
        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT s.department, COUNT(a.id) as count
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = ?
            WHERE s.status='Active'
            GROUP BY s.department
        ''', (today_str,))
        dept_data = [dict(row) for row in cursor.fetchall()]
        
        # 3. Emotion Distribution summary
        cursor.execute('''
            SELECT emotion, COUNT(*) as count
            FROM attendance
            WHERE emotion IS NOT NULL AND emotion != ''
            GROUP BY emotion
        ''')
        emotion_data = [dict(row) for row in cursor.fetchall()]
        
        # 4. Highest Attendance Performers (Top 5)
        # Check-in rate = count(presents) / total records
        cursor.execute('''
            SELECT s.student_id, s.name, s.department,
                   COUNT(a.id) as attended_classes
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
            GROUP BY s.student_id
            ORDER BY attended_classes DESC
            LIMIT 5
        ''')
        top_performers = [dict(row) for row in cursor.fetchall()]
        
        # 5. Lowest Attendance / At Risk Students (Bottom 5)
        # For demo, select students with fewest check-ins
        cursor.execute('''
            SELECT s.student_id, s.name, s.department,
                   COUNT(a.id) as attended_classes
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
            GROUP BY s.student_id
            ORDER BY attended_classes ASC
            LIMIT 5
        ''')
        at_risk = [dict(row) for row in cursor.fetchall()]
        
    return render_template(
        'analytics/index.html',
        weekly_trend=weekly_trend,
        dept_data=dept_data,
        emotion_data=emotion_data,
        top_performers=top_performers,
        at_risk=at_risk,
        active_page='analytics'
    )
