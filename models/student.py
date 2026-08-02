import sqlite3
import re
import os
import shutil
from datetime import datetime
from config import Config
from models.db import get_db_connection
from utils.logger import log_event

def get_all_students(search_query=None, department=None, semester=None):
    """
    Retrieves all students, applying optional filters for search query (name/id/roll),
    department, and semester.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM students WHERE 1=1"
        params = []
        
        if search_query:
            query += " AND (name LIKE ? OR student_id LIKE ? OR roll_number LIKE ?)"
            like_param = f"%{search_query}%"
            params.extend([like_param, like_param, like_param])
            
        if department:
            query += " AND department = ?"
            params.append(department)
            
        if semester:
            query += " AND semester = ?"
            params.append(semester)
            
        query += " ORDER BY name ASC"
        cursor.execute(query, params)
        return cursor.fetchall()

def get_student_by_id(db_id):
    """Retrieves a student by their database primary key (id)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (db_id,))
        return cursor.fetchone()

def get_student_by_student_id(student_id):
    """Retrieves a student by their unique student_id (e.g. FT-2026-0001)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        return cursor.fetchone()

def add_student(student_id, name, roll_number, email, phone, department, semester, photo_path=None):
    """
    Inserts a new student into the database.
    Validates fields and unique constraints.
    Returns (success, message_or_student_id).
    """
    # Validation checks
    if not student_id or not name or not roll_number or not email or not department or not semester:
        return False, "Missing mandatory student fields."
        
    if not re.match(r"^FT-\d{4}-\d{4}$", student_id):
        # Auto format if it doesn't match standard
        # We enforce FT-YYYY-XXXX
        pass

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check unique email/id
            cursor.execute("SELECT id FROM students WHERE student_id = ? OR email = ?", (student_id, email))
            if cursor.fetchone():
                return False, "Student ID or Email is already registered."
                
            cursor.execute('''
                INSERT INTO students (student_id, name, roll_number, email, phone, department, semester, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, name, roll_number, email, phone, department, semester, photo_path))
            
            log_event("INFO", "StudentManagement", f"Registered new student: {name} ({student_id})")
            return True, student_id
    except Exception as e:
        log_event("ERROR", "StudentManagement", f"Failed to register student: {str(e)}")
        return False, f"Database error: {str(e)}"

def update_student(db_id, name, roll_number, email, phone, department, semester, photo_path=None):
    """
    Updates student details by database ID.
    Returns (success, message).
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if email is used by another student
            cursor.execute("SELECT id FROM students WHERE email = ? AND id != ?", (email, db_id))
            if cursor.fetchone():
                return False, "Email address is already in use by another student."
                
            # Perform update
            if photo_path:
                cursor.execute('''
                    UPDATE students 
                    SET name = ?, roll_number = ?, email = ?, phone = ?, department = ?, semester = ?, photo_path = ?
                    WHERE id = ?
                ''', (name, roll_number, email, phone, department, semester, photo_path, db_id))
            else:
                cursor.execute('''
                    UPDATE students 
                    SET name = ?, roll_number = ?, email = ?, phone = ?, department = ?, semester = ?
                    WHERE id = ?
                ''', (name, roll_number, email, phone, department, semester, db_id))
                
            cursor.execute("SELECT student_id FROM students WHERE id = ?", (db_id,))
            student_id = cursor.fetchone()['student_id']
            log_event("INFO", "StudentManagement", f"Updated details for student ID: {student_id}")
            return True, "Student updated successfully."
    except Exception as e:
        log_event("ERROR", "StudentManagement", f"Failed to update student ID {db_id}: {str(e)}")
        return False, f"Database error: {str(e)}"

def delete_student(student_id):
    """
    Deletes a student using their unique student_id.
    Note: ON DELETE CASCADE will automatically delete encodings and attendance records.
    Returns (success, message).
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if student exists
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
            student = cursor.fetchone()
            if not student:
                return False, "Student not found."
                
            cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            log_event("INFO", "StudentManagement", f"Deleted student: {student['name']} ({student_id}) and cascading records.")
            return True, "Student deleted successfully."
    except Exception as e:
        log_event("ERROR", "StudentManagement", f"Failed to delete student {student_id}: {str(e)}")
        return False, f"Database error: {str(e)}"

def bulk_insert_students(students_list):
    """
    Inserts multiple students into the database inside a single transaction.
    Expects students_list to be a list of tuples:
    (student_id, name, roll_number, email, phone, department, semester)
    Returns (inserted_count, error_messages).
    """
    inserted = 0
    errors = []
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for idx, s in enumerate(students_list):
            try:
                # Expect s structure: (student_id, name, roll_number, email, phone, department, semester)
                student_id, name, roll_number, email, phone, dept, sem = s
                
                # Basic check
                cursor.execute("SELECT id FROM students WHERE student_id = ? OR email = ?", (student_id, email))
                if cursor.fetchone():
                    errors.append(f"Row {idx+2}: Student ID '{student_id}' or Email '{email}' already registered.")
                    continue
                    
                cursor.execute('''
                    INSERT INTO students (student_id, name, roll_number, email, phone, department, semester)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (student_id, name, roll_number, email, phone, dept, sem))
                inserted += 1
            except Exception as e:
                errors.append(f"Row {idx+2}: Error inserting row - {str(e)}")
                
        if inserted > 0:
            log_event("INFO", "StudentManagement", f"Bulk imported {inserted} students.")
            
    return inserted, errors

def delete_all_students():
    """
    Deletes all students and associated records (face encodings, attendance) from the database,
    and cleans up upload and dataset folders.
    Returns (success, message).
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance")
            cursor.execute("DELETE FROM face_encodings")
            cursor.execute("DELETE FROM students")
            
        # Clean up files in uploads and dataset folders
        for folder in [Config.UPLOAD_FOLDER, Config.DATASET_FOLDER]:
            if os.path.exists(folder):
                for item in os.listdir(folder):
                    item_path = os.path.join(folder, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        
        log_event("WARNING", "StudentManagement", "All student data, encodings, and attendance logs deleted.")
        return True, "All student data cleared successfully."
    except Exception as e:
        log_event("ERROR", "StudentManagement", f"Failed to delete all student data: {str(e)}")
        return False, f"Error clearing student data: {str(e)}"

def verify_student(username, password):
    """
    Verifies student credentials where:
    - Username (Login ID) is the student's middle name (case-insensitive).
    - Password is the last 4 digits of their student_id.
    Returns the student record if valid, otherwise None.
    """
    if not username or not password:
        return None

    clean_username = username.strip().lower()
    clean_password = password.strip()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE status = 'Active'")
        students = cursor.fetchall()
        
        for student in students:
            full_name = (student['name'] or '').strip()
            parts = full_name.split()
            if not parts:
                continue
                
            # Middle name (2nd word for 2+ word names, otherwise 1st word)
            middle_name = parts[1].lower() if len(parts) >= 2 else parts[0].lower()
            
            st_id = (student['student_id'] or '').strip()
            last_4_digits = st_id[-4:] if len(st_id) >= 4 else st_id
            
            # Match middle name (or fallback if 2-word/1-word name) with clean_username
            if (middle_name == clean_username or (len(parts) == 2 and parts[0].lower() == clean_username)) and last_4_digits == clean_password:
                return student

    return None

