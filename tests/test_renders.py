from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.models import User, Product, ProductVariant, SizeEnum, FitType, RenderJob, UserProfile

# Mocks or setup fixtures might be needed depending on existing test infra.
# Assuming basic client setup.

client = TestClient(app)

def test_create_render_job_incomplete_profile(db: Session, normal_user_token_headers, test_user):
    # Ensure profile is empty
    if test_user.profile:
        db.delete(test_user.profile)
        db.commit()
    
    # Create product
    product = Product(name="Test Tee", category="tshirt", fit_type=FitType.REGULAR)
    db.add(product)
    db.commit()

    response = client.post(
        "/api/v1/renders/",
        headers=normal_user_token_headers,
        json={"product_id": str(product.id), "size": "M"}
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PROFILE_MISSING" or response.json()["detail"]["code"] == "PROFILE_INCOMPLETE"

def test_create_render_job_success(db: Session, normal_user_token_headers, test_user):
    # Setup profile
    if not test_user.profile:
        profile = UserProfile(user_id=test_user.id, height_cm=180, chest_cm=100, shoulders_cm=50)
        db.add(profile)
    else:
        test_user.profile.height_cm = 180
        test_user.profile.chest_cm = 100
        test_user.profile.shoulders_cm = 50
    db.commit()

    # Create product
    product = Product(name="Render Tee", category="tshirt", fit_type=FitType.REGULAR)
    db.add(product)
    db.commit()

    # Mock Redis enqueue? 
    # For integration test, if redis is not running, this might fail or we need to mock service.queue.enqueue
    # Here we assume we want to test the API logic.
    # Note: real integration requires Redis.
    
    # We will patch queue enqueue to avoid redis dependency in unit test
    from unittest.mock import patch
    with patch("app.modules.renders.service.queue.enqueue") as mock_enqueue:
        response = client.post(
            "/api/v1/renders/",
            headers=normal_user_token_headers,
            json={"product_id": str(product.id), "size": "L"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "QUEUED"
        assert "job_id" in data
        assert mock_enqueue.called

def test_get_render_job_ownership(db: Session, normal_user_token_headers, test_user):
    # Create a job manually
    product = Product(name="Owner Tee", category="tshirt", fit_type=FitType.REGULAR)
    db.add(product)
    db.commit()
    
    job = RenderJob(user_id=test_user.id, product_id=product.id, size=SizeEnum.M)
    db.add(job)
    db.commit()

    response = client.get(
        f"/api/v1/renders/{job.id}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    assert response.json()["job_id"] == str(job.id)

def test_get_render_job_forbidden(db: Session, normal_user_token_headers, test_user):
    # Create job for ANOTHER user
    other_user = User(email="other@test.com", password_hash="hash")
    db.add(other_user)
    db.commit()
    
    product = Product(name="Other Tee", category="tshirt", fit_type=FitType.REGULAR)
    db.add(product)
    db.commit()
    
    job = RenderJob(user_id=other_user.id, product_id=product.id, size=SizeEnum.M)
    db.add(job)
    db.commit()

    response = client.get(
        f"/api/v1/renders/{job.id}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 403
