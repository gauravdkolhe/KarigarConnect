from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.market_linkage import (
    ArtisanInventory,
    BuyerMatchesResponse,
    BuyerRequirementCreate,
    BuyerRequirementResponse,
    BuyerRequirementStatusUpdate,
    BuyerRequirementUpdate,
    ProductMatchResult,
    ProductMatchesResponse,
)
from backend.app.services.buyer_service import (
    create_buyer_requirement,
    delete_or_archive_requirement,
    get_buyer_requirement,
    list_buyer_requirements,
    update_buyer_requirement,
    update_requirement_status,
)
from backend.app.services.inventory_service import (
    get_artisan_inventory,
    save_artisan_inventory,
)
from backend.app.services.matching_service import (
    find_matches_for_buyer,
    find_matches_for_product,
)

router = APIRouter(
    tags=["Market Linkage"],
)


# =====================================================================
# 1. Buyer Requirement Management Endpoints
# =====================================================================

@router.post(
    "/api/buyers/requirements",
    response_model=BuyerRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a genuine buyer requirement",
    description="Registers a new sourcing requirement from a verified wholesaler, retailer, or business buyer.",
)
def create_requirement(request: BuyerRequirementCreate):
    try:
        created = create_buyer_requirement(request)
        return created
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err)) from val_err
    except Exception as error:
        print(f"Error creating buyer requirement: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create buyer requirement. Check the backend terminal.",
        ) from error


@router.get(
    "/api/buyers/requirements",
    summary="List buyer requirements",
    description="List active sourcing requirements with optional category, status, and buyer type filters.",
)
def list_requirements(
    status: str | None = Query(default="active", description="Filter by status ('active', 'draft', 'paused', 'all')"),
    category: str | None = Query(default=None, description="Filter by product category"),
    buyer_type: str | None = Query(default=None, description="Filter by buyer entity type"),
    limit: int = Query(default=20, ge=1, le=100, description="Records per page"),
    skip: int = Query(default=0, ge=0, description="Records to skip"),
):
    try:
        records, total = list_buyer_requirements(
            status=status,
            category=category,
            buyer_type=buyer_type,
            limit=limit,
            skip=skip,
            mask_contact=True,  # Always mask contact info in public listings
        )
        return {
            "total_records": total,
            "limit": limit,
            "skip": skip,
            "requirements": records,
        }
    except Exception as error:
        print(f"Error listing buyer requirements: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list buyer requirements.",
        ) from error


@router.get(
    "/api/buyers/requirements/{requirement_id}",
    response_model=BuyerRequirementResponse,
    summary="Retrieve a buyer requirement",
    description="Fetch single buyer requirement by ID. Contact information is masked unless authorized.",
)
def get_requirement(
    requirement_id: str,
    authorized: bool = Query(default=False, description="Set True for authorized artisan/buyer to view full contact info"),
):
    try:
        record = get_buyer_requirement(requirement_id, mask_contact=not authorized)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Buyer requirement '{requirement_id}' not found.",
            )
        return record
    except HTTPException:
        raise
    except Exception as error:
        print(f"Error retrieving requirement {requirement_id}: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve requirement.",
        ) from error


@router.put(
    "/api/buyers/requirements/{requirement_id}",
    response_model=BuyerRequirementResponse,
    summary="Update a buyer requirement",
    description="Update specification fields of an existing buyer requirement.",
)
def update_requirement(
    requirement_id: str,
    request: BuyerRequirementUpdate,
):
    try:
        updated = update_buyer_requirement(requirement_id, request, mask_contact=False)
        if updated is None:
            raise HTTPException(
                status_code=404,
                detail=f"Buyer requirement '{requirement_id}' not found.",
            )
        return updated
    except HTTPException:
        raise
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err)) from val_err
    except Exception as error:
        print(f"Error updating requirement {requirement_id}: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update buyer requirement.",
        ) from error


@router.patch(
    "/api/buyers/requirements/{requirement_id}/status",
    response_model=BuyerRequirementResponse,
    summary="Update buyer requirement status",
    description="Change status (draft, active, paused, fulfilled, expired, cancelled).",
)
def change_requirement_status(
    requirement_id: str,
    request: BuyerRequirementStatusUpdate,
):
    try:
        updated = update_requirement_status(
            requirement_id,
            request.requirement_status,
            mask_contact=False,
        )
        if updated is None:
            raise HTTPException(
                status_code=404,
                detail=f"Buyer requirement '{requirement_id}' not found.",
            )
        return updated
    except HTTPException:
        raise
    except Exception as error:
        print(f"Error changing status for {requirement_id}: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update status.",
        ) from error


