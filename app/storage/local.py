import shutil
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

def save_upload_file(upload_file: UploadFile, sub_folder: str) -> str:
    path = Path(settings.UPLOAD_DIR) / sub_folder
    path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename to avoid collisions? For now just use original name as per req implying simplicity or prepend UUID.
    # Safe simple approach: timestamp or uuid prepend
    import uuid
    extension = Path(upload_file.filename).suffix
    new_filename = f"{uuid.uuid4()}{extension}"
    dest_path = path / new_filename
    
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    # Return relative URL compliant with StaticFiles mount
    # Mounted at /static/uploads
    return f"/static/uploads/{sub_folder}/{new_filename}"

def save_file_from_bytes(data: bytes, filename: str, sub_folder: str) -> str:
    path = Path(settings.UPLOAD_DIR) / sub_folder
    path.mkdir(parents=True, exist_ok=True)
    
    dest_path = path / filename
    with dest_path.open("wb") as buffer:
        buffer.write(data)
        
    return f"/static/uploads/{sub_folder}/{filename}"
