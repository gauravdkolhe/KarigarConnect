from fastapi import APIRouter, Depends, Query, status

from backend.app.schemas.auth import UserProfileResponse
from backend.app.schemas.market_linkage import ProductMatchesResponse
from backend.app.schemas.workflow import (
    WorkflowCatalogApprovalRequest,
    WorkflowInventoryRequest,
    WorkflowPricingRequest,
    WorkflowProductCreate,
    WorkflowStateResponse,
)
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.matching_service import find_matches_for_product
from backend.app.services.product_workflow_service import (
    approve_workflow_catalog,
    calculate_workflow_pricing,
    configure_workflow_inventory,
    create_product_draft,
    generate_workflow_catalog_ai,
    get_workflow_state,
    list_artisan_workflows,
    publish_workflow_product,
)

router = APIRouter(
    prefix="/api/workflow",
    tags=["Four-Agent Product Workflow"],
)


@router.post(
    "/products",
    response_model=WorkflowStateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Step 1: Start a new product workflow",
    description="Initializes a new artisan product draft. Accessible to authenticated artisans.",
)
def create_product(
    request: WorkflowProductCreate,
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return create_product_draft(current_user.user_id, request)


@router.get(
    "/products",
    summary="List artisan products and workflow states",
    description="Lists all product workflows created by the authenticated artisan with current lifecycle status.",
)
def list_products(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    records, total = list_artisan_workflows(
        artisan_id=current_user.user_id,
        limit=limit,
        skip=skip,
    )
    return {
        "total_records": total,
        "limit": limit,
        "skip": skip,
        "products": records,
    }


@router.get(
    "/products/{product_id}",
    response_model=WorkflowStateResponse,
    summary="Get unified product state across all 4 agents",
    description="Aggregates images, catalog, latest pricing, operational inventory, and genuine buyer matches.",
)
def get_product_state(
    product_id: str,
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return get_workflow_state(product_id, artisan_id=current_user.user_id)


@router.post(
    "/products/{product_id}/ai-catalog",
    response_model=WorkflowStateResponse,
    summary="Step 3: Auto-generate product catalog using AI",
    description="Invokes the Product Catalog Agent (powered by Gemini AI) to automatically generate title, keywords, and description for the product.",
)
def auto_generate_catalog(
    product_id: str,
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return generate_workflow_catalog_ai(product_id, current_user.user_id)


@router.post(
    "/products/{product_id}/catalog",
    response_model=WorkflowStateResponse,
    summary="Step 3: Review and approve catalog",
    description="Saves approved product catalog (titles, descriptions, keywords).",
)
def submit_catalog_approval(
    product_id: str,
    request: WorkflowCatalogApprovalRequest,
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return approve_workflow_catalog(product_id, current_user.user_id, request)


@router.post(
    "/products/{product_id}/pricing",
    response_model=WorkflowStateResponse,
    summary="Step 4: Execute dynamic pricing recommendation",
    description="Runs deterministic pricing engine and persists pricing record for the product.",
)
def submit_pricing_calculation(
    product_id: str,
    request: WorkflowPricingRequest,
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return calculate_workflow_pricing(product_id, current_user.user_id, request)


@router.post(
    "/products/{product_id}/inventory",
    response_model=WorkflowStateResponse,
    summary="Step 5: Configure operational inventory & capacity",
    description="Sets ready stock, monthly crafting capacity, minimum order batch, and production lead times.",
)
def submit_inventory_configuration(
    product_id: str,
    request: WorkflowInventoryRequest,
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return configure_workflow_inventory(product_id, current_user.user_id, request)


@router.post(
    "/products/{product_id}/publish",
    response_model=WorkflowStateResponse,
    summary="Step 7: Final review and product publication",
    description="Publishes the completed artisan product listing after verifying all previous agent steps.",
)
def publish_product(
    product_id: str,
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return publish_workflow_product(product_id, current_user.user_id)


@router.get(
    "/products/{product_id}/matches",
    response_model=ProductMatchesResponse,
    summary="Step 6: Discover genuine buyer matches",
    description="Runs Market Linkage Agent to match artisan product with active buyer requirements in MongoDB.",
)
def get_product_buyer_matches(
    product_id: str,
    min_score: float = Query(default=30.0, ge=0.0, le=100.0),
    max_results: int = Query(default=20, ge=1, le=100),
    current_user: UserProfileResponse = Depends(require_role(["artisan", "admin"])),
):
    return find_matches_for_product(
        product_id=product_id,
        min_score=min_score,
        max_results=max_results,
    )
