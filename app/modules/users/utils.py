import cv2
import numpy as np
import uuid
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from app.storage.local import save_file_from_bytes

# Load Haar Cascade
# In a real build, we'd ensure this file exists. 
# OpenCV usually bundles it, or we can use the one from cv2.data
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def process_body_photo(file_bytes: bytes):
    """
    1. Detect face -> crop -> save
    2. Extract skin tone
    Returns: (face_crop_url, skin_tone_hex)
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    face_crop_url = None
    skin_tone_hex = "#DZC5B3" # Default fallback
    
    skin_sample_region = None
    
    if len(faces) > 0:
        # Pick largest face
        (x, y, w, h) = max(faces, key=lambda r: r[2] * r[3])
        
        # Crop face
        face_img = img[y:y+h, x:x+w]
        
        # Save face crop
        # Encode back to jpg
        success, buffer = cv2.imencode(".jpg", face_img)
        if success:
            face_filename = f"face_{uuid.uuid4()}.jpg"
            face_crop_url = save_file_from_bytes(buffer.tobytes(), face_filename, "faces")
            
        # Sample region for skin tone: center of the face
        center_x, center_y = w // 2, h // 2
        sw, sh = w // 4, h // 4 # small window
        skin_sample_region = face_img[center_y-sh:center_y+sh, center_x-sw:center_x+sw]
        
    else:
        # No face, fallback to center of upper body
        h, w, _ = img.shape
        center_x, center_y = w // 2, h // 4
        sw, sh = w // 8, h // 8
        skin_sample_region = img[center_y-sh:center_y+sh, center_x-sw:center_x+sw]

    if skin_sample_region is not None and skin_sample_region.size > 0:
        # Calculate mean color
        avg_color_per_row = np.average(skin_sample_region, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        # Convert BGR to Hex
        b, g, r = int(avg_color[0]), int(avg_color[1]), int(avg_color[2])
        skin_tone_hex = "#{:02x}{:02x}{:02x}".format(r, g, b)

    return face_crop_url, skin_tone_hex
