from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core import deps
from app.core.database import get_db
from app.db.models import User, UserProfile, Product, GarmentAsset, MannequinAsset, BodyType, SizeEnum, AssetType

router = APIRouter()

@router.get("/{product_id}")
async def try_product(
    product_id: UUID,
    size: SizeEnum,
    current_user: Annotated[User, Depends(deps.get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Validate Profile
    profile = await db.scalar(select(UserProfile).where(UserProfile.user_id == current_user.id))
    if not profile or not profile.profile_completed:
        missing = []
        if not profile: missing = ["all"]
        else:
            if not profile.height_cm: missing.append("height_cm")
            if not profile.chest_cm: missing.append("chest_cm")
            if not profile.shoulders_cm: missing.append("shoulders_cm")
            if not profile.body_photo_url: missing.append("body_photo_url")
            
        return HTTPException(
            status_code=409, 
            detail={
                "error": {
                    "code": "PROFILE_INCOMPLETE", 
                    "message": "User profile is incomplete.",
                    "details": {"missing_fields": missing}
                }
            }
        )

    # 2. Get Product & Size
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # 3. Get Mannequin (Default)
    mannequin = await db.scalar(select(MannequinAsset).where(MannequinAsset.body_type == BodyType.DEFAULT))
    if not mannequin:
         # Check if seed or fallback exists
         # In MVP, this might be null if not seeded.
         pass 

    # 4. Get Garment Assets
    assets_query = select(GarmentAsset).where(
        GarmentAsset.product_id == product_id,
        GarmentAsset.size == size
    )
    assets = (await db.execute(assets_query)).scalars().all()
    
    front_clean = next((a.url for a in assets if a.asset_type == AssetType.OVERLAY_FRONT), None)
    back_clean = next((a.url for a in assets if a.asset_type == AssetType.OVERLAY_BACK), None)

    return {
        "product": {
            "id": product.id,
            "name": product.name,
            "fit_type": product.fit_type
        },
        "selected_size": size,
        "mannequin": {
            "body_type": mannequin.body_type if mannequin else "DEFAULT",
            "video_url": mannequin.video_url if mannequin else None,
            "rotation_degrees": mannequin.rotation_degrees if mannequin else 180,
            "duration_ms": mannequin.duration_ms if mannequin else None
        },
        "personalization": {
            "skin_tone_hex": profile.skin_tone_hex,
            "face_crop_url": profile.face_crop_url
        },
        "garment": {
            "overlay_front_url": front_clean,
            "overlay_back_url": back_clean
        }
    }
