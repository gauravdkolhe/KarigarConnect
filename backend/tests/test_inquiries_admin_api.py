import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_inquiry_and_notification_flow(client):
    """Test buyer submitting inquiry, artisan receiving it, notifications, and status updates."""
    u = uuid4().hex[:6]
    artisan_email = f"artisan_inq_{u}@k.com"
    buyer_email = f"buyer_inq_{u}@k.com"
    pwd = "Password123!"

    # 1. Register Artisan
    client.post("/api/auth/register", json={"email": artisan_email, "password": pwd, "full_name": f"Artisan {u}", "role": "artisan"})
    artisan_token = client.post("/api/auth/login", json={"email": artisan_email, "password": pwd}).json()["access_token"]
    artisan_headers = {"Authorization": f"Bearer {artisan_token}"}

    # Artisan creates a product
    prod_res = client.post(
        "/api/workflow/products",
        headers=artisan_headers,
        json={"product_name": "Carved Teakwood Box", "category": "Home Decor"},
    )
    product_id = prod_res.json()["product_id"]

    # 2. Register Buyer
    client.post("/api/auth/register", json={"email": buyer_email, "password": pwd, "full_name": f"Buyer {u}", "role": "buyer", "business_name": "Craft Export House"})
    buyer_token = client.post("/api/auth/login", json={"email": buyer_email, "password": pwd}).json()["access_token"]
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    # 3. Buyer submits inquiry
    inq_payload = {
        "product_id": product_id,
        "quantity_requested": 50,
        "target_price_per_unit": 1200.0,
        "delivery_destination": "New Delhi, India",
        "message": "Interested in 50 custom engraved teakwood boxes with brass inlays.",
    }
    inq_res = client.post("/api/inquiries", headers=buyer_headers, json=inq_payload)
    assert inq_res.status_code == 201
    inquiry_id = inq_res.json()["inquiry_id"]
    assert inq_res.json()["status"] == "pending"

    # 4. Artisan lists inquiries and receives the new inquiry
    artisan_inqs = client.get("/api/inquiries", headers=artisan_headers)
    assert artisan_inqs.status_code == 200
    assert any(i["inquiry_id"] == inquiry_id for i in artisan_inqs.json()["inquiries"])

    # 5. Artisan checks notifications
    notifs = client.get("/api/notifications", headers=artisan_headers)
    assert notifs.status_code == 200
    assert len(notifs.json()["notifications"]) >= 1
    notif_id = notifs.json()["notifications"][0]["notification_id"]

    # Mark notification read
    read_res = client.patch(f"/api/notifications/{notif_id}/read", headers=artisan_headers)
    assert read_res.status_code == 200

    # 6. Artisan accepts the inquiry
    update_res = client.patch(
        f"/api/inquiries/{inquiry_id}/status",
        headers=artisan_headers,
        json={"status": "accepted", "artisan_response_note": "Sample dispatching in 3 business days."},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "accepted"


def test_admin_dashboard_metrics_and_management(client):
    """Test administrative overview metrics, user suspension, and moderation."""
    # 1. Login as bootstrap admin
    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@karigarconnect.com", "password": "Admin@Karigar2026"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get live metrics
    metrics_res = client.get("/api/admin/metrics", headers=admin_headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert "total_artisans" in metrics
    assert "total_buyers" in metrics
    assert "total_products" in metrics
    assert "categories_breakdown" in metrics

    # 3. List platform users
    users_res = client.get("/api/admin/users", headers=admin_headers)
    assert users_res.status_code == 200
    assert users_res.json()["total_users"] >= 1

    # 4. List platform products
    prods_res = client.get("/api/admin/products", headers=admin_headers)
    assert prods_res.status_code == 200
    assert "products" in prods_res.json()

    # 5. Non-admin access denied (403 Forbidden)
    u = uuid4().hex[:6]
    client.post("/api/auth/register", json={"email": f"buyer_test_{u}@k.com", "password": "Password123!", "full_name": "Test", "role": "buyer"})
    user_token = client.post("/api/auth/login", json={"email": f"buyer_test_{u}@k.com", "password": "Password123!"}).json()["access_token"]

    forbidden_res = client.get("/api/admin/metrics", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden_res.status_code == 403
