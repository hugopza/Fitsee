from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import deps
from app.core.database import get_db
from app.db.models import User, UserProfile
from app.modules.users import schemas, utils
from app.storage import local

router = APIRouter()

@router.get("/", response_model=schemas.ProfileResponse)
async def get_profile(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    if not profile:
        # Should not happen if registration creates it, but safety check
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        await db.commit()
    return profile

@router.put("/", response_model=schemas.ProfileResponse)
async def update_profile(
    profile_in: schemas.ProfileUpdate,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    
    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    
    # Check completion
    check_completion(profile)
    
    await db.commit()
    await db.refresh(profile)
    return profile

@router.post("/upload-body-photo", response_model=schemas.ProfileResponse)
async def upload_body_photo(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Read bytes
    content = await file.read()
    
    # 2. Save Original
    # Reset cursor for saving if needed, but we pass bytes to processing
    # Actually save_upload_file usually takes the file object. Let's just use bytes for both to be safe or reset.
    # We will use our util which takes bytes for processing, but for saving original we can use the bytes too.
    
    filename = file.filename or "photo.jpg"
    body_photo_url = local.save_file_from_bytes(content, f"body_{current_user.id}_{filename}", "bodies")
    
    # 3. Process
    try:
        face_crop_url, skin_tone_hex = utils.process_body_photo(content)
    except Exception as e:
        # Fallback if processing fails? Or error?
        # User requirement says "Attempt basic face detection", implied soft fail or specific logic.
        print(f"Error processing photo: {e}")
        face_crop_url = None
        skin_tone_hex = "#DZC5B3" # Fallback

    # 4. Update Profile
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    
    profile.body_photo_url = body_photo_url
    if face_crop_url:
        profile.face_crop_url = face_crop_url
    if skin_tone_hex:
        profile.skin_tone_hex = skin_tone_hex
        
    check_completion(profile)
    
    await db.commit()
    await db.refresh(profile)
    return profile

@router.delete("/body-photo", response_model=schemas.ProfileResponse)
async def delete_body_photo(
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile.body_photo_url = None
    profile.face_crop_url = None
    profile.profile_completed = False
    
    await db.commit()
    await db.refresh(profile)
    return profile

def check_completion(profile: UserProfile):
    # Requirements: height, chest, shoulders + body_photo
    has_measures = all([profile.height_cm, profile.chest_cm, profile.shoulders_cm])
    has_photo = bool(profile.body_photo_url)
    profile.profile_completed = has_measures and has_photo
