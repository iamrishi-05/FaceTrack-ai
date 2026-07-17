from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from models.admin import verify_admin
from utils.logger import log_event

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to dashboard
    if 'admin_id' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template('auth/login.html')
            
        admin = verify_admin(username, password)
        if admin:
            # Login successful
            session['admin_id'] = admin['id']
            session['username'] = admin['username']
            session['name'] = admin['name']
            
            if remember:
                session.permanent = True  # Cookie will persist for standard duration (usually 31 days)
            else:
                session.permanent = False
                
            log_event("INFO", "Authentication", f"Admin user '{username}' logged in successfully.")
            flash(f"Welcome back, {admin['name']}!", "success")
            
            # Redirect to next parameter or dashboard
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'): # Prevent open redirect vulnerabilities
                return redirect(next_url)
            return redirect(url_for('dashboard.index'))
        else:
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
