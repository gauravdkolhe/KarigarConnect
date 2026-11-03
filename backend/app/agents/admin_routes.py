from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from backend.app.database.connection import database
from backend.app.schemas.auth import UserProfileResponse, UserStatus
from backend.app.services.auth_service import require_role

router = APIRouter(
    prefix="/api/admin",
    tags=["Administrative Oversight"],
)


class UserStatusChangeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: UserStatus
    reason: str = Field(default="Administrative policy review", min_length=3, max_length=500)


class ProductModerationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    workflow_status: str
    moderation_note: str | None = Field(default=None, max_length=500)


@router.get(
    "/metrics",
    summary="Platform overview metrics",
    description="Calculates live platform aggregates directly from genuine MongoDB collections.",
)
def get_platform_metrics(
    admin: UserProfileResponse = Depends(require_role(["admin"])),
):
    total_artisans = database["users"].count_documents({"role": "artisan"})
    total_buyers = database["users"].count_documents({"role": "buyer"})
    total_products = database["product_workflows"].count_documents({})
    published_products = database["product_workflows"].count_documents({"workflow_status": "published"})
    total_requirements = database["buyer_requirements"].count_documents({})
    active_requirements = database["buyer_requirements"].count_documents({"requirement_status": "active"})
    total_inquiries = database["buyer_inquiries"].count_documents({})
    total_pricing_records = database["pricing_records"].count_documents({})

    # Category aggregation from product_catalogs
    cat_pipeline = [
        {"$group": {"_id": "$product_details.purpose", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 8},
    ]
    cat_agg = list(database["product_catalogs"].aggregate(cat_pipeline))
    categories_breakdown = [
        {"category": item["_id"] or "General Crafts", "count": item["count"]}
        for item in cat_agg
    ]

    return {
        "total_artisans": total_artisans,
        "total_buyers": total_buyers,
        "total_products": total_products,
        "published_products": published_products,
        "total_requirements": total_requirements,
        "active_requirements": active_requirements,
        "total_inquiries": total_inquiries,
        "total_pricing_records": total_pricing_records,
        "categories_breakdown": categories_breakdown,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/users",
    summary="List platform users",
    description="List registered artisans and buyers with optional role and status filters.",
)
def list_users(
    role: str | None = Query(default=None, description="artisan, buyer, admin"),
    status: str | None = Query(default=None, description="active, suspended"),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    admin: UserProfileResponse = Depends(require_role(["admin"])),
):
    query: dict[str, Any] = {}
    if role and role != "all":
        query["role"] = role
    if status and status != "all":
        query["status"] = status

    total = database["users"].count_documents(query)
    cursor = database["users"].find(query, {"password_hash": 0, "_id": 0}).sort("created_at", -1).skip(skip).limit(limit)

    users = []
    for d in cursor:
        for dt_field in ("created_at", "updated_at"):
            if isinstance(d.get(dt_field), datetime):
                d[dt_field] = d[dt_field].isoformat()
        users.append(d)

    return {"total_users": total, "limit": limit, "skip": skip, "users": users}


@router.patch(
    "/users/{user_id}/status",
    summary="Suspend or reactivate user account",
)
def update_user_status(
    user_id: str,
    request: UserStatusChangeRequest,
    admin: UserProfileResponse = Depends(require_role(["admin"])),
):
    user = database["users"].find_one({"user_id": user_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Cannot suspend an administrator account.")

    now = datetime.now(timezone.utc)
    database["users"].update_one(
        {"user_id": user_id},
        {
            "$set": {
                "status": request.status,
                "status_reason": request.reason,
                "updated_at": now,
            }
        },
    )

    # Log audit
    database["audit_logs"].insert_one({
        "action": "user_status_changed",
        "target_user_id": user_id,
        "admin_user_id": admin.user_id,
        "previous_status": user.get("status"),
        "new_status": request.status,
        "reason": request.reason,
        "timestamp": now,
    })

    return {
        "user_id": user_id,
        "status": request.status,
        "message": f"User status successfully updated to {request.status}.",
    }


@router.get(
    "/products",
    summary="List all platform products for moderation",
)
def list_all_products(
    status_filter: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    admin: UserProfileResponse = Depends(require_role(["admin"])),
):
    query = {}
    if status_filter and status_filter != "all":
        query["workflow_status"] = status_filter

    total = database["product_workflows"].count_documents(query)
    cursor = database["product_workflows"].find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)

    products = []
    for d in cursor:
        pid = d["product_id"]
        # Fetch thumbnail & artisan email
        img = database["product_images"].find_one({"product_id": pid}, {"_id": 1})
        thumb = f"/api/images/{img['_id']}/file" if img else None
        artisan = database["users"].find_one({"user_id": d.get("artisan_id")}, {"email": 1, "full_name": 1})

        for dt in ("created_at", "updated_at"):
            if isinstance(d.get(dt), datetime):
                d[dt] = d[dt].isoformat()

        d["thumbnail_url"] = thumb
        d["artisan_name"] = artisan.get("full_name") if artisan else "Unknown"
        d["artisan_email"] = artisan.get("email") if artisan else None
        products.append(d)

    return {"total_products": total, "limit": limit, "skip": skip, "products": products}


@router.patch(
    "/products/{product_id}/status",
    summary="Moderate product workflow status",
)
def moderate_product(
    product_id: str,
    request: ProductModerationRequest,
    admin: UserProfileResponse = Depends(require_role(["admin"])),
):
    wf = database["product_workflows"].find_one({"product_id": product_id})
    if wf is None:
        raise HTTPException(status_code=404, detail="Product not found.")

    now = datetime.now(timezone.utc)
    database["product_workflows"].update_one(
        {"product_id": product_id},
        {
            "$set": {
                "workflow_status": request.workflow_status,
                "moderation_note": request.moderation_note,
                "updated_at": now,
            }
        },
    )

    return {
        "product_id": product_id,
        "workflow_status": request.workflow_status,
        "message": f"Product status updated to '{request.workflow_status}'.",
    }
