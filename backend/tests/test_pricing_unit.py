
import pytest
from pydantic import ValidationError

from backend.app.schemas.pricing import (
    CompetitorObservation,
    PricingRequest,
    PricingScenarioRequest,
)
from backend.app.services.pricing_service import (
    analyze_competitors,
    calculate_price,
    calculate_scenarios,
)


# ---------------------------------------------------------------------------
# 1. Basic Calculation Tests
# ---------------------------------------------------------------------------

def test_basic_pricing_calculation():
    """Test 1 & 2: Base production costs and 25% profit margin."""
    req = PricingRequest(
        product_id="PROD004",
        product_name="Handmade Bamboo Basket",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
    )
    res = calculate_price(req)

    assert res.total_cost == 600.0
    assert res.suggested_selling_price == 800.0
    assert res.estimated_profit == 200.0
    assert res.estimated_profit_margin_percent == 25.0
    assert res.currency == "INR"
    assert res.cost_breakdown.base_production_cost == 600.0
    assert res.cost_breakdown.total_seller_cost == 600.0


# ---------------------------------------------------------------------------
# 2. Input Validation Tests
# ---------------------------------------------------------------------------

def test_reject_negative_material_cost():
    """Test 3: Reject negative material cost."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=-10.0,
            labor_cost=100.0,
        )


def test_reject_negative_labor_cost():
    """Test 4: Reject negative labor cost."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=-50.0,
        )


def test_reject_negative_packaging_cost():
    """Test 5: Reject negative packaging cost."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            packaging_cost=-5.0,
        )


def test_reject_negative_overhead():
    """Test 6: Reject negative overhead."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            overhead_cost=-20.0,
        )


def test_reject_negative_target_margin():
    """Test 7: Reject negative target margin."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            target_profit_margin_percent=-10.0,
        )


def test_reject_zero_target_margin():
    """Test 8: Reject zero target margin."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            target_profit_margin_percent=0.0,
        )


