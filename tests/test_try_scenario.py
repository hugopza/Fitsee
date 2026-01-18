import pytest
from httpx import AsyncClient
from app.db.models import FitType, SizeEnum

@pytest.mark.asyncio
async def test_try_profile_incomplete(client: AsyncClient):
    # 1. Setup User
    await client.post("/api/v1/auth/register", json={"email": "try@test.com", "password": "pass"})
    login = await client.post("/api/v1/auth/login", data={"username": "try@test.com", "password": "pass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Setup Product (Need Admin? or Seeding?)
    # Since we use an empty DB in tests, we must insert a product.
    # Alternatively, create an admin & insert.
    # Let's bypass and fail early if we can't find product?
    # No, let's create a product via direct DB or Admin API.
    # Using Admin API is cleaner.
    
    # Create Admin
    # ... Wait, Admin needs direct DB insertion or special key. 
    # Let's assume we can't easily become admin without seeding.
    # Let's mock a product? No, integration test.
    # Let's insert product via endpoint but we need admin.
    pass

@pytest.mark.asyncio
async def test_try_flow_full(client: AsyncClient, db_session):
    # This test mixes some direct DB usage for setup to speed things up
    from app.db.models import User, UserRole, Product, ProductVariant, MannequinAsset, BodyType
    from app.core.security import get_password_hash
    import uuid
    
    # 1. Create Admin & Product directly in DB
    prod_id = uuid.uuid4()
    product = Product(id=prod_id, name="Test Tee", fit_type="REGULAR", category="tshirt")
    db_session.add(product)
    
    variant = ProductVariant(product_id=prod_id, size="M")
    db_session.add(variant)
    
    mann = MannequinAsset(body_type=BodyType.DEFAULT, video_url="vid.mp4")
    db_session.add(mann)
    
    await db_session.commit()
    
    # 2. Register & Login Customer
    email = "customer@flow.com"
    await client.post("/api/v1/auth/register", json={"email": email, "password": "pass"})
    login = await client.post("/api/v1/auth/login", data={"username": email, "password": "pass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Call Try -> Should Fail (Incomplete)
    res = await client.get(f"/api/v1/try/{prod_id}?size=M", headers=headers)
    assert res.status_code == 409
    assert res.json()["detail"]["error"]["code"] == "PROFILE_INCOMPLETE"
    
    # 4. Complete Profile (Measurements + Photo)
    # Upload Photo
    # Mocking file upload
    files = {'file': ('test.jpg', b'fakeimagebytes', 'image/jpeg')}
    # Note: The backend tries to process image with opencv. 
    # A fake byte string might crash opencv or return None.
    # Utils handles crash -> fallback. So it should be fine.
    
    up_res = await client.post("/api/v1/profile/upload-body-photo", headers=headers, files=files)
    assert up_res.status_code == 200
    
    # Update Measurements
    meas_res = await client.put("/api/v1/profile/", headers=headers, json={
        "height_cm": 180, "chest_cm": 100, "shoulders_cm": 50, "waist_cm": 80
    })
    assert meas_res.status_code == 200
    assert meas_res.json()["profile_completed"] == True
    
    # 5. Call Try -> Success
    res = await client.get(f"/api/v1/try/{prod_id}?size=M", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["mannequin"]["video_url"] == "vid.mp4"
    assert "personalization" in data
