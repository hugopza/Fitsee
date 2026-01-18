from typing import Optional
from pydantic import BaseModel, HttpUrl

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    height_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    shoulders_cm: Optional[float] = None
    waist_cm: Optional[float] = None

class ProfileResponse(BaseModel):
    full_name: Optional[str] = None
    height_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    shoulders_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    
    body_photo_url: Optional[str] = None
    face_crop_url: Optional[str] = None
    skin_tone_hex: Optional[str] = None
    profile_completed: bool

    class Config:
        from_attributes = True
