from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.db.models import SizeEnum, RenderJobStatus

class RenderJobCreate(BaseModel):
    product_id: UUID
    size: SizeEnum

class RenderJobResponse(BaseModel):
    job_id: UUID
    product_id: UUID
    size: SizeEnum
    status: RenderJobStatus
    progress: int
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
