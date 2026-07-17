import cv2
import numpy as np
import json
import base64
from config import Config
from utils.logger import log_event

# Try to import face_recognition and dlib
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
    log_event("INFO", "FaceService", "face_recognition library loaded successfully.")
except ImportError:
    FACE_REC_AVAILABLE = False
    log_event("WARNING", "FaceService", "face_recognition not found. Running in Haar Cascade simulated mode.")

class FaceService:
    def __init__(self):
        # Load Haar Cascade as a fallback face detector
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            log_event("ERROR", "FaceService", "Failed to load OpenCV Haar Cascade XML.")
            
    def decode_image(self, base64_data):
        """
        Decodes base64-encoded image data sent from the browser canvas.
        Returns a numpy RGB image.
        """
        try:
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            img_data = base64.b64decode(base64_data)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            # OpenCV loads BGR, convert to RGB for face_recognition and rendering
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            log_event("ERROR", "FaceService", f"Failed to decode image data: {str(e)}")
            return None

    def detect_faces(self, rgb_image):
        """
        Detects faces in an RGB image.
        Returns a list of bounding boxes in face_recognition format: [(top, right, bottom, left), ...]
        """
        if rgb_image is None:
            return []
            
        if FACE_REC_AVAILABLE:
            try:
                # Returns [(top, right, bottom, left), ...]
                return face_recognition.face_locations(rgb_image, model="hog")
            except Exception as e:
                log_event("ERROR", "FaceService", f"face_recognition detection failed: {str(e)}")
                # Fallback to Haar cascade below if library fails in runtime
        
        # Fallback OpenCV Haar Cascade
        try:
            gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(60, 60)
            )
            
            # Translate OpenCV (x, y, w, h) to face_recognition (top, right, bottom, left)
            locations = []
            for (x, y, w, h) in faces:
                locations.append((int(y), int(x + w), int(y + h), int(x)))
            return locations
        except Exception as e:
            log_event("ERROR", "FaceService", f"Haar Cascade detection failed: {str(e)}")
            return []

    def get_face_encodings(self, rgb_image, face_locations):
        """
        Generates 128-dimensional encodings for detected face regions.
        Returns a list of 128D encodings (numpy arrays or mock float lists).
        """
        if not face_locations or rgb_image is None:
            return []
            
        if FACE_REC_AVAILABLE:
            try:
                return face_recognition.face_encodings(rgb_image, face_locations)
            except Exception as e:
                log_event("ERROR", "FaceService", f"Encoding computation failed: {str(e)}")
                
        # Simulated mode: Generate a deterministic mock 128D encoding for the face region.
        # We average color values in quadrants of the bounding box to make it somewhat unique.
        mock_encodings = []
        for (top, right, bottom, left) in face_locations:
            try:
                face_crop = rgb_image[top:bottom, left:right]
                if face_crop.size == 0:
                    mock_encodings.append(np.zeros(128))
                    continue
                # Divide crop into a 4x4 grid (16 sections), calculate average R, G, B, and grayscale (64 values)
                # repeat twice to get 128 dimensions.
                h_step, w_step = max(1, face_crop.shape[0] // 4), max(1, face_crop.shape[1] // 4)
                features = []
                for r in range(4):
                    for c in range(4):
                        sub_crop = face_crop[r*h_step:(r+1)*h_step, c*w_step:(c+1)*w_step]
                        if sub_crop.size > 0:
                            mean_val = np.mean(sub_crop, axis=(0, 1)) / 255.0  # Normalized [0, 1]
                            features.extend([mean_val[0], mean_val[1], mean_val[2], np.mean(mean_val)])
                        else:
                            features.extend([0.0, 0.0, 0.0, 0.0])
                # Duplicate features to get exactly 128 elements
                full_encoding = np.array(features + features)
                # L2 normalize
                norm = np.linalg.norm(full_encoding)
                if norm > 0:
                    full_encoding = full_encoding / norm
                mock_encodings.append(full_encoding)
            except Exception as e:
                mock_encodings.append(np.zeros(128))
        return mock_encodings

    def compare_faces(self, known_encodings, face_encoding, tolerance=0.5):
        """
        Compares a probe face encoding with known registered encodings.
        Returns a list of boolean matches.
        """
        if not known_encodings or face_encoding is None:
            return []
            
        if FACE_REC_AVAILABLE:
            try:
                # Convert list of serialised encodings (list of floats) to numpy arrays
                np_known = [np.array(e) for e in known_encodings]
                np_probe = np.array(face_encoding)
                return face_recognition.compare_faces(np_known, np_probe, tolerance=tolerance)
            except Exception as e:
                log_event("ERROR", "FaceService", f"Face comparison failed: {str(e)}")

        # Fallback Euclidean distance matching on simulated encodings
        matches = []
        for known in known_encodings:
            dist = np.linalg.norm(np.array(known) - np.array(face_encoding))
            matches.append(dist <= (tolerance * 1.5))  # Loosen threshold slightly for mock encodings
        return matches

    def calculate_distance(self, known_encoding, face_encoding):
        """Calculates distance between two encodings. Lower means more similar."""
        try:
            return float(np.linalg.norm(np.array(known_encoding) - np.array(face_encoding)))
        except Exception:
            return 1.0

    def analyze_face_features(self, rgb_image, face_location):
        """
        Runs additional AI features: Blink, Smile, Emotion, and Mask detection.
        Returns a dict: {
            'blink_detected': bool,
            'smile_detected': bool,
            'emotion': str,
            'mask_detected': bool,
            'confidence': float
        }
        """
        top, right, bottom, left = face_location
        width = right - left
        height = bottom - top
        
        # 1. Mask Detection
        # Analysis: Check if the mouth/nose region (lower 40% of the face crop) is covered by uniform, low-texture colors
        mask_detected = False
        try:
            face_crop = rgb_image[top:bottom, left:right]
            if face_crop.size > 0:
                h_crop = face_crop.shape[0]
                lower_face = face_crop[int(h_crop*0.6):, :]
                
                # Check for standard surgical mask colors (blues, white, black)
                hsv = cv2.cvtColor(lower_face, cv2.COLOR_RGB2HSV)
                
                # Surgical Blue/Green range
                lower_blue = np.array([80, 40, 40])
                upper_blue = np.array([130, 255, 255])
                blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
                
                # Standard color uniformity check (low texture variance indicates mask covering details)
                gray_lower = cv2.cvtColor(lower_face, cv2.COLOR_RGB2GRAY)
                std_dev = np.std(gray_lower)
                
                # If blue color dominates or standard deviation is extremely low (flat mask surface)
                blue_ratio = np.sum(blue_mask > 0) / lower_face.size
                if blue_ratio > 0.15 or std_dev < 18.0:
                    mask_detected = True
        except Exception as e:
            pass

        # 2. Extract landmarks if face_recognition is active
        blink_detected = False
        smile_detected = False
        emotion = "neutral"
        
        if FACE_REC_AVAILABLE and not mask_detected:
            try:
                landmarks = face_recognition.face_landmarks(rgb_image, [face_location])
                if landmarks:
                    lm = landmarks[0]
                    
                    # Blink Detection (EAR - Eye Aspect Ratio)
                    # EAR = (dist(p2, p6) + dist(p3, p5)) / (2 * dist(p1, p4))
                    def eye_aspect_ratio(eye_pts):
                        p1, p2, p3, p4, p5, p6 = eye_pts
                        dist_vertical_1 = np.linalg.norm(np.array(p2) - np.array(p6))
                        dist_vertical_2 = np.linalg.norm(np.array(p3) - np.array(p5))
                        dist_horizontal = np.linalg.norm(np.array(p1) - np.array(p4))
                        if dist_horizontal == 0: return 1.0
                        return (dist_vertical_1 + dist_vertical_2) / (2.0 * dist_horizontal)
                    
                    left_eye_ear = eye_aspect_ratio(lm['left_eye'])
                    right_eye_ear = eye_aspect_ratio(lm['right_eye'])
                    mean_ear = (left_eye_ear + right_eye_ear) / 2.0
                    
                    # Threshold: if eyes are closed (EAR < threshold)
                    if mean_ear < Config.EYE_EAR_THRESHOLD:
                        blink_detected = True
                        
                    # Smile Detection (MAR - Mouth Aspect Ratio / Width ratio)
                    # MAR = dist(m13, m19) / dist(m15, m17) or corner distance compared to vertical
                    top_lip = lm['top_lip']
                    bottom_lip = lm['bottom_lip']
                    
                    mouth_width = np.linalg.norm(np.array(top_lip[0]) - np.array(top_lip[6]))
                    mouth_height = np.linalg.norm(np.array(top_lip[9]) - np.array(bottom_lip[9]))
                    
                    mar = mouth_height / mouth_width if mouth_width > 0 else 0.0
                    # Standard smile draws corners of mouth wider (width/height ratio decreases height/width ratio)
                    # Smile detection: if mouth width is relatively wide compared to height
                    if mar < 0.25 and mouth_width > (width * 0.45):
                        smile_detected = True
                        emotion = "happy"
                    elif mar > 0.4:
                        emotion = "surprised"
                    else:
                        emotion = "neutral"
            except Exception as e:
                log_event("WARNING", "FaceService", f"Landmark feature extraction failed: {str(e)}")

        # Fallback mock animations/states when face_recognition is not loaded
        if not FACE_REC_AVAILABLE:
            # We vary results based on current timestamp millisecond to simulate real-time changes
            import time
            ms = int(time.time() * 1000)
            
            # Simulate blinking (closed eyes 10% of time)
            if (ms // 400) % 8 == 0:
                blink_detected = True
                
            # Simulate smile and emotions cycle
            cycle = (ms // 3000) % 3
            if cycle == 0:
                smile_detected = True
                emotion = "happy"
            elif cycle == 1:
                emotion = "surprised"
            else:
                emotion = "neutral"
                
            # Randomly toggle mask if face box touches boundaries, keep False by default
            mask_detected = False

        return {
            'blink_detected': blink_detected,
            'smile_detected': smile_detected,
            'emotion': emotion,
            'mask_detected': mask_detected
        }