@router.delete(
    "/api/buyers/requirements/{requirement_id}",
    summary="Delete or archive buyer requirement",
    description="Marks requirement status as cancelled (soft delete) by default.",
)
def remove_requirement(
    requirement_id: str,
    hard_delete: bool = Query(default=False, description="Permanently delete from database if true"),
):
    try:
        success = delete_or_archive_requirement(requirement_id, hard_delete=hard_delete)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Buyer requirement '{requirement_id}' not found.",
            )
        action = "permanently deleted" if hard_delete else "archived / cancelled"
        return {
            "requirement_id": requirement_id,
            "status": "success",
            "message": f"Buyer requirement successfully {action}.",
        }
    except HTTPException:
        raise
    except Exception as error:
        print(f"Error deleting requirement {requirement_id}: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete requirement.",
        ) from error


# =====================================================================
# 2. Artisan Inventory & Capacity Management
# =====================================================================

@router.post(
    "/api/market-linkage/inventory",
    summary="Set artisan inventory and production capacity",
    description="Registers operational capacity, ready stock, and lead times for an artisan product.",
)
def update_inventory(request: ArtisanInventory):
    try:
        result = save_artisan_inventory(request)
        return {
            "status": "success",
            "message": "Artisan inventory and capacity updated successfully.",
            "inventory": result,
        }
    except Exception as error:
        print(f"Error saving inventory: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save artisan inventory.",
        ) from error


@router.get(
    "/api/market-linkage/inventory/{product_id}",
    summary="Retrieve artisan inventory and capacity",
    description="Fetches current inventory and production capacity parameters for a product.",
)
def get_inventory(product_id: str):
    try:
        inv = get_artisan_inventory(product_id)
        if inv is None:
            raise HTTPException(
                status_code=404,
                detail=f"No operational inventory record found for product '{product_id}'.",
            )
        return inv
    except HTTPException:
        raise
    except Exception as error:
        print(f"Error retrieving inventory: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve inventory.",
        ) from error


# =====================================================================
# 3. Market Linkage Matching Endpoints
# =====================================================================

@router.get(
    "/api/market-linkage/product/{product_id}/matches",
    response_model=ProductMatchesResponse,
    summary="Find matching buyers for an artisan product",
    description="Evaluates all active genuine buyer requirements in MongoDB against the artisan's product catalog and pricing.",
)
def get_matches_for_artisan_product(
    product_id: str,
    min_score: float = Query(default=40.0, ge=0.0, le=100.0, description="Minimum match score threshold (0-100)"),
    max_results: int = Query(default=20, ge=1, le=100, description="Maximum number of matches to return"),
    status: str = Query(default="active", description="Requirement status to consider"),
    category: str | None = Query(default=None, description="Optional category filter"),
):
    try:
        results = find_matches_for_product(
            product_id=product_id,
            min_score=min_score,
            max_results=max_results,
            status=status,
            category_filter=category,
        )
        return results
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err)) from val_err
    except Exception as error:
        print(f"Error matching product {product_id}: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to compute market linkage matches. Check the backend terminal.",
        ) from error


@router.get(
    "/api/market-linkage/buyer/{requirement_id}/matches",
    response_model=BuyerMatchesResponse,
    summary="Find matching artisan products for a buyer requirement",
    description="Scans artisan catalog products and ranks compatible products for a buyer requirement.",
)
def get_matches_for_buyer_requirement(
    requirement_id: str,
    min_score: float = Query(default=40.0, ge=0.0, le=100.0, description="Minimum match score threshold (0-100)"),
    max_results: int = Query(default=20, ge=1, le=100, description="Maximum number of matches to return"),
):
    try:
        results = find_matches_for_buyer(
            requirement_id=requirement_id,
            min_score=min_score,
            max_results=max_results,
        )
        return results
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err)) from val_err
    except Exception as error:
        print(f"Error matching buyer requirement {requirement_id}: {type(error).__name__}: {error}")
        raise HTTPException(
            status_code=500,
            detail="Failed to compute buyer matches.",
        ) from error
