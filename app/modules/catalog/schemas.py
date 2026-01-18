import uuid
from typing import List, Optional
from pydantic import BaseModel
from app.db.models import FitType, SizeEnum, AssetType, BodyType

class VariantBase(BaseModel):
    size: SizeEnum
    sku: Optional[str] = None
    is_active: bool = True

class VariantCreate(VariantBase):
    pass

class VariantResponse(VariantBase):
    id: uuid.UUID
    product_id: uuid.UUID

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    category: str = "tshirt"
    fit_type: FitType
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: uuid.UUID
    variants: List[VariantResponse] = []

    class Config:
        from_attributes = True

class GarmentAssetCreate(BaseModel):
    size: SizeEnum
    asset_type: AssetType
    note: Optional[str] = None

class MannequinAssetCreate(BaseModel):
    video_url: str
    duration_ms: Optional[int] = None
    rotation_degrees: int = 180