def test_reject_margin_at_or_above_100():
    """Test 9: Reject margin >= 100%."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            target_profit_margin_percent=100.0,
        )
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            target_profit_margin_percent=105.0,
        )


def test_upper_bounds_monetary_inputs():
    """Test 10: Reject inputs > 10,000,000 INR."""
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=10_000_001.0,
            labor_cost=100.0,
        )


def test_missing_required_fields_and_types():
    """Test 11: Missing required fields and bad types."""
    with pytest.raises(ValidationError):
        PricingRequest(product_id="P1")  # missing product_name, material_cost, labor_cost

    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost="not-a-number",
            labor_cost=100.0,
        )


# ---------------------------------------------------------------------------
# 3. Additional Expenses & Fees
# ---------------------------------------------------------------------------

def test_marketplace_commission():
    """Test 12: Nonzero marketplace commission."""
    # Cost = 600. Commission = 10%, Target margin = 25%
    # Price = 600 / (1 - 0.10 - 0.25) = 600 / 0.65 = 923.08
    # Comm amount = 92.31. Net = 830.77. Profit = 230.77. Margin = 230.77 / 923.08 = 25.00%
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
        marketplace_commission_percent=10.0,
    )
    res = calculate_price(req)
    assert res.suggested_selling_price == 923.08
    assert res.fee_breakdown.marketplace_commission_amount == 92.31
    assert abs(res.estimated_profit_margin_percent - 25.0) <= 0.02


def test_shipping_expense():
    """Test 13: Shipping costs included in seller cost."""
    # Production cost = 600, shipping = 100 => Total cost = 700
    # Price at 25% margin = 700 / 0.75 = 933.33
    # Profit = 933.33 - 700 = 233.33. Margin = 233.33 / 933.33 = 25.00%
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        shipping_cost=100.0,
        target_profit_margin_percent=25.0,
    )
    res = calculate_price(req)
    assert res.total_cost == 700.0
    assert res.suggested_selling_price == 933.33
    assert res.estimated_profit == 233.33
    assert abs(res.estimated_profit_margin_percent - 25.0) <= 0.01


def test_other_variable_costs():
    """Test 14: Additional variable costs included."""
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        other_variable_costs=50.0,
        target_profit_margin_percent=25.0,
    )
    res = calculate_price(req)
    assert res.cost_breakdown.other_variable_costs == 50.0
    assert res.total_cost == 550.0
    assert res.suggested_selling_price == round(550.0 / 0.75, 2)


def test_commission_and_shipping_combination():
    """Test 15: Combination of commission and shipping."""
    # Cost = 600 + 80 shipping = 680
    # Comm = 15%, margin = 20% => Denominator = 1 - 0.15 - 0.20 = 0.65
    # Price = 680 / 0.65 = 1046.15
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=300.0,
        shipping_cost=80.0,
        target_profit_margin_percent=20.0,
        marketplace_commission_percent=15.0,
    )
    res = calculate_price(req)
    assert res.total_cost == 680.0
    assert res.suggested_selling_price == 1046.15
    assert abs(res.estimated_profit_margin_percent - 20.0) <= 0.05


def test_discount_pricing():
    """Test 16: Promotional discount configuration."""
    # Total cost = 600, margin = 25% => Required transaction price = 800
    # Discount = 20% => Listing price = 800 / (1 - 0.20) = 1000
    # Discounted transaction price = 1000 * 0.80 = 800
    # Profit = 800 - 600 = 200 => Margin = 200 / 800 = 25%
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
        discount_percent=20.0,
    )
    res = calculate_price(req)
    assert res.suggested_selling_price == 1000.0
    assert res.discounted_price == 800.0
    assert res.fee_breakdown.discount_amount == 200.0
    assert res.estimated_profit == 200.0
    assert res.estimated_profit_margin_percent == 25.0


def test_tax_calculations_inclusive_and_exclusive():
    """Test 17: Statutory tax handling (both exclusive and inclusive)."""
    # Exclusive: 18% GST added to selling price
    req_exclusive = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
        tax_rate_percent=18.0,
        tax_inclusive=False,
    )
    res_ex = calculate_price(req_exclusive)
    assert res_ex.suggested_selling_price == 800.0
    assert res_ex.fee_breakdown.tax_amount == 144.0  # 800 * 0.18

    # Inclusive: Selling price 800 includes 18% GST
    req_inclusive = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
        tax_rate_percent=18.0,
        tax_inclusive=True,
    )
    res_in = calculate_price(req_inclusive)
    assert res_in.suggested_selling_price == 800.0
    # pre-tax = 800 / 1.18 = 677.966 => tax = 122.03
    assert res_in.fee_breakdown.tax_amount == 122.03


# ---------------------------------------------------------------------------
# 4. Profitability & Boundary Conditions
# ---------------------------------------------------------------------------

def test_profitability_guarantee():
    """Test 18: Guarantee target margin is achieved."""
    for margin in [10.0, 20.0, 30.0, 45.0]:
        req = PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=150.0,
            labor_cost=100.0,
            target_profit_margin_percent=margin,
            marketplace_commission_percent=5.0,
        )
        res = calculate_price(req)
        assert res.estimated_profit_margin_percent >= (margin - 0.05)


def test_impossible_pricing_configurations_rejected():
    """Test 19: Reject configurations where deductions >= 100%."""
    # Commission 25% + Target Margin 75% = 100%
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            target_profit_margin_percent=75.0,
            marketplace_commission_percent=25.0,
        )

    # Commission 30% + Target Margin 80% = 110%
    with pytest.raises(ValidationError):
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=100.0,
            labor_cost=100.0,
            target_profit_margin_percent=80.0,
            marketplace_commission_percent=30.0,
        )


def test_rounding_strategies_do_not_violate_margin():
    """Test 20: Rounding strategies guarantee actual margin >= target margin."""
    # Required price for cost 600 at 25% is 800.00
    req_rupee = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
        pricing_strategy="round_nearest_rupee",
    )
    res_rupee = calculate_price(req_rupee)
    assert res_rupee.suggested_selling_price == 800.0
    assert res_rupee.estimated_profit_margin_percent >= 25.0

    # Test psychological 99 rounding
    # Cost = 600, margin 25% => required = 800.00
    # Next 99 candidate is 899.00
    req_99 = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
        pricing_strategy="psychological_99",
    )
    res_99 = calculate_price(req_99)
    assert res_99.suggested_selling_price == 899.0
    # Profit = 899 - 600 = 299 => margin = 299 / 899 = 33.26% >= 25.0%
    assert res_99.estimated_profit_margin_percent >= 25.0


def test_zero_cost_input():
    """Test 21: Zero-cost edge case."""
    req = PricingRequest(
        product_id="P_ZERO",
        product_name="Free Sample",
        material_cost=0.0,
        labor_cost=0.0,
        packaging_cost=0.0,
        overhead_cost=0.0,
        target_profit_margin_percent=25.0,
    )
    res = calculate_price(req)
    assert res.total_cost == 0.0
    assert res.suggested_selling_price == 0.0
    assert res.estimated_profit == 0.0
    assert res.estimated_profit_margin_percent == 0.0


def test_small_and_large_amounts():
    """Test 22: Small amounts (e.g. ₹0.50) and large amounts (e.g. ₹5,000,000)."""
    # Small
    req_small = PricingRequest(
        product_id="P_SMALL",
        product_name="Small Item",
        material_cost=0.50,
        labor_cost=0.50,
        target_profit_margin_percent=50.0,
    )
    res_small = calculate_price(req_small)
    assert res_small.total_cost == 1.0
    assert res_small.suggested_selling_price == 2.0
    assert res_small.estimated_profit == 1.0

    # Large
    req_large = PricingRequest(
        product_id="P_LARGE",
        product_name="Exquisite Silk Tapestry",
        material_cost=2_000_000.0,
        labor_cost=1_000_000.0,
        target_profit_margin_percent=25.0,
    )
    res_large = calculate_price(req_large)
    assert res_large.total_cost == 3_000_000.0
    assert res_large.suggested_selling_price == 4_000_000.0
    assert res_large.estimated_profit == 1_000_000.0


# ---------------------------------------------------------------------------
# 5. Competitor Comparison Tests
# ---------------------------------------------------------------------------

def test_no_competitor_data():
    """Test 23: No competitor data provided."""
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        competitor_prices=None,
    )
    res = calculate_price(req)
    assert res.competitor_analysis is not None
    assert res.competitor_analysis.market_data_available is False
    assert res.competitor_analysis.observation_count == 0


def test_single_competitor_observation():
    """Test 24: Single competitor observation."""
    obs = [
        CompetitorObservation(
            price=850.0,
            currency="INR",
            source="FabIndia",
            is_verified=True,
        )
    ]
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,  # Price = 800
        competitor_prices=obs,
    )
    res = calculate_price(req)
    assert res.competitor_analysis.market_data_available is True
    assert res.competitor_analysis.observation_count == 1
    assert res.competitor_analysis.min_price == 850.0
    assert res.competitor_analysis.max_price == 850.0
    assert res.competitor_analysis.median_price == 850.0
    # 800 is within 5% of 850 (850 * 0.95 = 807.5 => 800 < 807.5 => below median)
    assert res.competitor_analysis.price_position == "below_competitor_median"


def test_several_competitor_observations():
    """Test 25: Multiple competitor observations with median calculation."""
    obs = [
        CompetitorObservation(price=700.0, currency="INR"),
        CompetitorObservation(price=900.0, currency="INR"),
        CompetitorObservation(price=800.0, currency="INR"),
        CompetitorObservation(price=1000.0, currency="INR"),
    ]
    # Sorted: 700, 800, 900, 1000 => Median = (800 + 900) / 2 = 850
    analysis, _ = analyze_competitors(obs, recommended_price=850.0, total_cost=600.0)
    assert analysis.market_data_available is True
    assert analysis.observation_count == 4
    assert analysis.min_price == 700.0
    assert analysis.max_price == 1000.0
    assert analysis.median_price == 850.0
    assert analysis.price_position == "near_competitor_median"


def test_reject_invalid_or_negative_competitor_price():
    """Test 26: Negative or zero competitor price rejected."""
    with pytest.raises(ValidationError):
        CompetitorObservation(price=-50.0, currency="INR")

    with pytest.raises(ValidationError):
        CompetitorObservation(price=0.0, currency="INR")


def test_reject_mixed_currencies():
    """Test 27: Mixed currencies rejected."""
    with pytest.raises(ValidationError) as exc_info:
        PricingRequest(
            product_id="P1",
            product_name="Test",
            material_cost=300.0,
            labor_cost=200.0,
            currency="INR",
            competitor_prices=[
                CompetitorObservation(price=15.0, currency="USD"),
            ],
        )
    assert "currency 'USD' does not match request currency 'INR'" in str(exc_info.value)


def test_competitor_all_below_minimum_profitable_price():
    """Test 29: Warning triggered when competitor median is below direct cost."""
    obs = [
        CompetitorObservation(price=400.0, currency="INR"),
        CompetitorObservation(price=450.0, currency="INR"),
    ]
    # Total cost = 600, median = 425 => Warning
    req = PricingRequest(
        product_id="P1",
        product_name="Test",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margin_percent=25.0,
        competitor_prices=obs,
    )
    res = calculate_price(req)
    assert any("below your direct production cost" in w for w in res.warnings)


# ---------------------------------------------------------------------------
# 6. Multi-margin Scenarios
# ---------------------------------------------------------------------------

def test_pricing_scenarios_evaluation():
    """Test scenarios service across multiple target margins."""
    scenario_req = PricingScenarioRequest(
        product_id="PROD004",
        product_name="Handmade Bamboo Basket",
        material_cost=300.0,
        labor_cost=200.0,
        packaging_cost=50.0,
        overhead_cost=50.0,
        target_profit_margins=[15.0, 25.0, 35.0],
        marketplace_commission_percent=5.0,
    )
    scenario_res = calculate_scenarios(scenario_req)

    assert len(scenario_res.scenarios) == 3
    # Check scenario 1: 15% margin
    s1 = scenario_res.scenarios[0]
    assert s1.target_profit_margin_percent == 15.0
    assert s1.meets_target_margin is True

    # Check scenario 2: 25% margin
    s2 = scenario_res.scenarios[1]
    assert s2.target_profit_margin_percent == 25.0
    assert s2.meets_target_margin is True

    # Check scenario 3: 35% margin
    s3 = scenario_res.scenarios[2]
    assert s3.target_profit_margin_percent == 35.0
    assert s3.meets_target_margin is True

    # Price must strictly increase as target margin increases
    assert s1.suggested_selling_price < s2.suggested_selling_price < s3.suggested_selling_price
