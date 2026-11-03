import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Buyer Requirement Management API Tests
# ---------------------------------------------------------------------------

def test_api_create_and_retrieve_buyer_requirement(client):
    """Test creating a buyer requirement and retrieving it with masking."""
    payload = {
        "buyer_id": "BUYER_TEST_1",
        "buyer_name": "FabIndia Lifestyle Ltd",
        "buyer_type": "Retailer",
        "required_category": "Storage",
        "requirement_title": "Eco-friendly Storage Baskets",
        "description": "Looking for 100 units of sturdy natural bamboo storage baskets.",
        "required_keywords": ["bamboo", "storage", "basket"],
        "preferred_materials": ["bamboo"],
        "preferred_craft_types": ["handwoven"],
        "required_quantity": 100,
        "minimum_budget": 600.0,
        "maximum_budget": 1000.0,
        "currency": "INR",
        "delivery_location": "Mumbai, Maharashtra, India",
        "delivery_deadline_days": 30,
        "contact_email": "procurement@fabindia.example.com",
        "contact_phone": "+91-9876543210",
        "requirement_status": "active",
    }

    create_res = client.post("/api/buyers/requirements", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    req_id = created_data["requirement_id"]
    assert req_id.startswith("REQ-")
    assert created_data["buyer_name"] == "FabIndia Lifestyle Ltd"

    # Public retrieval (masked)
    get_res = client.get(f"/api/buyers/requirements/{req_id}")
    assert get_res.status_code == 200
    public_data = get_res.json()
    assert public_data["contact_email"] != "procurement@fabindia.example.com"
    assert "***" in public_data["contact_email"]
    assert "***" in public_data["contact_phone"]

    # Authorized retrieval (unmasked)
    auth_res = client.get(f"/api/buyers/requirements/{req_id}?authorized=true")
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    assert auth_data["contact_email"] == "procurement@fabindia.example.com"
    assert auth_data["contact_phone"] == "+91-9876543210"


def test_api_list_buyer_requirements_with_pagination(client):
    """Test listing buyer requirements with pagination and status filter."""
    res = client.get("/api/buyers/requirements?status=active&limit=10&skip=0")
    assert res.status_code == 200
    data = res.json()
    assert "total_records" in data
    assert "requirements" in data
    assert isinstance(data["requirements"], list)
    if data["requirements"]:
        first = data["requirements"][0]
        assert "requirement_id" in first
        # Verify contact masking in public listings
        if first.get("contact_email"):
            assert "***" in first["contact_email"]


def test_api_update_requirement_and_status(client):
    """Test updating requirement fields and transitioning status."""
    # Create requirement
    payload = {
        "buyer_id": "BUYER_TEST_UPD",
        "buyer_name": "Update Test Buyer",
        "buyer_type": "Wholesaler",
        "required_category": "Home Decor",
        "requirement_title": "Initial Requirement Title",
        "description": "Initial requirement description details here.",
        "required_quantity": 50,
        "minimum_budget": 400.0,
        "maximum_budget": 800.0,
        "delivery_location": "Bangalore",
    }
    create_res = client.post("/api/buyers/requirements", json=payload)
    req_id = create_res.json()["requirement_id"]

    # Update description & budget
    upd_payload = {
        "requirement_title": "Updated Requirement Title",
        "maximum_budget": 850.0,
    }
    upd_res = client.put(f"/api/buyers/requirements/{req_id}", json=upd_payload)
    assert upd_res.status_code == 200
    assert upd_res.json()["requirement_title"] == "Updated Requirement Title"
    assert upd_res.json()["maximum_budget"] == 850.0

    # Patch status to paused
    status_res = client.patch(
        f"/api/buyers/requirements/{req_id}/status",
        json={"requirement_status": "paused"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["requirement_status"] == "paused"

    # Soft delete / cancel
    del_res = client.delete(f"/api/buyers/requirements/{req_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"


def test_api_inventory_management(client):
    """Test setting and retrieving artisan inventory."""
    # Ensure PROD004 has catalog in database
    client.put(
        "/api/catalog/PROD004/approve",
        json={
            "product_id": "PROD004",
            "product_name": "Handmade Bamboo Basket",
            "product_title": "Handwoven Natural Brown Bamboo Storage Basket",
            "keywords": ["bamboo", "storage", "basket", "handwoven", "organizer"],
            "description": "Handcrafted eco-friendly bamboo basket designed for home storage.",
            "language": "en",
            "details": {
                "material": "bamboo",
                "color": "natural brown",
                "purpose": "storage",
                "craft_type": "handwoven",
            },
        },
    )

    payload = {
        "product_id": "PROD004",
        "artisan_id": "ARTISAN_ASSAM_01",
        "available_quantity": 40,
        "production_capacity_per_month": 120,
        "minimum_order_quantity": 5,
        "unit_price": 800.0,
        "currency": "INR",
        "production_lead_time_days": 10,
        "location": "Guwahati, Assam, India",
    }
    post_res = client.post("/api/market-linkage/inventory", json=payload)
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "success"

    # Retrieve inventory
    get_res = client.get("/api/market-linkage/inventory/PROD004")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["product_id"] == "PROD004"
    assert data["available_quantity"] == 40
    assert data["production_capacity_per_month"] == 120


def test_api_product_to_buyer_matches(client):
    """Test finding matching buyers for an artisan product."""
    # Ensure PROD004 has inventory and catalog (from existing fixtures)
    res = client.get("/api/market-linkage/product/PROD004/matches?min_score=30")
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == "PROD004"
    assert "matches" in data
    assert "total_matches" in data
    if data["matches"]:
        match = data["matches"][0]
        assert "match_score" in match
        assert "match_category" in match
        assert "compatibility" in match
        assert "score_breakdown" in match
        assert "buyer_summary" in match
        # Verify contact info is masked
        assert "contact_email_masked" in match["buyer_summary"]


def test_api_buyer_to_artisan_matches(client):
    """Test finding matching artisan products for a buyer requirement."""
    # Create an active requirement
    req_payload = {
        "buyer_id": "BUYER_DISCOVERY",
        "buyer_name": "Discovery Retailer",
        "buyer_type": "Wholesaler",
        "required_category": "storage",
        "requirement_title": "Bamboo Storage Basket Sourcing",
        "description": "Looking for handwoven natural bamboo storage baskets.",
        "preferred_materials": ["bamboo"],
        "required_quantity": 25,
        "minimum_budget": 500.0,
        "maximum_budget": 1200.0,
        "delivery_location": "Delhi",
        "delivery_deadline_days": 30,
        "requirement_status": "active",
    }
    create_res = client.post("/api/buyers/requirements", json=req_payload)
    req_id = create_res.json()["requirement_id"]

    res = client.get(f"/api/market-linkage/buyer/{req_id}/matches?min_score=30")
    assert res.status_code == 200
    data = res.json()
    assert data["requirement_id"] == req_id
    assert "matches" in data
    assert isinstance(data["matches"], list)


def test_api_unknown_product_or_requirement_returns_404(client):
    """Test 404 error responses for non-existent product or requirement."""
    res1 = client.get("/api/market-linkage/product/NON_EXISTENT_PROD_9999/matches")
    assert res1.status_code == 404

    res2 = client.get("/api/market-linkage/buyer/REQ-DOES-NOT-EXIST/matches")
    assert res2.status_code == 404

    res3 = client.get("/api/buyers/requirements/REQ-DOES-NOT-EXIST")
    assert res3.status_code == 404


def test_api_swagger_discovers_market_linkage_routes():
    """Verify OpenAPI documentation discovers all market linkage routes and schemas."""
    openapi = app.openapi()
    paths = openapi["paths"]

    assert "/api/buyers/requirements" in paths
    assert "/api/buyers/requirements/{requirement_id}" in paths
    assert "/api/buyers/requirements/{requirement_id}/status" in paths
    assert "/api/market-linkage/inventory" in paths
    assert "/api/market-linkage/inventory/{product_id}" in paths
    assert "/api/market-linkage/product/{product_id}/matches" in paths
    assert "/api/market-linkage/buyer/{requirement_id}/matches" in paths

    schemas = openapi["components"]["schemas"]
    assert "BuyerRequirementCreate" in schemas
    assert "BuyerRequirementResponse" in schemas
    assert "ArtisanInventory" in schemas
    assert "ProductMatchesResponse" in schemas
    assert "BuyerMatchesResponse" in schemas
    assert "ProductMatchResult" in schemas
