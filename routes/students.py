import os
import csv
import io
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, Response
from werkzeug.utils import secure_filename
from models.student import (
    get_all_students, get_student_by_id, get_student_by_student_id,
    add_student, update_student, delete_student, bulk_insert_students
)
from utils.decorators import login_required
from utils.logger import log_event
from config import Config

students_bp = Blueprint('students', __name__)

# Allowed image file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@students_bp.route('/students')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    semester = request.args.get('semester', '').strip()
    
    # Query matching students
    students = get_all_students(
        search_query=search_query if search_query else None,
        department=department if department else None,
        semester=semester if semester else None
    )
    
    # Unique lists for dropdown filters
    all_students_raw = get_all_students()
    departments = sorted(list(set(s['department'] for s in all_students_raw if s['department'])))
    semesters = sorted(list(set(s['semester'] for s in all_students_raw if s['semester'])))
    
    return render_template(
        'students/list.html', 
        students=students, 
        departments=departments, 
        semesters=semesters,
        selected_dept=department,
        selected_sem=semester,
        search_query=search_query,
        active_page='students'
    )

@students_bp.route('/students/register', methods=['GET', 'POST'])
@login_required
def register():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        
        # Profile image upload
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{student_id}_{file.filename}")
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                dest_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(dest_path)
                photo_path = f"uploads/{filename}"
                
        # Insert student
        success, msg = add_student(
            student_id, name, roll_number, email, phone, department, semester, photo_path
        )
        
        if success:
            flash(f"Student '{name}' registered successfully! Proceed to enroll their face.", "success")
            return redirect(url_for('students.profile', student_id=student_id, start_face_reg=True))
        else:
            flash(msg, "error")
            
    return render_template('students/register.html', active_page='students')

@students_bp.route('/students/edit/<int:db_id>', methods=['GET', 'POST'])
@login_required
def edit(db_id):
    student = get_student_by_id(db_id)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('students.index'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        
        # Profile image upload check
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{student['student_id']}_{file.filename}")
                os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                dest_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(dest_path)
                photo_path = f"uploads/{filename}"
                
        success, msg = update_student(
            db_id, name, roll_number, email, phone, department, semester, photo_path
        )
        
        if success:
            flash(msg, "success")
            return redirect(url_for('students.profile', student_id=student['student_id']))
        else:
            flash(msg, "error")
            
    return render_template('students/edit.html', student=student, active_page='students')

@students_bp.route('/students/delete/<student_id>', methods=['POST', 'GET'])
@login_required
def delete(student_id):
    # Enforce POST for security or allow GET if triggered from safe admin prompts
    success, msg = delete_student(student_id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "error")
    return redirect(url_for('students.index'))

@students_bp.route('/students/profile/<student_id>')
@login_required
def profile(student_id):
    student = get_student_by_student_id(student_id)
    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for('students.index'))
        
    # Check if face is enrolled
    from models.db import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM face_encodings WHERE student_id = ?", (student_id,))
        is_enrolled = cursor.fetchone() is not None
        
        # Fetch individual attendance summaries
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE student_id = ? AND status='Present'", (student_id,))
        present_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE student_id = ? AND status='Absent'", (student_id,))
        absent_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE student_id = ? AND status='Late'", (student_id,))
        late_count = cursor.fetchone()['count']
        
        # Recent logs
        cursor.execute("SELECT date, time, status, method, confidence, emotion FROM attendance WHERE student_id = ? ORDER BY date DESC, time DESC LIMIT 10", (student_id,))
        recent_attendance = cursor.fetchall()
        
    total_classes = present_count + absent_count + late_count
    attendance_rate = (present_count + late_count) / total_classes * 100 if total_classes > 0 else 0.0
    
    # Check query flags
    start_face_reg = request.args.get('start_face_reg') == 'True'
    
    return render_template(
        'students/profile.html', 
        student=student, 
        is_enrolled=is_enrolled,
        present_count=present_count,
        absent_count=absent_count,
        late_count=late_count,
        attendance_rate=round(attendance_rate, 1),
        recent_attendance=recent_attendance,
        start_face_reg=start_face_reg,
        active_page='students'
    )

@students_bp.route('/students/import', methods=['POST'])
@login_required
def import_csv():
    if 'csv_file' not in request.files:
        flash("No file part provided.", "error")
        return redirect(url_for('students.index'))
        
    file = request.files['csv_file']
    if file.filename == '':
        flash("No selected file.", "error")
        return redirect(url_for('students.index'))
        
    if not file.filename.endswith('.csv'):
        flash("Please upload a valid CSV file.", "error")
        return redirect(url_for('students.index'))
        
    try:
        # Read CSV file stream using Pandas
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)
        
        # Validate columns
        required_cols = {'student_id', 'name', 'roll_number', 'email', 'phone', 'department', 'semester'}
        missing = required_cols - set(df.columns)
        if missing:
            flash(f"CSV is missing required headers: {', '.join(missing)}", "error")
            return redirect(url_for('students.index'))
            
        students_list = []
        for index, row in df.iterrows():
            students_list.append((
                str(row['student_id']).strip().upper(),
                str(row['name']).strip(),
                str(row['roll_number']).strip(),
                str(row['email']).strip(),
                str(row['phone']).strip() if pd.notna(row['phone']) else None,
                str(row['department']).strip(),
                str(row['semester']).strip()
            ))
            
        inserted, errors = bulk_insert_students(students_list)
        
        if inserted > 0:
            flash(f"Successfully imported {inserted} students!", "success")
        if errors:
            for err in errors[:5]: # Show first 5 errors
                flash(err, "warning")
            if len(errors) > 5:
                flash(f"...and {len(errors) - 5} more issues were encountered.", "warning")
                
    except Exception as e:
        log_event("ERROR", "StudentManagement", f"Failed to parse CSV file upload: {str(e)}")
        flash(f"Failed to process CSV file: {str(e)}", "error")
        
    return redirect(url_for('students.index'))

@students_bp.route('/students/sample-csv')
@login_required
def sample_csv():
    """Generates a downloadable sample CSV template for administrators."""
    csv_data = "student_id,name,roll_number,email,phone,department,semester\n" \
               "FT-2026-0001,John Doe,CS-01,john.doe@facetrack.ai,9876543210,Computer Science,Semester 5\n" \
               "FT-2026-0002,Jane Smith,CS-02,jane.smith@facetrack.ai,9876543211,Computer Science,Semester 5\n"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=facetrack_sample_students.csv"}
    )

@students_bp.route('/students/enroll/<student_id>')
@login_required
def enroll(student_id):
    student = get_student_by_student_id(student_id)
    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for('students.index'))
    return render_template('students/enroll.html', student=student, active_page='students')
