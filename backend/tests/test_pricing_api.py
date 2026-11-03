
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

from backend.app.main import app
from backend.app.schemas.pricing import PricingResponse
from backend.app.services.pricing_persistence import (
    _normalize_pricing_record,
    get_latest_pricing_record,
    get_pricing_records,
    save_pricing_record,
)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. API Endpoints & Backward Compatibility
# ---------------------------------------------------------------------------

def test_api_original_pricing_request(client):
    """Test 37: Original pricing request with exact legacy payload."""
    payload = {
        "product_id": "PROD004",
        "product_name": "Handmade Bamboo Basket",
        "material_cost": 300,
        "labor_cost": 200,
        "packaging_cost": 50,
        "overhead_cost": 50,
        "target_profit_margin_percent": 25,
    }
    response = client.post("/api/pricing/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == "PROD004"
    assert data["suggested_selling_price"] == 800.0
    assert data["total_cost"] == 600.0
    assert data["estimated_profit"] == 200.0
    assert data["estimated_profit_margin_percent"] == 25.0
    assert data["currency"] == "INR"
    assert data["pricing_method"] == "cost_plus_target_margin"
    assert data["record_id"] is not None


def test_api_full_extended_pricing_request(client):
    """Test full extended pricing request with commission, shipping, discount, taxes, and competitor data."""
    payload = {
        "product_id": "PROD_EXT_01",
        "product_name": "Embroidered Pashmina Shawl",
        "material_cost": 1200,
        "labor_cost": 800,
        "packaging_cost": 100,
        "overhead_cost": 100,
        "shipping_cost": 150,
        "other_variable_costs": 50,
        "target_profit_margin_percent": 20,
        "marketplace_commission_percent": 10,
        "discount_percent": 10,
        "tax_rate_percent": 12,
        "tax_inclusive": False,
        "pricing_strategy": "round_nearest_rupee",
        "competitor_prices": [
            {"price": 3200, "currency": "INR", "source": "Competitor A"},
            {"price": 3600, "currency": "INR", "source": "Competitor B"},
        ],
    }
    response = client.post("/api/pricing/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == "PROD_EXT_01"
    assert data["total_cost"] == 2400.0  # 1200 + 800 + 100 + 100 + 50 + 150
    assert data["cost_breakdown"] is not None
    assert data["fee_breakdown"] is not None
    assert data["fee_breakdown"]["marketplace_commission_percent"] == 10.0
    assert data["competitor_analysis"]["market_data_available"] is True
    assert data["competitor_analysis"]["observation_count"] == 2
    assert "explanation" in data
    assert len(data["explanation"]) > 0


def test_api_scenarios_endpoint(client):
    """Test POST /api/pricing/scenarios endpoint."""
    payload = {
        "product_id": "PROD_SCEN_01",
        "product_name": "Handmade Clay Pot",
        "material_cost": 200,
        "labor_cost": 150,
        "packaging_cost": 25,
        "overhead_cost": 25,
        "target_profit_margins": [15.0, 25.0, 35.0],
        "marketplace_commission_percent": 5.0,
    }
    response = client.post("/api/pricing/scenarios", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == "PROD_SCEN_01"
    assert len(data["scenarios"]) == 3
    assert data["scenarios"][0]["target_profit_margin_percent"] == 15.0
    assert data["scenarios"][1]["target_profit_margin_percent"] == 25.0
    assert data["scenarios"][2]["target_profit_margin_percent"] == 35.0
    assert data["cost_summary"]["total_seller_cost"] == 400.0


def test_api_get_pricing_history(client):
    """Test 31: GET /api/pricing/{product_id} returns history list."""
    response = client.get("/api/pricing/PROD004")
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == "PROD004"
    assert "total_records" in data
    assert "records" in data
    assert isinstance(data["records"], list)
    if data["records"]:
        # Verify newest record has expected fields
        latest = data["records"][0]
        assert "suggested_selling_price" in latest


def test_api_get_latest_pricing(client):
    """Test GET /api/pricing/{product_id}/latest endpoint."""
    response = client.get("/api/pricing/PROD004/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "PROD004"
    assert "suggested_selling_price" in data


def test_api_get_latest_unknown_product_returns_404(client):
    """Test 32: Unknown product ID on /latest returns 404."""
    response = client.get("/api/pricing/UNKNOWN_PROD_999999/latest")
    assert response.status_code == 404
    assert "No pricing records found" in response.json()["detail"]


def test_api_get_paginated_history(client):
    """Test GET /api/pricing/{product_id}/history endpoint."""
    response = client.get("/api/pricing/PROD004/history?limit=2&skip=0")
    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == "PROD004"
    assert data["limit"] == 2
    assert data["skip"] == 0
    assert len(data["records"]) <= 2


# ---------------------------------------------------------------------------
# 2. Schema Validation & Error Responses (4xx/5xx)
# ---------------------------------------------------------------------------

def test_api_invalid_input_returns_422(client):
    """Test 40: Validation error returns 422 Unprocessable Entity."""
    # Negative cost
    response = client.post(
        "/api/pricing/calculate",
        json={
            "product_id": "P1",
            "product_name": "Test",
            "material_cost": -100,
            "labor_cost": 200,
        },
    )
    assert response.status_code == 422

    # Impossible margin + commission (60% + 45% = 105%)
    response2 = client.post(
        "/api/pricing/calculate",
        json={
            "product_id": "P1",
            "product_name": "Test",
            "material_cost": 100,
            "labor_cost": 200,
            "target_profit_margin_percent": 60,
            "marketplace_commission_percent": 45,
        },
    )
    assert response2.status_code == 422


# ---------------------------------------------------------------------------
# 3. Persistence & Backward-Compatibility Unit Tests
# ---------------------------------------------------------------------------

def test_legacy_record_normalization():
    """Test 34: Legacy records from previous schema versions serialize safely."""
    legacy_doc = {
        "_id": "64b0f0000000000000000001",
        "product_id": "PROD_LEGACY",
        "product_name": "Old Basket",
        "material_cost": 300.0,
        "labor_cost": 200.0,
        "packaging_cost": 50.0,
        "overhead_cost": 50.0,
        "total_cost": 600.0,
        "target_profit_margin_percent": 25.0,
        "suggested_selling_price": 800.0,
        "estimated_profit": 200.0,
        "estimated_profit_margin_percent": 25.0,
        "currency": "INR",
        "created_at": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    }

    normalized = _normalize_pricing_record(legacy_doc)
    assert normalized["record_id"] == "64b0f0000000000000000001"
    assert normalized["shipping_cost"] == 0.0
    assert normalized["other_variable_costs"] == 0.0
    assert normalized["discounted_price"] is None
    assert normalized["pricing_strategy"] == "exact"
    assert normalized["warnings"] == []
    assert isinstance(normalized["created_at"], str)


def test_database_failure_simulation(client):
    """Test 35: Simulated database failure returns 500 and does NOT claim success."""
    with patch(
        "backend.app.services.pricing_persistence.database"
    ) as mock_db:
        mock_db.__getitem__.return_value.insert_one.side_effect = PyMongoError("DB connection dropped")

        response = client.post(
            "/api/pricing/calculate",
            json={
                "product_id": "PROD_FAIL_TEST",
                "product_name": "Test Item",
                "material_cost": 100,
                "labor_cost": 100,
            },
        )
        assert response.status_code == 500
        assert "Pricing calculation or database saving failed" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 4. OpenAPI & Swagger Discovery
# ---------------------------------------------------------------------------

def test_swagger_openapi_discovery():
    """Test 38: Swagger exposes all new fields and routes."""
    openapi = app.openapi()
    paths = openapi["paths"]

    assert "/api/pricing/calculate" in paths
    assert "/api/pricing/scenarios" in paths
    assert "/api/pricing/{product_id}/latest" in paths
    assert "/api/pricing/{product_id}/history" in paths
    assert "/api/pricing/{product_id}" in paths

    # Check schemas registered
    schemas = openapi["components"]["schemas"]
    assert "PricingRequest" in schemas
    assert "PricingResponse" in schemas
    assert "PricingScenarioRequest" in schemas
    assert "PricingScenarioResponse" in schemas
    assert "CostBreakdown" in schemas
    assert "FeeBreakdown" in schemas
    assert "CompetitorMarketAnalysis" in schemas

    # Check field descriptions in PricingRequest
    pricing_req_props = schemas["PricingRequest"]["properties"]
    assert "marketplace_commission_percent" in pricing_req_props
    assert "shipping_cost" in pricing_req_props
    assert "discount_percent" in pricing_req_props
    assert "competitor_prices" in pricing_req_props


# ---------------------------------------------------------------------------
# 5. Catalog and Image Endpoint Preservation
# ---------------------------------------------------------------------------

def test_catalog_and_image_routes_preserved(client):
    """Test 36: Existing catalog and image routes are preserved."""
    openapi = app.openapi()
    paths = openapi["paths"]

    assert "/api/catalog/generate" in paths
    assert "/api/catalog/{product_id}" in paths
    assert "/api/catalog/{product_id}/approve" in paths
    assert "/api/images/enhance" in paths
    assert "/api/images/product/{product_id}" in paths
    assert "/api/images/{image_id}/file" in paths

    # Root and health checks
    home_res = client.get("/")
    assert home_res.status_code == 200
    assert home_res.json()["project"] == "KarigarConnect"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert "status" in health_res.json()
