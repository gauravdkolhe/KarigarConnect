from datetime import datetime, timezone
import re
from typing import Any
from uuid import uuid4

from pymongo.errors import PyMongoError

from backend.app.database.connection import database
from backend.app.schemas.market_linkage import (
    BuyerRequirementCreate,
    BuyerRequirementUpdate,
)


def init_market_linkage_indexes() -> None:
    """Safely initialize MongoDB indexes for buyer requirements, inventory, and matches."""
    try:
        # buyer_requirements indexes
        req_col = database["buyer_requirements"]
        req_col.create_index("requirement_id", unique=True, background=True, name="idx_req_id_unique")
        req_col.create_index([("requirement_status", 1), ("created_at", -1)], background=True, name="idx_req_status_created")
        req_col.create_index([("required_category", 1), ("requirement_status", 1)], background=True, name="idx_req_cat_status")
        req_col.create_index("buyer_id", background=True, name="idx_req_buyer_id")

        # artisan_inventory indexes
        inv_col = database["artisan_inventory"]
        inv_col.create_index("product_id", unique=True, background=True, name="idx_inv_product_id_unique")
        inv_col.create_index("artisan_id", background=True, name="idx_inv_artisan_id")

        # market_linkage_matches indexes
        match_col = database["market_linkage_matches"]
        match_col.create_index("match_id", unique=True, background=True, name="idx_match_id_unique")
        match_col.create_index([("product_id", 1), ("created_at", -1)], background=True, name="idx_match_product")
        match_col.create_index([("requirement_id", 1), ("created_at", -1)], background=True, name="idx_match_req")
    except Exception as error:
        print(f"Notice: Market linkage index initialization skipped or failed: {error}")


def mask_contact_email(email: str | None) -> str | None:
    """Mask email for privacy in public endpoints: e.g. 'john.doe@example.com' -> 'j***e@e***.com'."""
    if not email or "@" not in email:
        return None
    user, domain = email.split("@", 1)
    masked_user = f"{user[0]}***{user[-1]}" if len(user) > 1 else f"{user}***"
    domain_parts = domain.split(".")
    if len(domain_parts) > 1:
        masked_domain = f"{domain_parts[0][0]}***.{domain_parts[-1]}"
    else:
        masked_domain = "hidden"
    return f"{masked_user}@{masked_domain}"


def mask_contact_phone(phone: str | None) -> str | None:
    """Mask phone for privacy in public endpoints: e.g. '+91-9876543210' -> '+91-***-***3210'."""
    if not phone:
        return None
    clean = phone.strip()
    if len(clean) > 4:
        return f"***-***-{clean[-4:]}"
    return "****"


def _normalize_requirement_doc(doc: dict[str, Any], mask_contact: bool = True) -> dict[str, Any]:
    """Clean MongoDB document for API responses, serialize dates, and handle privacy masking."""
    doc = dict(doc)
    if "_id" in doc:
        doc.pop("_id")

    for dt_field in ("created_at", "updated_at"):
        val = doc.get(dt_field)
        if isinstance(val, datetime):
            doc[dt_field] = val.isoformat()
        elif val is None:
            doc[dt_field] = datetime.now(timezone.utc).isoformat()

    if mask_contact:
        doc["contact_email"] = mask_contact_email(doc.get("contact_email"))
        doc["contact_phone"] = mask_contact_phone(doc.get("contact_phone"))

    return doc


def create_buyer_requirement(data: BuyerRequirementCreate) -> dict[str, Any]:
    """
    Persist a genuine buyer requirement in MongoDB.
    Generates a unique human-friendly requirement_id (REQ-...) and UTC timestamps.
    """
    collection = database["buyer_requirements"]

    req_id = f"REQ-{uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)

    doc = data.model_dump()
    doc["requirement_id"] = req_id
    doc["created_at"] = now
    doc["updated_at"] = now

    collection.insert_one(doc)

    return _normalize_requirement_doc(doc, mask_contact=False)


def get_buyer_requirement(requirement_id: str, mask_contact: bool = False) -> dict[str, Any] | None:
    """Retrieve a single buyer requirement by ID."""
    collection = database["buyer_requirements"]

    doc = collection.find_one({"requirement_id": requirement_id})
    if doc is None:
        return None

    return _normalize_requirement_doc(doc, mask_contact=mask_contact)


def list_buyer_requirements(
    status: str | None = "active",
    category: str | None = None,
    buyer_type: str | None = None,
    limit: int = 50,
    skip: int = 0,
    mask_contact: bool = True,
) -> tuple[list[dict[str, Any]], int]:
    """
    List buyer requirements with optional filtering and pagination.
    Returns (records, total_count).
    """
    collection = database["buyer_requirements"]

    query: dict[str, Any] = {}
    if status is not None and status != "all":
        query["requirement_status"] = status
    if category is not None and category.strip():
        query["required_category"] = category.strip()
    if buyer_type is not None and buyer_type.strip():
        query["buyer_type"] = buyer_type.strip()

    total = collection.count_documents(query)
    cursor = (
        collection.find(query)
        .sort("created_at", -1)
        .skip(max(0, skip))
        .limit(max(1, min(limit, 100)))
    )

    records = [_normalize_requirement_doc(d, mask_contact=mask_contact) for d in cursor]
    return records, total


def update_buyer_requirement(
    requirement_id: str,
    update_data: BuyerRequirementUpdate,
    mask_contact: bool = False,
) -> dict[str, Any] | None:
    """Update fields of an existing buyer requirement."""
    collection = database["buyer_requirements"]

    updates = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        existing = get_buyer_requirement(requirement_id, mask_contact=mask_contact)
        return existing

    updates["updated_at"] = datetime.now(timezone.utc)

    result = collection.find_one_and_update(
        {"requirement_id": requirement_id},
        {"$set": updates},
        return_document=True,
    )

    if result is None:
        return None

    return _normalize_requirement_doc(result, mask_contact=mask_contact)


def update_requirement_status(
    requirement_id: str,
    new_status: str,
    mask_contact: bool = False,
) -> dict[str, Any] | None:
    """Transition requirement status (active, paused, fulfilled, expired, cancelled)."""
    collection = database["buyer_requirements"]

    result = collection.find_one_and_update(
        {"requirement_id": requirement_id},
        {
            "$set": {
                "requirement_status": new_status,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=True,
    )

    if result is None:
        return None

    return _normalize_requirement_doc(result, mask_contact=mask_contact)


def delete_or_archive_requirement(requirement_id: str, hard_delete: bool = False) -> bool:
    """
    Safely delete or archive a requirement.
    By default (hard_delete=False), marks status as 'cancelled'.
    """
    collection = database["buyer_requirements"]

    if hard_delete:
        del_result = collection.delete_one({"requirement_id": requirement_id})
        return del_result.deleted_count > 0
    else:
        upd = collection.update_one(
            {"requirement_id": requirement_id},
            {
                "$set": {
                    "requirement_status": "cancelled",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return upd.matched_count > 0
