import json
import cv2
import base64
import numpy as np
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from models.db import get_db_connection
from models.student import get_student_by_student_id, get_all_students
from services.face_service import FaceService, FACE_REC_AVAILABLE
from utils.decorators import login_required
from utils.logger import log_event

api_bp = Blueprint('api', __name__)
face_service = FaceService()

@api_bp.route('/api/register_face_frame/<student_id>', methods=['POST'])
@login_required
def register_face_frame(student_id):
    """
    Receives a single snapshot frame from the WebRTC canvas during student registration.
    Extracts face location, calculates 128D encoding, and stores it in the database.
    """
    student = get_student_by_student_id(student_id)
    if not student:
        return jsonify({'status': 'error', 'message': 'Student not found.'}), 404
        
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'status': 'error', 'message': 'No image data received.'}), 400
        
    # Decode image from base64
    rgb_image = face_service.decode_image(data['image'])
    if rgb_image is None:
        return jsonify({'status': 'error', 'message': 'Image decoding failed.'}), 400
        
    # Detect faces
    face_locations = face_service.detect_faces(rgb_image)
    if not face_locations:
        return jsonify({'status': 'error', 'message': 'No face detected. Keep face in frame.'}), 200
        
    if len(face_locations) > 1:
        return jsonify({'status': 'error', 'message': 'Multiple faces detected. Register one person at a time.'}), 200
        
    # Compute encoding
    encodings = face_service.get_face_encodings(rgb_image, face_locations)
    if not encodings or len(encodings) == 0:
        return jsonify({'status': 'error', 'message': 'Failed to process face biometric encoding.'}), 200
        
    # Serialize encoding to JSON
    encoding_json = json.dumps(encodings[0].tolist())
    
    # Store encoding in database
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO face_encodings (student_id, encoding_json)
                VALUES (?, ?)
            ''', (student_id, encoding_json))
            
        return jsonify({'status': 'success', 'message': 'Biometric frame enrolled successfully.'}), 200
    except Exception as e:
        log_event("ERROR", "Biometrics", f"Failed to store face encoding: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Database insertion failed.'}), 500

@api_bp.route('/api/recognize_attendance', methods=['POST'])
def recognize_attendance():
    """
    Receives video frames from the attendance scanner page.
    Performs face detection, matching, liveness/feature analysis, and registers attendance.
    """
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'status': 'error', 'message': 'No image data received.'}), 400
        
    # Decode image from base64
    rgb_image = face_service.decode_image(data['image'])
    if rgb_image is None:
        return jsonify({'status': 'error', 'message': 'Image decoding failed.'}), 400
        
    # Detect faces
    face_locations = face_service.detect_faces(rgb_image)
    if not face_locations:
        return jsonify({'status': 'no_face'}), 200

    # Fetch matching threshold and configurations
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='tolerance'")
        tolerance = float(cursor.fetchone()['value'])
        cursor.execute("SELECT value FROM settings WHERE key='confidence_threshold'")
        confidence_threshold = float(cursor.fetchone()['value'])
        
        # Load all known encodings
        cursor.execute("SELECT student_id, encoding_json FROM face_encodings")
        db_records = cursor.fetchall()

    # Match against registered student encodings
    known_encodings = []
    known_ids = []
    for r in db_records:
        known_encodings.append(json.loads(r['encoding_json']))
        known_ids.append(r['student_id'])
        
    probe_encodings = face_service.get_face_encodings(rgb_image, face_locations)
    
    results = []
    for idx, probe in enumerate(probe_encodings):
        loc = face_locations[idx]
        analysis = face_service.analyze_face_features(rgb_image, loc)
        
        match_found = False
        matched_id = None
        best_dist = 1.0
        
        if known_encodings:
            matches = face_service.compare_faces(known_encodings, probe, tolerance=tolerance)
            for m_idx, is_match in enumerate(matches):
                if is_match:
                    dist = face_service.calculate_distance(known_encodings[m_idx], probe)
                    if dist < best_dist:
                        best_dist = dist
                        matched_id = known_ids[m_idx]
                        match_found = True
        
        # Confidence score calculation
        if match_found:
            if not FACE_REC_AVAILABLE:
                # In cascade/simulated mode, scale confidence based on max allowed distance (tolerance * 1.5)
                # to guarantee it satisfies the confidence threshold if matches return true.
                max_allowed_dist = tolerance * 1.5
                if max_allowed_dist > 0:
                    confidence = 100.0 - (100.0 - confidence_threshold) * (best_dist / max_allowed_dist)
                    confidence = round(max(confidence_threshold, min(100.0, confidence)), 1)
                else:
                    confidence = 100.0
            else:
                confidence = round((1.0 - best_dist) * 100, 1)
        else:
            confidence = 0.0
            
        if match_found and confidence >= confidence_threshold:
            # Extract subject if provided by scanner client
            requested_subject = data.get('subject')
            # Mark attendance and get student details
            attendance_status, student_info = process_attendance_mark(matched_id, confidence, analysis, subject=requested_subject)
            results.append({
                'status': 'matched',
                'box': {'top': loc[0], 'right': loc[1], 'bottom': loc[2], 'left': loc[3]},
                'student': student_info,
                'attendance': attendance_status,
                'features': analysis,
                'confidence': confidence
            })
        else:
            results.append({
                'status': 'unknown',
                'box': {'top': loc[0], 'right': loc[1], 'bottom': loc[2], 'left': loc[3]},
                'features': analysis
            })
            
    mode_str = 'dlib' if FACE_REC_AVAILABLE else 'cascade'
    return jsonify({'status': 'processed', 'faces': results, 'mode': mode_str}), 200

@api_bp.route('/api/clear_encodings/<student_id>', methods=['POST'])
@login_required
def clear_encodings(student_id):
    """Deletes all enrolled biometric face encodings for a student."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM face_encodings WHERE student_id = ?", (student_id,))
        log_event("INFO", "Biometrics", f"Cleared biometrics for student ID: {student_id}")
        return jsonify({'status': 'success', 'message': 'Biometric data cleared successfully.'}), 200
    except Exception as e:
        log_event("ERROR", "Biometrics", f"Failed to clear biometrics: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/api/recognize_image_upload', methods=['POST'])
def recognize_image_upload():
    """
    Processes an uploaded image file or base64 photo for multi-face recognition.
    Detects faces, compares with database encodings, draws annotations on the image,
    logs attendance / recognition event, and returns JSON response with annotated image.
    """
    subject = request.form.get('subject') or 'Auto'
    rgb_image = None
    
    # Check if uploaded via FormData file or JSON payload
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            file_bytes = np.frombuffer(file.read(), np.uint8)
            bgr_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if bgr_img is not None:
                rgb_image = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
            else:
                return jsonify({'status': 'error', 'message': 'Invalid image file.'}), 400
        else:
            return jsonify({'status': 'error', 'message': 'No file selected.'}), 400
    else:
        data = request.get_json(silent=True)
        if data and 'image' in data:
            rgb_image = face_service.decode_image(data['image'])
            subject = data.get('subject', 'Auto')
        else:
            return jsonify({'status': 'error', 'message': 'No image data provided.'}), 400
            
    if rgb_image is None:
        return jsonify({'status': 'error', 'message': 'Failed to process image.'}), 400
        
    # Detect faces
    face_locations = face_service.detect_faces(rgb_image)
    if not face_locations:
        return jsonify({'status': 'no_face', 'message': 'No faces detected in the uploaded photo.'}), 200

    # Fetch tolerance & confidence thresholds
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='tolerance'")
        tolerance = float(cursor.fetchone()['value'])
        cursor.execute("SELECT value FROM settings WHERE key='confidence_threshold'")
        confidence_threshold = float(cursor.fetchone()['value'])
        
        cursor.execute("SELECT student_id, encoding_json FROM face_encodings")
        db_records = cursor.fetchall()

    known_encodings = []
    known_ids = []
    for r in db_records:
        known_encodings.append(json.loads(r['encoding_json']))
        known_ids.append(r['student_id'])
        
    probe_encodings = face_service.get_face_encodings(rgb_image, face_locations)
    
    # Clone image for drawing annotations (convert RGB back to BGR for OpenCV drawing)
    annotated_bgr = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
    matches_list = []
    
    for idx, probe in enumerate(probe_encodings):
        loc = face_locations[idx]
        analysis = face_service.analyze_face_features(rgb_image, loc)
        
        top, right, bottom, left = loc
        match_found = False
        matched_id = None
        best_dist = 1.0
        
        if known_encodings:
            matches = face_service.compare_faces(known_encodings, probe, tolerance=tolerance)
            for m_idx, is_match in enumerate(matches):
                if is_match:
                    dist = face_service.calculate_distance(known_encodings[m_idx], probe)
                    if dist < best_dist:
                        best_dist = dist
                        matched_id = known_ids[m_idx]
                        match_found = True
                        
        if match_found:
            if not FACE_REC_AVAILABLE:
                max_allowed_dist = tolerance * 1.5
                if max_allowed_dist > 0:
                    confidence = 100.0 - (100.0 - confidence_threshold) * (best_dist / max_allowed_dist)
                    confidence = round(max(confidence_threshold, min(100.0, confidence)), 1)
                else:
                    confidence = 100.0
            else:
                confidence = round((1.0 - best_dist) * 100, 1)
        else:
            confidence = 0.0
            
        if match_found and confidence >= confidence_threshold:
            attendance_status, student_info = process_attendance_mark(matched_id, confidence, analysis, subject=subject)
            student_info['confidence'] = confidence
            student_info['features'] = analysis
            student_info['attendance'] = attendance_status
            matches_list.append(student_info)
            
            # Draw emerald green bounding box and label
            cv2.rectangle(annotated_bgr, (left, top), (right, bottom), (16, 185, 129), 3)
            label = f"{student_info['name']} ({confidence}%)"
            cv2.rectangle(annotated_bgr, (left, top - 30), (right, top), (16, 185, 129), -1)
            cv2.putText(annotated_bgr, label, (left + 5, top - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        else:
            # Draw red bounding box for unrecognized face
            cv2.rectangle(annotated_bgr, (left, top), (right, bottom), (239, 68, 68), 2)
            cv2.rectangle(annotated_bgr, (left, top - 25), (right, top), (239, 68, 68), -1)
            cv2.putText(annotated_bgr, "Unknown Person", (left + 5, top - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Encode annotated image to Base64 JPEG data URL
    _, buffer = cv2.imencode('.jpg', annotated_bgr)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    annotated_data_url = f"data:image/jpeg;base64,{b64_str}"
    
    return jsonify({
        'status': 'success',
        'faces_detected': len(face_locations),
        'faces_matched': len(matches_list),
        'annotated_image': annotated_data_url,
        'matches': matches_list
    }), 200

def get_current_scheduled_lecture(now_dt=None):
    """
    Returns the scheduled lecture based on current time:
    - 09:30 - 10:30: Python
    - 10:30 - 11:30: Software Engineering
    - 11:30 - 12:30: Java
    """
    if now_dt is None:
        now_dt = datetime.now()
    t = now_dt.time()
    t_9_30 = datetime.strptime('09:30:00', '%H:%M:%S').time()
    t_10_30 = datetime.strptime('10:30:00', '%H:%M:%S').time()
    t_11_30 = datetime.strptime('11:30:00', '%H:%M:%S').time()
    t_12_30 = datetime.strptime('12:30:00', '%H:%M:%S').time()

    if t_9_30 <= t < t_10_30:
        return 'Python'
    elif t_10_30 <= t < t_11_30:
        return 'Software Engineering'
    elif t_11_30 <= t < t_12_30:
        return 'Java'
    else:
        return 'Python' # Default fallback

def process_attendance_mark(student_id, confidence, analysis, subject=None):
    """
    Saves an attendance log entry for a specific lecture subject.
    Checks limits and prevents duplicate check-ins for the same subject today.
    Returns (status_type, student_details).
    """
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')

    # Resolve active subject
    if not subject or subject == 'Auto':
        subject = get_current_scheduled_lecture(now)
        
    student = get_student_by_student_id(student_id)
    if not student:
        return 'error', None
        
    student_info = {
        'student_id': student['student_id'],
        'name': student['name'],
        'roll_number': student['roll_number'],
        'department': student['department'],
        'semester': student['semester'],
        'email': student.get('email', 'N/A'),
        'phone': student.get('phone', 'N/A'),
        'photo_path': student['photo_path'],
        'subject': subject
    }

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check for duplicate check-in today for this specific lecture subject
            cursor.execute(
                "SELECT id, time FROM attendance WHERE student_id = ? AND date = ? AND subject = ?", 
                (student_id, date_str, subject)
            )
            existing = cursor.fetchone()
            if existing:
                return f"Already marked for {subject} today at {existing['time']}", student_info

            # Lecture start times
            lecture_starts = {
                'Python': '09:30',
                'Software Engineering': '10:30',
                'Java': '11:30'
            }
            start_limit = lecture_starts.get(subject, '09:30')
            
            # Determine status based on checkin time (15 mins grace period)
            status = 'Present'
            try:
                limit_hr, limit_min = map(int, start_limit.split(':'))
                limit_min += 15
                if limit_min >= 60:
                    limit_hr += 1
                    limit_min -= 60
                    
                checkin_time = datetime.strptime(time_str, '%H:%M:%S')
                boundary_time = datetime.strptime(f"{limit_hr:02d}:{limit_min:02d}:00", '%H:%M:%S')
                if checkin_time > boundary_time:
                    status = 'Late'
            except Exception:
                pass
                
            cursor.execute('''
                INSERT INTO attendance (
                    student_id, date, time, subject, status, method, confidence, 
                    emotion, smile_detected, blink_detected, mask_detected
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                student_id, date_str, time_str, subject, status, 'Face', confidence,
                analysis.get('emotion', 'neutral'),
                1 if analysis.get('smile_detected') else 0,
                1 if analysis.get('blink_detected') else 0,
                1 if analysis.get('mask_detected') else 0
            ))
            
        log_event("INFO", "Attendance", f"Marked {status} for {student['name']} ({student_id}) in lecture '{subject}'.")
        return f"{status} marked for {subject}", student_info
        
    except Exception as e:
        log_event("ERROR", "Attendance", f"Failed to mark attendance for {student_id} in {subject}: {str(e)}")
        return "Database logging failed", student_info
