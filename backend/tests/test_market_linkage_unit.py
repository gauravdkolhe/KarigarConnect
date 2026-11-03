import pytest
from pydantic import ValidationError

from backend.app.schemas.market_linkage import (
    ArtisanProductProfile,
    BuyerRequirementCreate,
    BuyerRequirementUpdate,
)
from backend.app.services.matching_service import evaluate_match


# ---------------------------------------------------------------------------
# 1. Buyer Requirement Validation Tests
# ---------------------------------------------------------------------------

def test_create_valid_buyer_requirement():
    """Test 1: Valid buyer requirement creation."""
    req = BuyerRequirementCreate(
        buyer_id="BUYER_101",
        buyer_name="FabIndia Sourcing Dept",
        buyer_type="Retailer",
        required_category="Storage",
        requirement_title="Handwoven Bamboo Baskets for Home Storage",
        description="Looking for sturdy natural bamboo baskets for retail gift packaging.",
        required_keywords=["bamboo", "storage", "basket", "handwoven"],
        preferred_materials=["bamboo", "cane"],
        preferred_craft_types=["handwoven", "basketry"],
        required_quantity=200,
        minimum_budget=500.0,
        maximum_budget=900.0,
        currency="INR",
        delivery_location="Delhi, India",
        delivery_deadline_days=45,
        contact_email="sourcing@fabindia.example.com",
        contact_phone="+91-9876543210",
        requirement_status="active",
    )
    assert req.buyer_name == "FabIndia Sourcing Dept"
    assert req.maximum_budget == 900.0


def test_reject_empty_buyer_name():
    """Test 2: Reject empty buyer name."""
    with pytest.raises(ValidationError):
        BuyerRequirementCreate(
            buyer_id="B1",
            buyer_name="",
            buyer_type="Retailer",
            required_category="Storage",
            requirement_title="Title",
            description="Detailed specifications for the item required.",
            required_quantity=10,
            maximum_budget=500.0,
            delivery_location="Mumbai",
        )


def test_reject_negative_quantity():
    """Test 3: Reject negative or zero quantity."""
    with pytest.raises(ValidationError):
        BuyerRequirementCreate(
            buyer_id="B1",
            buyer_name="Buyer",
            buyer_type="Retailer",
            required_category="Storage",
            requirement_title="Title",
            description="Detailed specifications for the item required.",
            required_quantity=-5,
            maximum_budget=500.0,
            delivery_location="Mumbai",
        )

    with pytest.raises(ValidationError):
        BuyerRequirementCreate(
            buyer_id="B1",
            buyer_name="Buyer",
            buyer_type="Retailer",
            required_category="Storage",
            requirement_title="Title",
            description="Detailed specifications for the item required.",
            required_quantity=0,
            maximum_budget=500.0,
            delivery_location="Mumbai",
        )


def test_reject_invalid_price_range():
    """Test 4: Reject max_budget < min_budget."""
    with pytest.raises(ValidationError):
        BuyerRequirementCreate(
            buyer_id="B1",
            buyer_name="Buyer",
            buyer_type="Retailer",
            required_category="Storage",
            requirement_title="Title",
            description="Detailed specifications for the item required.",
            required_quantity=10,
            minimum_budget=800.0,
            maximum_budget=500.0,  # Max < Min
            delivery_location="Mumbai",
        )


def test_reject_invalid_email_format():
    """Test 5: Reject malformed email formats."""
    with pytest.raises(ValidationError):
        BuyerRequirementCreate(
            buyer_id="B1",
            buyer_name="Buyer",
            buyer_type="Retailer",
            required_category="Storage",
            requirement_title="Title",
            description="Detailed specifications for the item required.",
            required_quantity=10,
            maximum_budget=500.0,
            delivery_location="Mumbai",
            contact_email="not-an-email",
        )


# ---------------------------------------------------------------------------
# 2. Matching Engine Dimension Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_product():
    return ArtisanProductProfile(
        product_id="PROD004",
        artisan_id="ART_001",
        product_name="Handmade Bamboo Basket",
        product_title="Handwoven Natural Brown Bamboo Storage Basket",
        category="Storage",
        description="Traditional handcrafted storage basket made from Assam bamboo.",
        keywords=["bamboo", "storage", "handwoven", "basket", "organizer"],
        material="bamboo",
        craft_type="handwoven",
        color="natural brown",
        available_quantity=50,
        production_capacity=100,
        minimum_order_quantity=5,
        unit_price=800.0,
        currency="INR",
        production_lead_time_days=14,
        location="Guwahati, Assam, India",
        product_status="available",
    )


