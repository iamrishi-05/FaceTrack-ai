from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from models.user import get_or_create_user
from utils.logger import log_event

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Renders Google Sign-In page or processes email sign-in."""
    if session.get('user_id'):
        return redirect(url_for('tracker.live_tracker'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        
        if not email or not email.strip():
            flash('Google Email ID is required.', 'error')
            return redirect(url_for('auth.login'))
            
        user = get_or_create_user(email=email.strip(), name=name)
        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            session['user_avatar'] = user.get('avatar_url') or ''
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('tracker.live_tracker'))
        else:
            flash('Failed to sign in. Please try again.', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/login/google', methods=['POST'])
def google_auth():
    """
    Handles Google Sign-In token or OAuth payload sent from client side.
    Creates or updates the user account and stores session.
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        name = data.get('name')
        google_id = data.get('google_id')
        avatar_url = data.get('avatar_url')
        
        if not email:
            return jsonify({'success': False, 'message': 'Google email is required'}), 400
            
        user = get_or_create_user(
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=avatar_url
        )
        
        if not user:
            return jsonify({'success': False, 'message': 'Account creation failed'}), 500
            
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        session['user_avatar'] = user.get('avatar_url') or ''
        
        log_event("INFO", "Auth", f"Google Authentication successful for {email}")
        return jsonify({
            'success': True,
            'message': f'Welcome, {user["name"]}!',
            'redirect': url_for('tracker.live_tracker')
        })
    except Exception as e:
        log_event("ERROR", "Auth", f"Google authentication failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/logout')
def logout():
    """Clears user session and logs out."""
    email = session.get('user_email', 'User')
    session.clear()
    log_event("INFO", "Auth", f"User logged out: {email}")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
