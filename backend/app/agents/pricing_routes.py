
from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.pricing import (
    PricingRequest,
    PricingResponse,
    PricingScenarioRequest,
    PricingScenarioResponse,
)
from backend.app.services.pricing_persistence import (
    count_pricing_records,
    get_latest_pricing_record,
    get_pricing_records,
    save_pricing_record,
)
from backend.app.services.pricing_service import (
    calculate_price,
    calculate_scenarios,
)

router = APIRouter(
    prefix="/api/pricing",
    tags=["Dynamic Pricing"],
)


@router.post(
    "/calculate",
    response_model=PricingResponse,
    summary="Calculate selling price recommendation",
    description=(
        "Calculate an explainable selling price based on artisan direct costs, "
        "marketplace commission fees, shipping expenses, statutory taxes, and margin goals. "
        "Persists the resulting recommendation in MongoDB."
    ),
)
def calculate_product_pricing(request: PricingRequest):
    try:
        result = calculate_price(request)
        save_pricing_record(result)
        return result

    except ValueError as val_err:
        raise HTTPException(
            status_code=422,
            detail=str(val_err),
        ) from val_err

    except Exception as error:
        print(
            f"Pricing calculation or saving failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Pricing calculation or database saving failed. Check the backend terminal.",
        ) from error


@router.post(
    "/scenarios",
    response_model=PricingScenarioResponse,
    summary="Simulate multi-margin pricing scenarios",
    description=(
        "Simulate multiple target profit margin scenarios (e.g. 15%, 25%, 35%) "
        "against an identical artisan cost structure to compare price points."
    ),
)
def simulate_pricing_scenarios(request: PricingScenarioRequest):
    try:
        return calculate_scenarios(request)

    except ValueError as val_err:
        raise HTTPException(
            status_code=422,
            detail=str(val_err),
        ) from val_err

    except Exception as error:
        print(
            f"Pricing scenario calculation failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Pricing scenario calculation failed. Check the backend terminal.",
        ) from error


@router.get(
    "/{product_id}/latest",
    summary="Retrieve latest pricing recommendation",
    description="Retrieve the single most recent persisted pricing recommendation for a product ID.",
)
def get_latest_product_pricing(product_id: str):
    try:
        record = get_latest_pricing_record(product_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"No pricing records found for product ID '{product_id}'.",
            )
        return record

    except HTTPException:
        raise

    except Exception as error:
        print(
            f"Latest pricing retrieval failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Latest pricing retrieval failed. Check the backend terminal.",
        ) from error


@router.get(
    "/{product_id}/history",
    summary="Retrieve paginated pricing history",
    description="Retrieve paginated pricing calculation history for a product ID.",
)
def get_product_pricing_history_paginated(
    product_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return (1-100)"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
):
    try:
        total = count_pricing_records(product_id)
        records = get_pricing_records(product_id, limit=limit, skip=skip)

        return {
            "product_id": product_id,
            "total_records": total,
            "limit": limit,
            "skip": skip,
            "records": records,
        }

    except Exception as error:
        print(
            f"Pricing history retrieval failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Pricing history retrieval failed. Check the backend terminal.",
        ) from error


@router.get(
    "/{product_id}",
    summary="Retrieve all pricing history (backward-compatible)",
    description="Retrieve pricing calculation history for a product ID (newest first).",
)
def get_product_pricing_history(product_id: str):
    try:
        records = get_pricing_records(product_id)

        return {
            "product_id": product_id,
            "total_records": len(records),
            "records": records,
        }

    except Exception as error:
        print(
            f"Pricing history retrieval failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Pricing history retrieval failed. Check the backend terminal.",
        ) from error
