from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from models.db import get_db_connection

def get_admin_by_id(admin_id):
    """Retrieves an administrator record by its ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, name, last_login, created_at FROM admins WHERE id = ?", (admin_id,))
        return cursor.fetchone()

def get_admin_by_username(username):
    """Retrieves an administrator record by its username."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, name, last_login, created_at FROM admins WHERE username = ?", (username,))
        return cursor.fetchone()

def verify_admin(username, password):
    """
    Verifies administrator credentials.
    Returns the admin record and updates last login if correct, otherwise returns None.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cursor.fetchone()
        
        if admin and check_password_hash(admin['password_hash'], password):
            # Update last login timestamp
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE admins SET last_login = ? WHERE id = ?", (now, admin['id']))
            return {
                'id': admin['id'],
                'username': admin['username'],
                'email': admin['email'],
                'name': admin['name'],
                'last_login': now
            }
    return None

def change_admin_password(admin_id, old_password, new_password):
    """Verifies the old password and sets the new hashed password."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM admins WHERE id = ?", (admin_id,))
        admin = cursor.fetchone()
        
        if not admin or not check_password_hash(admin['password_hash'], old_password):
            return False, "Incorrect current password"
            
        new_hashed = generate_password_hash(new_password)
        cursor.execute("UPDATE admins SET password_hash = ? WHERE id = ?", (new_hashed, admin_id))
        return True, "Password updated successfully"

def update_admin_profile(admin_id, name, email):
    """Updates admin profile details (name and email)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE admins SET name = ?, email = ? WHERE id = ?", (name, email, admin_id))
            return True, "Profile updated successfully"
        except sqlite3.IntegrityError:
            return False, "Email address is already in use"
        except Exception as e:
            return False, f"An error occurred: {str(e)}"
