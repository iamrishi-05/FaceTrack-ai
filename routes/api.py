import os
import time
import json
import base64
from flask import Blueprint, request, jsonify, session
from config import Config
from models.target import (
    add_target, get_all_target_encodings, log_detection, 
    clear_detection_logs, get_tracker_stats, get_all_targets,
    is_target_logged_recently
)
from models.db import get_db_connection
from services.face_service import face_service
from utils.logger import log_event

api_bp = Blueprint('api', __name__)

# In-memory cooldown tracker to prevent flooding DB with duplicate detection logs
# Maps (user_id, target_id) -> last_logged_timestamp
DETECTION_COOLDOWN = {}

@api_bp.route('/api/recognize_frame', methods=['POST'])
def recognize_frame():
    """
    Processes real-time camera frames sent from the browser canvas.
    Detects faces, compares against registered Target encodings of the logged-in user.
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401

        data = request.get_json() or {}
        image_data = data.get('image')
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'}), 400

        # Decode RGB frame
        rgb_frame = face_service.decode_image(image_data)
        if rgb_frame is None:
            return jsonify({'success': False, 'message': 'Failed to decode image frame'}), 400

        # Fetch active target tolerance setting for this user
        tolerance = Config.DEFAULT_TOLERANCE
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE user_id = ? AND key = 'tolerance'", (user_id,))
            row = cursor.fetchone()
            if row:
                try:
                    tolerance = float(row['value'])
                except ValueError:
                    pass

        # Detect faces in frame
        face_locations = face_service.detect_faces(rgb_frame)
        if not face_locations:
            return jsonify({
                'success': True,
                'faces_count': 0,
                'results': []
            })

        # Compute encodings for detected faces
        probe_encodings = face_service.get_face_encodings(rgb_frame, face_locations)
        
        # Load registered target profiles and encodings strictly owned by user_id
        target_map = get_all_target_encodings(user_id)

        results = []
        current_time = time.time()

        for idx, (location, probe_enc) in enumerate(zip(face_locations, probe_encodings)):
            top, right, bottom, left = location
            
            best_match_target = None
            best_distance = 1.0
            best_confidence = 0.0

            # Compare probe encoding against all target encodings of this user
            for tgt_id, tgt_info in target_map.items():
                for known_enc in tgt_info['encodings']:
                    dist = face_service.calculate_distance(known_enc, probe_enc)
                    if dist < best_distance:
                        best_distance = dist
                        best_match_target = tgt_info

            # Liveness features & Emotion analysis
            liveness = face_service.analyze_face_features(rgb_frame, location)

            if best_match_target and best_distance <= tolerance:
                confidence = face_service.calculate_confidence(best_distance, tolerance=tolerance)
                target_id = best_match_target['target_id']
                target_name = best_match_target['name']

                # Enforce 1-minute (60 seconds) cooldown per target person per user
                cooldown_key = (user_id, target_id)
                last_logged = DETECTION_COOLDOWN.get(cooldown_key, 0)
                cooldown_sec = 60.0

                if (current_time - last_logged >= cooldown_sec) and not is_target_logged_recently(user_id, target_id, seconds=60):
                    DETECTION_COOLDOWN[cooldown_key] = current_time
                    # Log detection event to database (at most once per minute)
                    log_detection(
                        user_id=user_id,
                        target_id=target_id,
                        target_name=target_name,
                        confidence=confidence,
                        emotion=liveness['emotion'],
                        smile=liveness['smile_detected'],
                        blink=liveness['blink_detected'],
                        mask=liveness['mask_detected']
                    )

                results.append({
                    'matched': True,
                    'target_id': target_id,
                    'name': target_name,
                    'confidence': confidence,
                    'distance': round(best_distance, 3),
                    'photo_path': best_match_target.get('photo_path'),
                    'location': {'top': top, 'right': right, 'bottom': bottom, 'left': left},
                    'liveness': liveness
                })
            else:
                results.append({
                    'matched': False,
                    'name': 'Unknown / Unregistered',
                    'confidence': 0.0,
                    'distance': round(best_distance, 3),
                    'location': {'top': top, 'right': right, 'bottom': bottom, 'left': left},
                    'liveness': liveness
                })

        return jsonify({
            'success': True,
            'faces_count': len(results),
            'results': results
        })

    except Exception as e:
        log_event("ERROR", "API", f"Error in recognize_frame endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/api/upload_target', methods=['POST'])
def upload_target():
    """
    API endpoint to add a new target person by uploading a photo file or sending a webcam snapshot base64 image.
    Saves target under the logged-in user's account.
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401

        name = request.form.get('name') or (request.json.get('name') if request.is_json else None)
        notes = request.form.get('notes') or (request.json.get('notes') if request.is_json else "")
        target_id_custom = request.form.get('target_id') or (request.json.get('target_id') if request.is_json else None)
        
        if not name or not name.strip():
            return jsonify({'success': False, 'message': 'Target Name is required.'}), 400

        name = name.strip()
        photo_saved_path = None
        encodings = []

        # Ensure target upload directory exists
        target_upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'targets')
        os.makedirs(target_upload_dir, exist_ok=True)

        # Check if file uploaded via multipart form
        if 'photo_file' in request.files and request.files['photo_file'].filename != '':
            file = request.files['photo_file']
            filename = f"user_{user_id}_target_{int(time.time())}_{file.filename}"
            filepath = os.path.join(target_upload_dir, filename)
            file.save(filepath)
            photo_saved_path = f"/uploads/targets/{filename}"
            
            # Extract encodings from uploaded file
            encodings = face_service.extract_encodings_from_file(filepath)

        # Check if base64 snapshot provided
        elif (request.form.get('photo_base64') or (request.is_json and request.json.get('photo_base64'))):
            base64_str = request.form.get('photo_base64') or request.json.get('photo_base64')
            filename = f"user_{user_id}_target_{int(time.time())}.jpg"
            filepath = os.path.join(target_upload_dir, filename)
            
            # Save base64 to image file
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(base64_str))
                
            photo_saved_path = f"/uploads/targets/{filename}"
            encodings = face_service.extract_encodings_from_file(filepath)

        else:
            return jsonify({'success': False, 'message': 'Target photo is required (Upload file or capture webcam picture).'}), 400

        # Ensure at least 1 face encoding was successfully extracted
        if not encodings:
            return jsonify({
                'success': False, 
                'message': 'No face detected in the provided picture. Please upload a clear photo with a visible face.'
            }), 400

        # Save target profile and encodings in database under logged in user_id
        assigned_id = add_target(
            user_id=user_id,
            name=name,
            notes=notes,
            photo_path=photo_saved_path,
            encodings_list=encodings,
            target_id=target_id_custom
        )

        return jsonify({
            'success': True,
            'message': f'Target "{name}" registered successfully under your account!',
            'target_id': assigned_id,
            'photo_path': photo_saved_path
        })

    except Exception as e:
        log_event("ERROR", "API", f"Failed to upload target: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    """Clears detection history logs for logged-in user."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
            
        clear_detection_logs(user_id)
        return jsonify({'success': True, 'message': 'Detection history cleared successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/api/stats', methods=['GET'])
def get_stats():
    """Returns real-time system stats for logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    return jsonify({'success': True, 'stats': get_tracker_stats(user_id)})
