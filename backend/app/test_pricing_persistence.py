
from backend.app.schemas.pricing import PricingRequest
from backend.app.services.pricing_service import calculate_price
from backend.app.services.pricing_persistence import (
    save_pricing_record,
    get_pricing_records,
)


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

    print("Saving pricing record...")
    saved = save_pricing_record(result)
    print("SAVE RESULT:", saved)

    print("\nRetrieving pricing records...")
    records = get_pricing_records("PROD004")
    print("RECORD COUNT:", len(records))
    print("RECORDS:", records)

    if not records:
        raise RuntimeError("Pricing record was not found after saving.")

    print("\nSUCCESS: Pricing persistence verified.")


if __name__ == "__main__":
    main()