def test_exact_category_match(sample_product):
    """Test 11: Exact category match gets full category score."""
    req = {
        "requirement_id": "REQ_01",
        "buyer_id": "B1",
        "buyer_name": "Delhi Retail",
        "buyer_type": "Retailer",
        "required_category": "Storage",
        "requirement_title": "Storage Baskets Needed",
        "description": "Looking for storage items.",
        "preferred_materials": ["bamboo"],
        "preferred_craft_types": ["handwoven"],
        "required_quantity": 40,
        "minimum_budget": 700.0,
        "maximum_budget": 1000.0,
        "currency": "INR",
        "delivery_location": "Delhi, India",
        "delivery_deadline_days": 30,
    }
    res = evaluate_match(sample_product, req)
    assert res.score_breakdown.category_score == 20.0
    assert res.compatibility.category is True


def test_keyword_overlap(sample_product):
    """Test 12: Keyword and text similarity calculation."""
    req = {
        "requirement_id": "REQ_02",
        "buyer_name": "Eco Stores",
        "required_category": "Storage",
        "requirement_title": "Handmade bamboo organizer basket",
        "description": "Eco friendly organizer basket handwoven from bamboo.",
        "required_keywords": ["organizer", "bamboo", "handwoven"],
        "preferred_materials": ["bamboo"],
        "required_quantity": 20,
        "maximum_budget": 900.0,
        "currency": "INR",
        "delivery_location": "India",
        "delivery_deadline_days": 20,
    }
    res = evaluate_match(sample_product, req)
    assert res.score_breakdown.keyword_score > 10.0


def test_material_compatibility(sample_product):
    """Test 13: Material matching and mismatch handling."""
    # Match
    req_match = {
        "required_category": "Storage",
        "preferred_materials": ["cane", "bamboo", "wood"],
        "maximum_budget": 900.0,
        "required_quantity": 10,
    }
    res_m = evaluate_match(sample_product, req_match)
    assert res_m.score_breakdown.material_score == 15.0
    assert res_m.compatibility.material is True

    # Mismatch
    req_diff = {
        "required_category": "Storage",
        "preferred_materials": ["brass", "copper"],
        "maximum_budget": 900.0,
        "required_quantity": 10,
    }
    res_d = evaluate_match(sample_product, req_diff)
    assert res_d.score_breakdown.material_score == 0.0
    assert res_d.compatibility.material is False


def test_craft_type_compatibility(sample_product):
    """Test 14: Craft type alignment."""
    req_craft = {
        "required_category": "Storage",
        "preferred_craft_types": ["handwoven", "basketry"],
        "maximum_budget": 900.0,
        "required_quantity": 10,
    }
    res = evaluate_match(sample_product, req_craft)
    assert res.score_breakdown.craft_type_score == 10.0
    assert res.compatibility.craft_type is True


def test_budget_compatibility_and_mismatch(sample_product):
    """Test 15 & 16: Budget compatibility sweet spot vs hard mismatch."""
    # Sweet spot: unit_price 800 within [600, 1000]
    req_sweet = {
        "required_category": "Storage",
        "minimum_budget": 600.0,
        "maximum_budget": 1000.0,
        "currency": "INR",
        "required_quantity": 10,
    }
    res_sweet = evaluate_match(sample_product, req_sweet)
    assert res_sweet.score_breakdown.price_score == 15.0
    assert res_sweet.compatibility.budget is True

    # Hard mismatch: buyer max_budget is 500 (artisan is 800)
    req_mismatch = {
        "required_category": "Storage",
        "minimum_budget": 300.0,
        "maximum_budget": 500.0,
        "currency": "INR",
        "required_quantity": 10,
    }
    res_mis = evaluate_match(sample_product, req_mismatch)
    assert res_mis.score_breakdown.price_score == 0.0
    assert res_mis.compatibility.budget is False
    assert res_mis.match_category == "Not eligible"
    assert any("Budget mismatch" in w for w in res_mis.warnings)


