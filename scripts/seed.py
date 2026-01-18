import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.core import security, config
from app.db.models import User, UserRole, UserProfile, Product, ProductVariant, MannequinAsset, GarmentAsset, FitType, SizeEnum, BodyType, AssetType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed():
    engine = create_async_engine(config.settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        # 1. Create Admin
        logger.info("Creating Admin...")
        result = await db.execute(select(User).where(User.email == config.settings.ADMIN_EMAIL))
        if not result.scalars().first():
            admin = User(
                email=config.settings.ADMIN_EMAIL,
                password_hash=security.get_password_hash(config.settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN
            )
            db.add(admin)
            await db.flush()
            # Admin Profile?
            admin_profile = UserProfile(user_id=admin.id, full_name="Admin User")
            db.add(admin_profile)
        
        # 2. Create Products
        logger.info("Creating Products...")
        products_data = [
            {"name": "Classic Tee", "fit_type": FitType.REGULAR, "description": "A classic regular fit tee."},
            {"name": "Street Oversize", "fit_type": FitType.OVERSIZE, "description": "Trendy oversized fit."},
            {"name": "Summer Crop", "fit_type": FitType.CROPPED, "description": "Perfect cropped tee."},
            {"name": "Boxy Heavy", "fit_type": FitType.BOXY, "description": "Heavyweight boxy fit."}
        ]

        for p_data in products_data:
            res = await db.execute(select(Product).where(Product.name == p_data["name"]))
            existing = res.scalars().first()
            if not existing:
                product = Product(
                    name=p_data["name"],
                    fit_type=p_data["fit_type"],
                    description=p_data["description"],
                    category="tshirt"
                )
                db.add(product)
                await db.flush()
                
                # Create Variants
                for size in SizeEnum:
                    v = ProductVariant(product_id=product.id, size=size, is_active=True)
                    db.add(v)
                
                # Create Placeholder Garment Assets
                for size in SizeEnum:
                    asset = GarmentAsset(
                        product_id=product.id,
                        size=size,
                        asset_type=AssetType.OVERLAY_FRONT,
                        url=f"/static/garments/placeholders/{product.fit_type.value}_{size.value}_front.png"
                    )
                    db.add(asset)

        # 3. Create Default Mannequin
        logger.info("Creating Mannequin...")
        res = await db.execute(select(MannequinAsset).where(MannequinAsset.body_type == BodyType.DEFAULT))
        if not res.scalars().first():
            mannequin = MannequinAsset(
                body_type=BodyType.DEFAULT,
                video_url="/static/mannequin/default.mp4",
                duration_ms=2000,
                rotation_degrees=180
            )
            db.add(mannequin)

        await db.commit()
    
    logger.info("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())
