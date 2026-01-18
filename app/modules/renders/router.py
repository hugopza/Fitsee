from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.router import get_current_user
from app.db.models import User, Product, UserProfile
from app.modules.renders import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.RenderJobResponse)
def create_render_job(
    request: schemas.RenderJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check Profile Completeness
    if not current_user.profile:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PROFILE_MISSING", "message": "User profile not found."}
        )
    
    # Simple completeness check based on required fields
    # height_cm, chest_cm, shoulders_cm required
    missing = []
    if not current_user.profile.height_cm: missing.append("height_cm")
    if not current_user.profile.chest_cm: missing.append("chest_cm")
    if not current_user.profile.shoulders_cm: missing.append("shoulders_cm")
    
    if missing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PROFILE_INCOMPLETE", 
                "message": "Complete your profile measurements first.",
                "details": {"missing_fields": missing}
            }
        )

    # 2. Check Product Exists
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    # 3. Create Job
    job = service.create_render_job(
        db=db,
        user_id=current_user.id,
        product_id=request.product_id,
        size=request.size
    )
    return job

@router.get("/{job_id}", response_model=schemas.RenderJobResponse)
def get_render_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = service.get_render_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Ownership check
    if job.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    return job
