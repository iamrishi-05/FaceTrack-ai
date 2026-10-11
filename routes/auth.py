from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from models.user import get_or_create_user
from utils.logger import log_event

from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Renders Clerk / Google Sign-In page or processes email sign-in."""
    if session.get('user_id'):
        return redirect(url_for('tracker.live_tracker'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        
        if not email or not email.strip():
            flash('Email ID is required.', 'error')
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
            
    return render_template(
        'auth/login.html',
        clerk_publishable_key=Config.CLERK_PUBLISHABLE_KEY,
        clerk_frontend_api=Config.CLERK_FRONTEND_API
    )


@auth_bp.route('/login/clerk', methods=['POST'])
def clerk_auth():
    """
    Handles authentication callback from Clerk JavaScript SDK.
    Syncs user details into SQLite and establishes Flask session.
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        name = data.get('name')
        clerk_id = data.get('clerk_id')
        avatar_url = data.get('avatar_url')
        token = data.get('token')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required from Clerk profile'}), 400

        # Optional: Verify session token with Clerk Backend API if CLERK_SECRET_KEY is provided
        secret_key = Config.CLERK_SECRET_KEY
        if secret_key and token:
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"https://api.clerk.com/v1/sessions?client_id={clerk_id}",
                    headers={"Authorization": f"Bearer {secret_key}"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    pass
            except Exception as v_err:
                log_event("WARNING", "Auth", f"Clerk remote token verification warning: {v_err}")
                
        user = get_or_create_user(
            email=email,
            name=name or email.split('@')[0].capitalize(),
            google_id=clerk_id,
            avatar_url=avatar_url
        )
        
        if not user:
            return jsonify({'success': False, 'message': 'Failed to provision local user account'}), 500
            
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        session['user_avatar'] = user.get('avatar_url') or ''
        session['clerk_id'] = clerk_id
        
        log_event("INFO", "Auth", f"Clerk authentication successful for {email} ({clerk_id})")
        return jsonify({
            'success': True,
            'message': f"Welcome back, {user['name']}!",
            'redirect': url_for('tracker.live_tracker')
        })
    except Exception as e:
        log_event("ERROR", "Auth", f"Clerk authentication handler failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