def test_quantity_in_stock_vs_conditional_vs_shortfall(sample_product):
    """Test 17, 18, 19: Quantity in stock (10 pts), conditional over time (7 pts), and shortfall (0 pts)."""
    # Case 1: In stock (available: 50, needed: 30)
    req_stock = {
        "required_category": "Storage",
        "required_quantity": 30,
        "maximum_budget": 900.0,
        "currency": "INR",
        "delivery_deadline_days": 30,
    }
    res_stock = evaluate_match(sample_product, req_stock)
    assert res_stock.score_breakdown.quantity_score == 10.0
    assert res_stock.compatibility.quantity is True

    # Case 2: Conditional on production (available: 50, capacity: 100/mo, needed: 120, deadline: 30 days)
    req_cond = {
        "required_category": "Storage",
        "required_quantity": 120,
        "maximum_budget": 900.0,
        "currency": "INR",
        "delivery_deadline_days": 30,
    }
    res_cond = evaluate_match(sample_product, req_cond)
    assert res_cond.score_breakdown.quantity_score == 7.0
    assert res_cond.compatibility.quantity is True
    assert any("Quantity condition" in w for w in res_cond.warnings)

    # Case 3: Shortfall (needed: 500 units in 30 days, can only do ~150)
    req_short = {
        "required_category": "Storage",
        "required_quantity": 500,
        "maximum_budget": 900.0,
        "currency": "INR",
        "delivery_deadline_days": 30,
    }
    res_short = evaluate_match(sample_product, req_short)
    assert res_short.score_breakdown.quantity_score == 0.0
    assert res_short.compatibility.quantity is False
    assert any("Capacity shortfall" in w for w in res_short.warnings)


def test_delivery_deadline_feasibility(sample_product):
    """Test 20: Delivery deadline vs lead time."""
    # Feasible: lead time is 14 days, deadline is 21 days
    req_feasible = {
        "required_category": "Storage",
        "required_quantity": 100,  # exceeds ready stock of 50
        "maximum_budget": 900.0,
        "delivery_deadline_days": 21,
    }
    res_f = evaluate_match(sample_product, req_feasible)
    assert res_f.score_breakdown.delivery_score == 5.0
    assert res_f.compatibility.delivery is True

    # Infeasible: lead time is 14 days, deadline is 5 days
    req_infeasible = {
        "required_category": "Storage",
        "required_quantity": 100,
        "maximum_budget": 900.0,
        "delivery_deadline_days": 5,
    }
    res_inf = evaluate_match(sample_product, req_infeasible)
    assert res_inf.score_breakdown.delivery_score == 0.0
    assert res_inf.compatibility.delivery is False
    assert any("Delivery infeasible" in w for w in res_inf.warnings)


def test_currency_mismatch(sample_product):
    """Test 22: Currency mismatch results in zero budget score and ineligibility."""
    req_usd = {
        "required_category": "Storage",
        "currency": "USD",
        "minimum_budget": 10.0,
        "maximum_budget": 20.0,
        "required_quantity": 10,
    }
    res = evaluate_match(sample_product, req_usd)
    assert res.score_breakdown.price_score == 0.0
    assert res.compatibility.budget is False
    assert res.match_category == "Not eligible"
    assert any("Currency mismatch" in w for w in res.warnings)


def test_match_categorization_hierarchy(sample_product):
    """Test 25, 26, 27, 28: Categorization into Excellent, Good, Conditional, Not eligible."""
    # Excellent match
    req_excellent = {
        "required_category": "Storage",
        "requirement_title": "Natural Handwoven Bamboo Baskets",
        "description": "High quality storage baskets made from natural bamboo.",
        "required_keywords": ["bamboo", "storage", "handwoven", "basket"],
        "preferred_materials": ["bamboo"],
        "preferred_craft_types": ["handwoven"],
        "required_quantity": 30,
        "minimum_budget": 750.0,
        "maximum_budget": 1000.0,
        "currency": "INR",
        "delivery_location": "Delhi, India",
        "delivery_deadline_days": 30,
    }
    res_ex = evaluate_match(sample_product, req_excellent)
    assert res_ex.match_score >= 80.0
    assert res_ex.match_category == "Excellent"

    # Conditional match due to slight budget stretch
    req_cond = {
        "required_category": "Storage",
        "requirement_title": "Storage Baskets",
        "description": "Storage baskets for household use.",
        "preferred_materials": ["bamboo"],
        "required_quantity": 30,
        "minimum_budget": 600.0,
        "maximum_budget": 750.0,  # Artisan is 800 (within 10% stretch: 800 vs 750)
        "currency": "INR",
        "delivery_location": "India",
        "delivery_deadline_days": 30,
    }
    res_c = evaluate_match(sample_product, req_cond)
    assert res_c.match_category == "Conditional"
