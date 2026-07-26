from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from datetime import datetime
from models.db import get_db_connection
from models.student import get_all_students
from services.report_service import ReportService
from utils.decorators import login_required
from utils.logger import log_event

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports', methods=['GET', 'POST'])
@login_required
def index():
    # Fetch filter properties for lists dropdown
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT department FROM students WHERE department IS NOT NULL")
        departments = [row['department'] for row in cursor.fetchall()]
        
        # Load distinct subjects from database to support filtering
        cursor.execute("SELECT DISTINCT subject FROM attendance WHERE subject IS NOT NULL")
        db_subjects = [row['subject'] for row in cursor.fetchall()]
        
    default_subjects = ['Python', 'Software Engineering', 'Java']
    subjects = sorted(list(set(default_subjects + db_subjects)))
    students = get_all_students()
    
    if request.method == 'POST':
        # Handles export logic
        export_format = request.form.get('format', 'pdf').strip().lower()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        department = request.form.get('department', '').strip()
        student_id = request.form.get('student_id', '').strip()
        status = request.form.get('status', '').strip()
        subject = request.form.get('subject', '').strip()
        
        # Date defaults (Today)
        today_str = datetime.now().strftime('%Y-%m-%d')
        if not start_date: start_date = today_str
        if not end_date: end_date = today_str
        
        # Build Query
        query = '''
            SELECT a.student_id, a.date, a.time, a.subject, a.status, a.method, a.confidence, a.emotion,
                   s.name, s.roll_number, s.department, s.semester
            FROM attendance a
            INNER JOIN students s ON a.student_id = s.student_id
            WHERE a.date BETWEEN ? AND ?
        '''
        params = [start_date, end_date]
        
        filter_desc = f"Dates: {start_date} to {end_date}"
        
        if department:
            query += " AND s.department = ?"
            params.append(department)
            filter_desc += f" | Dept: {department}"
            
        if student_id:
            query += " AND s.student_id = ?"
            params.append(student_id)
            filter_desc += f" | Student ID: {student_id}"
            
        if status:
            query += " AND a.status = ?"
            params.append(status)
            filter_desc += f" | Status: {status}"

        if subject:
            query += " AND a.subject = ?"
            params.append(subject)
            filter_desc += f" | Lecture: {subject}"
            
        query += " ORDER BY a.date ASC, a.time ASC"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            records = cursor.fetchall()
            
        if not records or len(records) == 0:
            flash("No attendance logs found matching those filters.", "warning")
            return redirect(url_for('reports.index'))
            
        # Export as requested
        now_ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        if export_format == 'excel':
            excel_bytes = ReportService.generate_excel(records)
            return Response(
                excel_bytes,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition": f"attachment; filename=facetrack_report_{now_ts}.xlsx"}
            )
        else: # PDF default
            pdf_bytes = ReportService.generate_pdf(records, filter_desc)
            return Response(
                pdf_bytes,
                mimetype="application/pdf",
                headers={"Content-disposition": f"attachment; filename=facetrack_report_{now_ts}.pdf"}
            )
            
    return render_template(
        'reports/index.html',
        departments=departments,
        subjects=subjects,
        students=students,
        active_page='reports'
    )
