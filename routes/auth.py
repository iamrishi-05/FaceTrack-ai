from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models.admin import verify_admin
from models.student import verify_student
from utils.logger import log_event

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to appropriate page
    if 'admin_id' in session:
        return redirect(url_for('dashboard.index'))
    if 'student_id' in session:
        return redirect(url_for('students.profile', student_id=session['student_id']))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template('auth/login.html')
            
        # 1. Attempt Administrator Authentication
        admin = verify_admin(username, password)
        if admin:
            session['admin_id'] = admin['id']
            session['username'] = admin['username']
            session['name'] = admin['name']
            session['role'] = 'admin'
            
            if remember:
                session.permanent = True
            else:
                session.permanent = False
                
            log_event("INFO", "Authentication", f"Admin user '{username}' logged in successfully.")
            flash(f"Welcome back, {admin['name']}!", "success")
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard.index'))

        # 2. Attempt Student Authentication (Username = Middle Name, Password = last 4 digits of Student ID)
        student = verify_student(username, password)
        if student:
            parts = student['name'].strip().split()
            middle_name = parts[1] if len(parts) >= 2 else (parts[0] if parts else student['name'])
            session['student_id'] = student['student_id']
            session['username'] = middle_name
            session['name'] = student['name']
            session['role'] = 'student'
            
            if remember:
                session.permanent = True
            else:
                session.permanent = False
                
            log_event("INFO", "Authentication", f"Student '{student['name']}' ({student['student_id']}) logged in successfully.")
            flash(f"Welcome back, {student['name']}!", "success")
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('students.profile', student_id=student['student_id']))

        log_event("WARNING", "Authentication", f"Failed login attempt for user '{username}'.")
        flash("Invalid username or password.", "error")
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    log_event("INFO", "Authentication", f"Admin user '{username}' logged out.")
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        # Since this runs locally on sqlite, we can instruct the user how to reset credentials directly
        log_event("INFO", "Authentication", f"Password recovery requested for: {email}")
        flash("Instructions to recover credentials have been logged. Please check system console or logs.", "info")
        return render_template('auth/login.html', recovery_instructions=True)
        
    return render_template('auth/forgot_password.html')
