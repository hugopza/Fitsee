from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core import deps
from app.core.database import get_db
from app.db.models import Product, ProductVariant, User, MannequinAsset, GarmentAsset, BodyType
from app.modules.catalog import schemas
from app.storage import local

router = APIRouter()
admin_router = APIRouter() # Mounted at /admin

# --- PUBLIC ENDPOINTS ---

@router.get("/products", response_model=List[schemas.ProductResponse])
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: Optional[str] = None,
    fit_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    query = select(Product).where(Product.is_active == True)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if fit_type:
        query = query.where(Product.fit_type == fit_type)
        
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    # Using unique() if joined loading, but we are lazy loading variants in Pydantic or need selectinload.
    # For simplicitly, let's rely on Pydantic's lazy load or explicit join if needed.
    # Async lazy loading is tricky. Let's use explicit eager load options in a real app, 
    # but for this snippet we'll let it slide or fix if errors pop up. 
    # FIX: Add options(selectinload(Product.variants))
    from sqlalchemy.orm import selectinload
    query = query.options(selectinload(Product.variants))
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/products/{id}", response_model=schemas.ProductResponse)
async def get_product(
    id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from sqlalchemy.orm import selectinload
    query = select(Product).where(Product.id == id).options(selectinload(Product.variants))
    product = await db.scalar(query)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/products/{id}/variants", response_model=List[schemas.VariantResponse])
async def get_product_variants(
    id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    query = select(ProductVariant).where(ProductVariant.product_id == id)
    result = await db.execute(query)
    return result.scalars().all()


# --- ADMIN ENDPOINTS ---

@admin_router.post("/products", response_model=schemas.ProductResponse)
async def create_product(
    product_in: schemas.ProductCreate,
    current_user: Annotated[User, Depends(deps.get_current_active_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    product = Product(**product_in.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@admin_router.put("/products/{id}", response_model=schemas.ProductResponse)
async def update_product(
    id: UUID,
    product_in: schemas.ProductCreate,
    current_user: Annotated[User, Depends(deps.get_current_active_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    product = await db.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    for field, value in product_in.model_dump().items():
        setattr(product, field, value)
        
    await db.commit()
    await db.refresh(product)
    return product

@admin_router.delete("/products/{id}")
async def delete_product(
    id: UUID,
    current_user: Annotated[User, Depends(deps.get_current_active_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    product = await db.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False # Soft delete
    await db.commit()
    return {"status": "deleted"}

@admin_router.post("/products/{id}/variants")
async def create_variants_bulk(
    id: UUID,
    current_user: Annotated[User, Depends(deps.get_current_active_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Auto-generate XS-XL
    from app.db.models import SizeEnum
    variants = []
    for size in SizeEnum:
        v = ProductVariant(product_id=id, size=size, is_active=True)
        db.add(v)
        variants.append(v)
    
    await db.commit()
    return {"message": "Variants created", "count": len(variants)}

@admin_router.post("/products/{id}/upload-garment-asset")
async def upload_garment_asset(
    id: UUID,
    asset_data: Annotated[schemas.GarmentAssetCreate, Depends()],
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(deps.get_current_active_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    url = local.save_upload_file(file, f"garments/{id}/{asset_data.size.value}")
    
    asset = GarmentAsset(
        product_id=id,
        size=asset_data.size,
        asset_type=asset_data.asset_type,
        url=url,
        note=asset_data.note
    )
    # Upsert logic could be better, but simple add for now
    db.add(asset)
    await db.commit()
    return {"status": "uploaded", "url": url}

@admin_router.post("/mannequin/upload-video")
async def upload_mannequin_video(
    video_url: Optional[str] = None, # Allow passing direct URL
    file: Optional[UploadFile] = File(None), # Or uploading file
    current_user: Annotated[User, Depends(deps.get_current_active_admin)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Uploads a file OR stores a URL for the DEFAULT mannequin.
    """
    final_url = video_url
    
    if file:
        final_url = local.save_upload_file(file, "mannequin")
    
    if not final_url:
         raise HTTPException(status_code=400, detail="Provide video_url or file")

    # Update or Create DEFAULT mannequin asset
    result = await db.execute(select(MannequinAsset).where(MannequinAsset.body_type == BodyType.DEFAULT))
    asset = result.scalars().first()
    
    if not asset:
        asset = MannequinAsset(body_type=BodyType.DEFAULT, video_url=final_url)
        db.add(asset)
    else:
        asset.video_url = final_url
        
    await db.commit()
    return {"status": "updated", "video_url": final_url}
