import json
import uuid
import datetime
from models.db import get_db_connection
from utils.logger import log_event

def generate_target_id():
    """Generates a clean target tracking ID, e.g. TGT-8492."""
    short_uuid = str(uuid.uuid4()).split('-')[0].upper()
    return f"TGT-{short_uuid[:6]}"

def add_target(user_id, name, notes="", photo_path=None, encodings_list=None, target_id=None):
    """
    Creates a new Target profile for a specific user and saves associated face encodings.
    """
    if not target_id:
        target_id = generate_target_id()
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO targets (user_id, target_id, name, notes, photo_path, status)
            VALUES (?, ?, ?, ?, ?, 'Active')
        ''', (user_id, target_id, name, notes, photo_path))
        
        if encodings_list:
            for enc in encodings_list:
                enc_json = json.dumps(list(enc) if hasattr(enc, 'tolist') else enc)
                cursor.execute('''
                    INSERT INTO target_encodings (user_id, target_id, encoding_json)
                    VALUES (?, ?, ?)
                ''', (user_id, target_id, enc_json))
                
    log_event("INFO", "TargetModel", f"Target created for user {user_id}: {name} ({target_id})")
    return target_id

def get_all_targets(user_id):
    """Retrieves all target records owned by user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, 
                   (SELECT COUNT(*) FROM target_encodings te WHERE te.target_id = t.target_id AND te.user_id = t.user_id) as encodings_count,
                   (SELECT COUNT(*) FROM detection_logs dl WHERE dl.target_id = t.target_id AND dl.user_id = t.user_id) as total_detections,
                   (SELECT MAX(timestamp) FROM detection_logs dl WHERE dl.target_id = t.target_id AND dl.user_id = t.user_id) as last_detected
            FROM targets t
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_target_by_id(user_id, target_id):
    """Retrieves single target profile owned by user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM targets WHERE user_id = ? AND target_id = ?', (user_id, target_id))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_target(user_id, target_id):
    """Deletes a target and its encodings and detection logs for a specific user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM targets WHERE user_id = ? AND target_id = ?', (user_id, target_id))
        cursor.execute('DELETE FROM target_encodings WHERE user_id = ? AND target_id = ?', (user_id, target_id))
        cursor.execute('DELETE FROM detection_logs WHERE user_id = ? AND target_id = ?', (user_id, target_id))
    log_event("INFO", "TargetModel", f"Target deleted for user {user_id}: {target_id}")

def get_all_target_encodings(user_id):
    """
    Returns a dict mapping target_id to encodings owned by user_id:
    {
        'TGT-1234': {
            'target_id': 'TGT-1234',
            'name': 'John Doe',
            'photo_path': '/uploads/targets/...',
            'encodings': [[...128 float values...], [...]]
        }
    }
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.target_id, t.name, t.photo_path, te.encoding_json
            FROM targets t
            JOIN target_encodings te ON t.target_id = te.target_id AND t.user_id = te.user_id
            WHERE t.user_id = ? AND t.status = 'Active'
        ''', (user_id,))
        rows = cursor.fetchall()
        
        targets_map = {}
        for row in rows:
            tgt_id = row['target_id']
            if tgt_id not in targets_map:
                targets_map[tgt_id] = {
                    'target_id': tgt_id,
                    'name': row['name'],
                    'photo_path': row['photo_path'],
                    'encodings': []
                }
            try:
                enc = json.loads(row['encoding_json'])
                targets_map[tgt_id]['encodings'].append(enc)
            except Exception as e:
                log_event("ERROR", "TargetModel", f"Failed to parse JSON encoding: {e}")
                
        return targets_map

def is_target_logged_recently(user_id, target_id, seconds=60):
    """Checks if target was logged for user_id in detection_logs within the last N seconds (1 minute)."""
    cutoff_time = (datetime.datetime.now() - datetime.timedelta(seconds=seconds)).strftime('%Y-%m-%d %H:%M:%S')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM detection_logs 
            WHERE user_id = ? AND target_id = ? AND timestamp >= ?
            LIMIT 1
        ''', (user_id, target_id, cutoff_time))
        return cursor.fetchone() is not None

def log_detection(user_id, target_id, target_name, confidence, emotion="neutral", smile=False, blink=False, mask=False, snapshot_path=None, location="Primary Camera"):
    """Logs a target detection event in detection_logs table for a user."""
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO detection_logs 
            (user_id, target_id, target_name, date, time, confidence, emotion, smile_detected, blink_detected, mask_detected, snapshot_path, location_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, target_id, target_name, date_str, time_str, round(confidence, 1),
            emotion, 1 if smile else 0, 1 if blink else 0, 1 if mask else 0,
            snapshot_path, location
        ))
    log_event("INFO", "DetectionLog", f"Target detected for user {user_id}: {target_name} ({target_id})")

def get_detection_logs(user_id, limit=100, target_id=None, date=None):
    """Retrieves detection logs owned by user_id with optional filtering."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = 'SELECT * FROM detection_logs WHERE user_id = ?'
        params = [user_id]
        
        if target_id:
            query += ' AND target_id = ?'
            params.append(target_id)
        if date:
            query += ' AND date = ?'
            params.append(date)
            
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def clear_detection_logs(user_id):
    """Clears detection logs for a specific user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM detection_logs WHERE user_id = ?', (user_id,))

def get_tracker_stats(user_id):
    """Returns dashboard statistics for a specific user's face tracking system."""
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM targets WHERE user_id = ? AND status = "Active"', (user_id,))
        total_targets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM detection_logs WHERE user_id = ? AND date = ?', (user_id, today_str))
        today_detections = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT target_id) FROM detection_logs WHERE user_id = ? AND date = ?', (user_id, today_str))
        targets_spotted_today = cursor.fetchone()[0]
        
        cursor.execute('SELECT timestamp, target_name FROM detection_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1', (user_id,))
        last_log = cursor.fetchone()
        last_detection_time = last_log['timestamp'] if last_log else None
        last_target_name = last_log['target_name'] if last_log else None
        
        return {
            'total_targets': total_targets,
            'today_detections': today_detections,
            'targets_spotted_today': targets_spotted_today,
            'last_detection_time': last_detection_time,
            'last_target_name': last_target_name
        }
