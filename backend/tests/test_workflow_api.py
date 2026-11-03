import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_four_agent_workflow_full_lifecycle(client):
    """Test complete coordinated 7-step product workflow connecting all four agents."""
    unique = uuid4().hex[:6]
    artisan_email = f"artisan_wf_{unique}@karigar.com"
    pwd = "ArtisanPassword123!"

    # Register & Login
    client.post(
        "/api/auth/register",
        json={
            "email": artisan_email,
            "password": pwd,
            "full_name": f"Artisan WF {unique}",
            "role": "artisan",
            "craft_type": "Bamboo Crafts",
        },
    )
    login_res = client.post("/api/auth/login", json={"email": artisan_email, "password": pwd})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # STEP 1: Product Draft Initiation
    create_payload = {
        "product_name": "Handmade Bamboo Lamp Shade",
        "category": "Lighting & Home Decor",
        "initial_material": "Bamboo",
        "initial_craft_type": "Handwoven Lattice",
        "language": "en",
    }
    step1_res = client.post("/api/workflow/products", headers=headers, json=create_payload)
    assert step1_res.status_code == 201
    wf_data = step1_res.json()
    product_id = wf_data["product_id"]
    assert wf_data["workflow_status"] == "draft"

    # STEP 3: Catalog Review & Approval
    catalog_payload = {
        "product_title": "Eco-friendly Handwoven Bamboo Lattice Lamp Shade",
        "description": "Exquisite hand-carved and woven bamboo lamp shade casting ambient warm geometric light patterns.",
        "keywords": ["bamboo", "lamp shade", "pendant light", "handwoven", "eco-friendly"],
        "material": "Bamboo",
        "craft_type": "Handwoven Lattice",
        "color": "Natural Bamboo Amber",
        "purpose": "Home Decor & Lighting",
    }
    step3_res = client.post(
        f"/api/workflow/products/{product_id}/catalog",
        headers=headers,
        json=catalog_payload,
    )
    assert step3_res.status_code == 200
    assert step3_res.json()["workflow_status"] == "catalog_approved"
    assert step3_res.json()["catalog"]["product_title"] == catalog_payload["product_title"]

    # STEP 4: Dynamic Pricing Execution
    pricing_payload = {
        "material_cost": 250.0,
        "labor_cost": 200.0,
        "packaging_cost": 40.0,
        "overhead_cost": 30.0,
        "shipping_cost": 80.0,
        "target_profit_margin_percent": 25.0,
        "marketplace_commission_percent": 10.0,
        "pricing_strategy": "round_nearest_rupee",
    }
    step4_res = client.post(
        f"/api/workflow/products/{product_id}/pricing",
        headers=headers,
        json=pricing_payload,
    )
    assert step4_res.status_code == 200
    p_data = step4_res.json()
    assert p_data["workflow_status"] == "pricing_calculated"
    assert p_data["pricing"] is not None
    assert p_data["pricing"]["suggested_selling_price"] > 0

    # STEP 5: Inventory & Capacity Configuration
    inv_payload = {
        "available_quantity": 25,
        "production_capacity_per_month": 80,
        "minimum_order_quantity": 2,
        "production_lead_time_days": 10,
        "location": "Assam, India",
    }
    step5_res = client.post(
        f"/api/workflow/products/{product_id}/inventory",
        headers=headers,
        json=inv_payload,
    )
    assert step5_res.status_code == 200
    assert step5_res.json()["workflow_status"] == "inventory_configured"

    # STEP 6: Market Linkage Matching
    step6_res = client.get(
        f"/api/workflow/products/{product_id}/matches?min_score=20",
        headers=headers,
    )
    assert step6_res.status_code == 200
    assert "matches" in step6_res.json()

    # STEP 7: Product Publication
    step7_res = client.post(
        f"/api/workflow/products/{product_id}/publish",
        headers=headers,
    )
    assert step7_res.status_code == 200
    final_state = step7_res.json()
    assert final_state["workflow_status"] == "published"
    assert "product_published" in final_state["steps_completed"]

    # List Products
    list_res = client.get("/api/workflow/products", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total_records"] >= 1


def test_workflow_ownership_protection(client):
    """Verify unauthorized users cannot access another artisan's workflow."""
    u1, u2 = uuid4().hex[:6], uuid4().hex[:6]

    # Artisan 1
    client.post("/api/auth/register", json={"email": f"a1_{u1}@k.com", "password": "Pass123!", "full_name": "A1", "role": "artisan"})
    t1 = client.post("/api/auth/login", json={"email": f"a1_{u1}@k.com", "password": "Pass123!"}).json()["access_token"]

    # Artisan 2
    client.post("/api/auth/register", json={"email": f"a2_{u2}@k.com", "password": "Pass123!", "full_name": "A2", "role": "artisan"})
    t2 = client.post("/api/auth/login", json={"email": f"a2_{u2}@k.com", "password": "Pass123!"}).json()["access_token"]

    # Artisan 1 creates product
    p_res = client.post(
        "/api/workflow/products",
        headers={"Authorization": f"Bearer {t1}"},
        json={"product_name": "Artisan 1 Lamp"},
    )
    pid = p_res.json()["product_id"]

    # Artisan 2 attempts to view product -> 403 Forbidden
    unauth_res = client.get(
        f"/api/workflow/products/{pid}",
        headers={"Authorization": f"Bearer {t2}"},
    )
    assert unauth_res.status_code == 403
