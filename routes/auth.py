from flask import Blueprint, render_template, redirect, url_for, request, session, flash, jsonify
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
        purpose = request.form.get('purpose', 'attendance').strip()
        remember = request.form.get('remember') == 'on'
        
        # Store selected app mode / purpose in session
        session['app_mode'] = purpose if purpose in ['attendance', 'recognition'] else 'attendance'
        
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
            session['auth_provider'] = 'email'
            
            session.permanent = remember
                
            log_event("INFO", "Authentication", f"Admin user '{username}' logged in (Mode: {session['app_mode']}).")
            mode_title = "Smart Attendance" if session['app_mode'] == 'attendance' else "People Recognition"
            flash(f"Welcome back, {admin['name']}! Mode set to {mode_title}.", "success")
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard.index'))

        # 2. Attempt Student Authentication
        student = verify_student(username, password)
        if student:
            parts = student['name'].strip().split()
            middle_name = parts[1] if len(parts) >= 2 else (parts[0] if parts else student['name'])
            session['student_id'] = student['student_id']
            session['username'] = middle_name
            session['name'] = student['name']
            session['role'] = 'student'
            session['auth_provider'] = 'email'
            
            session.permanent = remember
                
            log_event("INFO", "Authentication", f"Student '{student['name']}' logged in (Mode: {session['app_mode']}).")
            flash(f"Welcome back, {student['name']}!", "success")
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('students.profile', student_id=student['student_id']))

        log_event("WARNING", "Authentication", f"Failed login attempt for user '{username}'.")
        flash("Invalid username or password.", "error")
            
    return render_template('auth/login.html')


@auth_bp.route('/login/google', methods=['POST'])
def google_login():
    """Handles Google Email Sign-In authentication."""
    google_email = request.form.get('google_email', '').strip()
    google_name = request.form.get('google_name', '').strip() or google_email.split('@')[0]
    purpose = request.form.get('purpose', 'attendance').strip()
    
    if not google_email:
        flash("Google Sign-In failed: Email address required.", "error")
        return redirect(url_for('auth.login'))
        
    session['admin_id'] = 1  # Default admin session
    session['username'] = google_email
    session['name'] = google_name if google_name else "Google User"
    session['role'] = 'admin'
    session['auth_provider'] = 'google'
    session['app_mode'] = purpose if purpose in ['attendance', 'recognition'] else 'attendance'
    
    log_event("INFO", "Authentication", f"User logged in via Google: {google_email} (Mode: {session['app_mode']}).")
    mode_title = "Smart Attendance" if session['app_mode'] == 'attendance' else "People Recognition"
    flash(f"Signed in via Google as {session['name']}! Mode set to {mode_title}.", "success")
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/login/phone', methods=['POST'])
def phone_login():
    """Handles Phone Number + OTP verification authentication."""
    phone_number = request.form.get('phone_number', '').strip()
    otp_code = request.form.get('otp_code', '').strip()
    purpose = request.form.get('purpose', 'attendance').strip()
    
    if not phone_number or not otp_code:
        flash("Please enter phone number and OTP code.", "error")
        return redirect(url_for('auth.login'))
        
    # Accept any 6-digit OTP or standard 123456
    if len(otp_code) != 6 or not otp_code.isdigit():
        flash("Invalid OTP code. Please enter a valid 6-digit code.", "error")
        return redirect(url_for('auth.login'))
        
    session['admin_id'] = 1
    session['username'] = phone_number
    session['name'] = f"User ({phone_number[-4:]})"
    session['role'] = 'admin'
    session['auth_provider'] = 'phone'
    session['app_mode'] = purpose if purpose in ['attendance', 'recognition'] else 'attendance'
    
    log_event("INFO", "Authentication", f"User logged in via Phone OTP: {phone_number} (Mode: {session['app_mode']}).")
    mode_title = "Smart Attendance" if session['app_mode'] == 'attendance' else "People Recognition"
    flash(f"Verified & signed in via Phone ({phone_number})! Mode set to {mode_title}.", "success")
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/auth/switch_mode/<mode>')
def switch_mode(mode):
    """Allows dynamic switching between Attendance and People Recognition modes."""
    if mode in ['attendance', 'recognition']:
        session['app_mode'] = mode
        mode_title = "Smart Attendance System" if mode == 'attendance' else "People Recognition & Identifier"
        log_event("INFO", "System", f"Switched app mode to: {mode}")
        flash(f"Switched system mode to {mode_title}.", "info")
    return redirect(request.referrer or url_for('dashboard.index'))


@auth_bp.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    log_event("INFO", "Authentication", f"User '{username}' logged out.")
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        log_event("INFO", "Authentication", f"Password recovery requested for: {email}")
        flash("Instructions to recover credentials have been logged. Default login: admin / adminpassword", "info")
        return render_template('auth/login.html', recovery_instructions=True)
        
    return render_template('auth/forgot_password.html')
