
from backend.app.schemas.pricing import PricingRequest
from backend.app.services.pricing_service import calculate_price


def main():
    request = PricingRequest(
        product_id="PROD004",
        product_name="Handmade Bamboo Basket",
        material_cost=300,
        labor_cost=200,
        packaging_cost=50,
        overhead_cost=50,
        target_profit_margin_percent=25,
    )

    result = calculate_price(request)

    print("PRICING RESULT:")
    print(result.model_dump_json(indent=2))

    assert result.total_cost == 600
    assert result.suggested_selling_price == 800
    assert result.estimated_profit == 200
    assert result.estimated_profit_margin_percent == 25

    print("\nSUCCESS: All pricing calculations passed.")


if __name__ == "__main__":
    main()
