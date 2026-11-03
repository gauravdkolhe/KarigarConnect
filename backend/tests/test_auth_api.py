import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_auth_register_and_login_flow(client):
    """Test user registration, login, and retrieval of authenticated profile."""
    unique_suffix = uuid4().hex[:6]
    email = f"artisan_{unique_suffix}@karigar.example.com"
    password = "SecurePassword123!"

    # 1. Register Artisan
    register_payload = {
        "email": email,
        "password": password,
        "full_name": f"Artisan {unique_suffix}",
        "role": "artisan",
        "phone": "+91-9876543210",
        "location": "Varanasi, UP, India",
        "business_name": "Varanasi Weavers Guild",
        "craft_type": "Silk Brocade Weaving",
        "product_categories": ["Textiles", "Apparel", "Home Decor"],
        "workshop_location": "Varanasi Silk Cluster",
        "bio": "Generational silk weaver crafting traditional Banarasi textiles.",
    }
    reg_res = client.post("/api/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == email.lower()
    assert user_data["role"] == "artisan"
    assert user_data["user_id"].startswith("USER-ART-")

    # 2. Duplicate registration rejected
    dup_res = client.post("/api/auth/register", json=register_payload)
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]

    # 3. Invalid credentials login rejected
    bad_login = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword"})
    assert bad_login.status_code == 401

    # 4. Successful login returns JWT
    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    assert token_data["user"]["email"] == email.lower()

    # 5. Access /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user_id"] == user_data["user_id"]
    assert me_data["full_name"] == register_payload["full_name"]

    # 6. Update profile
    update_res = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"bio": "Updated biography with national craft awards."},
    )
    assert update_res.status_code == 200
    assert update_res.json()["bio"] == "Updated biography with national craft awards."


def test_auth_buyer_registration(client):
    """Test buyer registration with buyer-specific fields."""
    unique_suffix = uuid4().hex[:6]
    email = f"buyer_{unique_suffix}@retailer.example.com"

    register_payload = {
        "email": email,
        "password": "BuyerPassword123!",
        "full_name": f"Buyer {unique_suffix}",
        "role": "buyer",
        "business_name": "FabIndia Lifestyle Corp",
        "buyer_type": "Retailer",
        "location": "Mumbai, India",
        "procurement_interests": ["Bamboo Crafts", "Pottery", "Handloom"],
    }
    reg_res = client.post("/api/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["role"] == "buyer"
    assert reg_res.json()["user_id"].startswith("USER-BUY-")


def test_admin_bootstrap_login(client):
    """Verify system admin account is pre-provisioned and can authenticate."""
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@karigarconnect.com", "password": "Admin@Karigar2026"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "admin"
    assert "access_token" in data
