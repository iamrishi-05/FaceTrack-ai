import datetime
from models.db import get_db_connection
from utils.logger import log_event

def get_or_create_user(email, name=None, google_id=None, avatar_url=None):
    """
    Fetches an existing user account by Google email ID or creates a new one.
    Updates last_login timestamp automatically.
    """
    if not email:
        return None
        
    email = email.strip().lower()
    if not name:
        name = email.split('@')[0].replace('.', ' ').title()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if user:
            # Update last login and avatar if provided
            user_id = user['id']
            cursor.execute('''
                UPDATE users 
                SET last_login = ?, name = COALESCE(?, name), avatar_url = COALESCE(?, avatar_url)
                WHERE id = ?
            ''', (now_str, name, avatar_url, user_id))
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            updated_user = cursor.fetchone()
            log_event("INFO", "UserModel", f"User logged in: {email} (ID: {user_id})")
            return dict(updated_user)
        else:
            # Insert new user account
            cursor.execute('''
                INSERT INTO users (email, name, google_id, avatar_url, last_login)
                VALUES (?, ?, ?, ?, ?)
            ''', (email, name, google_id, avatar_url, now_str))
            
            new_id = cursor.lastrowid
            cursor.execute('SELECT * FROM users WHERE id = ?', (new_id,))
            new_user = cursor.fetchone()
            log_event("INFO", "UserModel", f"New user account created: {email} (ID: {new_id})")
            return dict(new_user)

def get_user_by_id(user_id):
    """Retrieves user account by user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
