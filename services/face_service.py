import cv2
import numpy as np
import json
import base64
import os
from config import Config
from utils.logger import log_event

# Try to import face_recognition and dlib
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
    log_event("INFO", "FaceService", "face_recognition library loaded successfully.")
except ImportError:
    FACE_REC_AVAILABLE = False
    log_event("WARNING", "FaceService", "face_recognition not found. Running in OpenCV mode.")

class FaceService:
    def __init__(self):
        # Load Haar Cascade as fallback face detector
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            log_event("ERROR", "FaceService", "Failed to load OpenCV Haar Cascade XML.")
            
    def decode_image(self, base64_data):
        """
        Decodes base64-encoded image data sent from browser canvas/upload.
        Returns a numpy RGB image.
        """
        try:
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            img_data = base64.b64decode(base64_data)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None
            # OpenCV loads BGR, convert to RGB
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            log_event("ERROR", "FaceService", f"Failed to decode image data: {str(e)}")
            return None

    def read_image_file(self, file_path):
        """Reads an image file from disk and converts to RGB numpy array."""
        try:
            if not os.path.exists(file_path):
                return None
            img = cv2.imread(file_path)
            if img is None:
                return None
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            log_event("ERROR", "FaceService", f"Failed to read image file {file_path}: {e}")
            return None

    def detect_faces(self, rgb_image):
        """
        Detects faces in an RGB image.
        Returns list of bounding boxes in face_recognition format: [(top, right, bottom, left), ...]
        """
        if rgb_image is None:
            return []
            
        if FACE_REC_AVAILABLE:
            try:
                return face_recognition.face_locations(rgb_image, model="hog")
            except Exception as e:
                log_event("ERROR", "FaceService", f"face_recognition detection failed: {str(e)}")
        
        # Fallback OpenCV Haar Cascade
        try:
            gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(50, 50)
            )
            
            locations = []
            for (x, y, w, h) in faces:
                locations.append((int(y), int(x + w), int(y + h), int(x)))
            return locations
        except Exception as e:
            log_event("ERROR", "FaceService", f"Haar Cascade detection failed: {str(e)}")
            return []

    def get_face_encodings(self, rgb_image, face_locations):
        """
        Generates 128-dimensional face encodings for detected face locations.
        """
        if not face_locations or rgb_image is None:
            return []
            
        if FACE_REC_AVAILABLE:
            try:
                return face_recognition.face_encodings(rgb_image, face_locations)
            except Exception as e:
                log_event("ERROR", "FaceService", f"Encoding computation failed: {str(e)}")
                
        # Fallback mode: Generate deterministic 128D encoding for face region
        mock_encodings = []
        for (top, right, bottom, left) in face_locations:
            try:
                face_crop = rgb_image[max(0, top):bottom, max(0, left):right]
                if face_crop.size == 0:
                    mock_encodings.append(np.zeros(128))
                    continue
                h_step, w_step = max(1, face_crop.shape[0] // 4), max(1, face_crop.shape[1] // 4)
                features = []
                for r in range(4):
                    for c in range(4):
                        sub_crop = face_crop[r*h_step:(r+1)*h_step, c*w_step:(c+1)*w_step]
                        if sub_crop.size > 0:
                            mean_val = np.mean(sub_crop, axis=(0, 1)) / 255.0
                            features.extend([mean_val[0], mean_val[1], mean_val[2], np.mean(mean_val)])
                        else:
                            features.extend([0.0, 0.0, 0.0, 0.0])
                full_encoding = np.array(features + features)
                norm = np.linalg.norm(full_encoding)
                if norm > 0:
                    full_encoding = full_encoding / norm
                mock_encodings.append(full_encoding)
            except Exception as e:
                mock_encodings.append(np.zeros(128))
        return mock_encodings

    def extract_encodings_from_file(self, file_path):
        """Extracts encodings directly from an input image file path."""
        rgb_img = self.read_image_file(file_path)
        if rgb_img is None:
            return []
        locations = self.detect_faces(rgb_img)
        if not locations:
            return []
        return self.get_face_encodings(rgb_img, locations)

    def extract_encodings_from_base64(self, base64_str):
        """Extracts encodings directly from a base64 string."""
        rgb_img = self.decode_image(base64_str)
        if rgb_img is None:
            return []
        locations = self.detect_faces(rgb_img)
        if not locations:
            return []
        return self.get_face_encodings(rgb_img, locations)

    def calculate_distance(self, known_encoding, face_encoding):
        """Calculates Euclidean distance between two 128D encodings. Lower = higher match."""
        try:
            return float(np.linalg.norm(np.array(known_encoding) - np.array(face_encoding)))
        except Exception:
            return 1.0

    def calculate_confidence(self, distance, tolerance=0.5):
        """Converts distance into a 0 - 100% confidence percentage."""
        if distance > tolerance:
            conf = max(0.0, 100.0 - (distance / tolerance) * 50.0)
        else:
            conf = 100.0 - (distance / (tolerance * 2.0)) * 50.0
        return min(99.9, max(0.0, conf))

    def analyze_face_features(self, rgb_image, face_location):
        """
        Computes accurate liveness and facial emotion states: Blink, Smile, Emotion, Mask.
        Supports Happy, Surprised, Sad, Focused, and Neutral.
        """
        top, right, bottom, left = face_location
        width = max(1, right - left)
        height = max(1, bottom - top)
        
        # 1. Mask Detection
        mask_detected = False
        try:
            face_crop = rgb_image[max(0, top):bottom, max(0, left):right]
            if face_crop.size > 0:
                h_crop = face_crop.shape[0]
                lower_face = face_crop[int(h_crop*0.6):, :]
                hsv = cv2.cvtColor(lower_face, cv2.COLOR_RGB2HSV)
                
                lower_blue = np.array([80, 40, 40])
                upper_blue = np.array([130, 255, 255])
                blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
                
                gray_lower = cv2.cvtColor(lower_face, cv2.COLOR_RGB2GRAY)
                std_dev = np.std(gray_lower)
                
                blue_ratio = np.sum(blue_mask > 0) / lower_face.size
                if blue_ratio > 0.15 or std_dev < 18.0:
                    mask_detected = True
        except Exception:
            pass

        blink_detected = False
        smile_detected = False
        emotion = "neutral"
        
        if FACE_REC_AVAILABLE and not mask_detected:
            try:
                landmarks = face_recognition.face_landmarks(rgb_image, [face_location])
                if landmarks:
                    lm = landmarks[0]
                    
                    # Blink Detection (Eye Aspect Ratio)
                    def eye_aspect_ratio(eye_pts):
                        p1, p2, p3, p4, p5, p6 = eye_pts
                        dist_v1 = np.linalg.norm(np.array(p2) - np.array(p6))
                        dist_v2 = np.linalg.norm(np.array(p3) - np.array(p5))
                        dist_h = np.linalg.norm(np.array(p1) - np.array(p4))
                        if dist_h == 0: return 0.25
                        return (dist_v1 + dist_v2) / (2.0 * dist_h)
                    
                    left_ear = eye_aspect_ratio(lm['left_eye'])
                    right_ear = eye_aspect_ratio(lm['right_eye'])
                    mean_ear = (left_ear + right_ear) / 2.0
                    
                    if mean_ear < Config.EYE_EAR_THRESHOLD:
                        blink_detected = True
                        
                    # Mouth Landmark Analysis
                    left_corner = np.array(lm['top_lip'][0])
                    right_corner = np.array(lm['top_lip'][6])
                    top_center = np.array(lm['top_lip'][3])
                    bottom_center = np.array(lm['bottom_lip'][3])
                    
                    mouth_w = np.linalg.norm(left_corner - right_corner)
                    mouth_h = np.linalg.norm(top_center - bottom_center)
                    mar = mouth_h / mouth_w if mouth_w > 0 else 0.0
                    
                    # Corner lift: elevation of mouth corners compared to upper lip center
                    avg_corner_y = (left_corner[1] + right_corner[1]) / 2.0
                    lip_center_y = top_center[1]
                    corner_lift = lip_center_y - avg_corner_y
                    
                    # Eyebrow Geometry
                    left_eb_y = np.mean([p[1] for p in lm['left_eyebrow']])
                    right_eb_y = np.mean([p[1] for p in lm['right_eyebrow']])
                    left_eye_y = np.mean([p[1] for p in lm['left_eye']])
                    right_eye_y = np.mean([p[1] for p in lm['right_eye']])
                    
                    eb_eye_gap = ((left_eye_y - left_eb_y) + (right_eye_y - right_eb_y)) / 2.0
                    eb_eye_ratio = eb_eye_gap / float(height) if height > 0 else 0.15
                    
                    inner_eb_dist = np.linalg.norm(np.array(lm['left_eyebrow'][-1]) - np.array(lm['right_eyebrow'][0]))
                    eb_furrow_ratio = inner_eb_dist / float(width) if width > 0 else 0.25
                    
                    # Emotion Classification Matrix
                    if corner_lift > 0.4 or (mouth_w / float(width) > 0.38 and mar < 0.35):
                        smile_detected = True
                        emotion = "happy"
                    elif mar > 0.35 and eb_eye_ratio > 0.13:
                        emotion = "surprised"
                    elif eb_furrow_ratio < 0.13 or (eb_eye_ratio < 0.09 and corner_lift <= 0.0):
                        emotion = "focused"
                    elif corner_lift < -1.5:
                        emotion = "sad"
                    else:
                        emotion = "neutral"
            except Exception as e:
                log_event("WARNING", "FaceService", f"Landmark feature extraction failed: {str(e)}")

        # Fallback OpenCV image analysis when landmarks unavailable
        if not FACE_REC_AVAILABLE or emotion == "neutral":
            try:
                face_crop = rgb_image[max(0, top):bottom, max(0, left):right]
                if face_crop.size > 0:
                    gray = cv2.cvtColor(face_crop, cv2.COLOR_RGB2GRAY)
                    h_c, w_c = gray.shape
                    mouth_region = gray[int(h_c*0.65):, int(w_c*0.2):int(w_c*0.8)]
                    if mouth_region.size > 0:
                        std_m = np.std(mouth_region)
                        if std_m > 38.0 and not smile_detected:
                            smile_detected = True
                            if emotion == "neutral": emotion = "happy"
            except Exception:
                pass

        return {
            'blink_detected': blink_detected,
            'smile_detected': smile_detected,
            'emotion': emotion,
            'mask_detected': mask_detected
        }

# Global Singleton Instance
face_service = FaceService()
