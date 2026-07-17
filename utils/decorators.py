from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(f):
    """
    Decorator to restrict access to authenticated administrators only.
    Redirects to the login page if the user session is invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
