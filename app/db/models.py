import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Float, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class UserRole(str, PyEnum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"

class FitType(str, PyEnum):
    REGULAR = "REGULAR"
    OVERSIZE = "OVERSIZE"
    CROPPED = "CROPPED"
    BOXY = "BOXY"

class SizeEnum(str, PyEnum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"

class AssetType(str, PyEnum):
    OVERLAY_FRONT = "OVERLAY_FRONT"
    OVERLAY_BACK = "OVERLAY_BACK"

class BodyType(str, PyEnum):
    DEFAULT = "DEFAULT"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    full_name: Mapped[Optional[str]] = mapped_column(String)
    
    # Measurements
    height_cm: Mapped[Optional[float]] = mapped_column(Float)
    chest_cm: Mapped[Optional[float]] = mapped_column(Float)
    shoulders_cm: Mapped[Optional[float]] = mapped_column(Float)
    waist_cm: Mapped[Optional[float]] = mapped_column(Float)

    # Photo Data
    body_photo_url: Mapped[Optional[str]] = mapped_column(String)
    face_crop_url: Mapped[Optional[str]] = mapped_column(String)
    skin_tone_hex: Mapped[Optional[str]] = mapped_column(String)
    
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="profile")

class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[Optional[str]] = mapped_column(String)
    brand: Mapped[Optional[str]] = mapped_column(String)
    category: Mapped[str] = mapped_column(String, default="tshirt")
    fit_type: Mapped[FitType] = mapped_column(Enum(FitType))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    garment_assets: Mapped[List["GarmentAsset"]] = relationship("GarmentAsset", back_populates="product", cascade="all, delete-orphan")

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    image_url: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["Product"] = relationship("Product", back_populates="images")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    size: Mapped[SizeEnum] = mapped_column(Enum(SizeEnum))
    sku: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")

class GarmentAsset(Base):
    __tablename__ = "garment_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    size: Mapped[SizeEnum] = mapped_column(Enum(SizeEnum))
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType))
    url: Mapped[str] = mapped_column(String)
    note: Mapped[Optional[str]] = mapped_column(String)

    product: Mapped["Product"] = relationship("Product", back_populates="garment_assets")

    __table_args__ = (UniqueConstraint('product_id', 'size', 'asset_type', name='_product_size_asset_uc'),)

class MannequinAsset(Base):
    __tablename__ = "mannequin_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body_type: Mapped[BodyType] = mapped_column(Enum(BodyType), default=BodyType.DEFAULT)
    video_url: Mapped[str] = mapped_column(String)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    rotation_degrees: Mapped[int] = mapped_column(Integer, default=180)

class RenderJobStatus(str, PyEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"

class RenderJob(Base):
    __tablename__ = "render_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    size: Mapped[SizeEnum] = mapped_column(Enum(SizeEnum))
    status: Mapped[RenderJobStatus] = mapped_column(Enum(RenderJobStatus), default=RenderJobStatus.QUEUED)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    video_url: Mapped[Optional[str]] = mapped_column(String)
    error_message: Mapped[Optional[str]] = mapped_column(String)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User")
    product: Mapped["Product"] = relationship("Product")
