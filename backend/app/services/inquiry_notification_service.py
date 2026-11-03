from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from fastapi import HTTPException, status

from backend.app.database.connection import database
from backend.app.schemas.auth import UserProfileResponse
from backend.app.schemas.inquiry_notification import (
    InquiryCreateRequest,
    InquiryResponse,
    InquiryStatusUpdateRequest,
    NotificationResponse,
)


def init_inquiry_notification_indexes() -> None:
    """Initialize MongoDB indexes for inquiries and notifications."""
    try:
        inq_col = database["buyer_inquiries"]
        inq_col.create_index("inquiry_id", unique=True, background=True, name="idx_inq_id_unique")
        inq_col.create_index([("artisan_id", 1), ("created_at", -1)], background=True, name="idx_inq_artisan")
        inq_col.create_index([("buyer_id", 1), ("created_at", -1)], background=True, name="idx_inq_buyer")

        notif_col = database["notifications"]
        notif_col.create_index("notification_id", unique=True, background=True, name="idx_notif_id_unique")
        notif_col.create_index([("user_id", 1), ("is_read", 1), ("created_at", -1)], background=True, name="idx_notif_user_read")
    except Exception as error:
        print(f"Notice: Inquiry/notification index initialization skipped or failed: {error}")


def create_notification(
    user_id: str,
    title: str,
    message: str,
    notification_type: str,
    reference_id: str | None = None,
) -> dict[str, Any]:
    """Emit an in-app notification to a user."""
    col = database["notifications"]
    now = datetime.now(timezone.utc)
    notif_id = f"NOTIF-{uuid4().hex[:8].upper()}"

    doc = {
        "notification_id": notif_id,
        "user_id": user_id,
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "reference_id": reference_id,
        "is_read": False,
        "created_at": now,
    }
    col.insert_one(doc)
    doc.pop("_id", None)
    doc["created_at"] = now.isoformat()
    return doc


def list_notifications(user_id: str, limit: int = 50, skip: int = 0) -> tuple[list[dict[str, Any]], int]:
    """Retrieve notifications for authenticated user (newest first)."""
    col = database["notifications"]
    query = {"user_id": user_id}
    total = col.count_documents(query)

    cursor = col.find(query, {"_id": 0}).sort("created_at", -1).skip(max(0, skip)).limit(max(1, min(limit, 100)))
    records = []
    for d in cursor:
        if isinstance(d.get("created_at"), datetime):
            d["created_at"] = d["created_at"].isoformat()
        records.append(d)
    return records, total


def mark_notification_read(notification_id: str, user_id: str) -> bool:
    """Mark a specific notification as read."""
    col = database["notifications"]
    res = col.update_one(
        {"notification_id": notification_id, "user_id": user_id},
        {"$set": {"is_read": True}},
    )
    return res.matched_count > 0


def mark_all_notifications_read(user_id: str) -> int:
    """Mark all notifications as read for a user."""
    col = database["notifications"]
    res = col.update_many(
        {"user_id": user_id, "is_read": False},
        {"$set": {"is_read": True}},
    )
    return res.modified_count


def create_inquiry(buyer: UserProfileResponse, data: InquiryCreateRequest) -> InquiryResponse:
    """Submit a genuine buyer inquiry to an artisan for a product."""
    # Find product and determine artisan owner
    wf_doc = database["product_workflows"].find_one({"product_id": data.product_id})
    cat_doc = database["product_catalogs"].find_one({"product_id": data.product_id})
    product_name = wf_doc.get("product_name") if wf_doc else (cat_doc.get("product_name") if cat_doc else data.product_id)

    artisan_id = wf_doc.get("artisan_id") if wf_doc else "ARTISAN_DEFAULT"

    col = database["buyer_inquiries"]
    now = datetime.now(timezone.utc)
    inq_id = f"INQ-{uuid4().hex[:8].upper()}"

    doc = {
        "inquiry_id": inq_id,
        "product_id": data.product_id,
        "product_name": product_name,
        "artisan_id": artisan_id,
        "buyer_id": buyer.user_id,
        "buyer_name": buyer.full_name,
        "buyer_business": buyer.business_name,
        "buyer_contact_email": buyer.email,
        "buyer_contact_phone": buyer.phone,
        "requirement_id": data.requirement_id,
        "quantity_requested": data.quantity_requested,
        "target_price_per_unit": data.target_price_per_unit,
        "delivery_destination": data.delivery_destination,
        "message": data.message,
        "status": "pending",
        "artisan_response_note": None,
        "created_at": now,
        "updated_at": now,
    }
    col.insert_one(doc)

    # Notify the artisan
    create_notification(
        user_id=artisan_id,
        title="New Buyer Inquiry Received!",
        message=f"{buyer.full_name} submitted an inquiry for {data.quantity_requested} units of '{product_name}'.",
        notification_type="new_inquiry",
        reference_id=inq_id,
    )

    doc.pop("_id", None)
    doc["created_at"] = now.isoformat()
    doc["updated_at"] = now.isoformat()
    return InquiryResponse(**doc)


def list_inquiries(
    user: UserProfileResponse,
    status_filter: str | None = None,
    limit: int = 50,
    skip: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """List inquiries filtered by user role (artisan sees received; buyer sees sent; admin sees all)."""
    col = database["buyer_inquiries"]
    query: dict[str, Any] = {}

    if user.role == "artisan":
        query["artisan_id"] = user.user_id
    elif user.role == "buyer":
        query["buyer_id"] = user.user_id
    # admin sees all

    if status_filter and status_filter != "all":
        query["status"] = status_filter

    total = col.count_documents(query)
    cursor = col.find(query, {"_id": 0}).sort("created_at", -1).skip(max(0, skip)).limit(max(1, min(limit, 100)))

    records = []
    for d in cursor:
        for dt_field in ("created_at", "updated_at"):
            if isinstance(d.get(dt_field), datetime):
                d[dt_field] = d[dt_field].isoformat()
        records.append(d)

    return records, total


def update_inquiry_status(
    inquiry_id: str,
    user: UserProfileResponse,
    data: InquiryStatusUpdateRequest,
) -> dict[str, Any]:
    """Transition inquiry status (accept, reply, decline, close)."""
    col = database["buyer_inquiries"]
    inq = col.find_one({"inquiry_id": inquiry_id})
    if inq is None:
        raise HTTPException(status_code=404, detail="Inquiry not found.")

    # Only artisan recipient, buyer creator, or admin can update
    if user.role != "admin" and user.user_id not in (inq["artisan_id"], inq["buyer_id"]):
        raise HTTPException(status_code=403, detail="You do not have access to this inquiry.")

    now = datetime.now(timezone.utc)
    updates: dict[str, Any] = {
        "status": data.status,
        "updated_at": now,
    }
    if data.artisan_response_note:
        updates["artisan_response_note"] = data.artisan_response_note

    updated = col.find_one_and_update(
        {"inquiry_id": inquiry_id},
        {"$set": updates},
        return_document=True,
    )

    # Notify counterparty
    target_user_id = inq["buyer_id"] if user.user_id == inq["artisan_id"] else inq["artisan_id"]
    create_notification(
        user_id=target_user_id,
        title=f"Inquiry Status Updated: {data.status.capitalize()}",
        message=f"Inquiry for '{inq.get('product_name')}' was marked as {data.status}.",
        notification_type="inquiry_update",
        reference_id=inquiry_id,
    )

    updated.pop("_id", None)
    for dt_field in ("created_at", "updated_at"):
        if isinstance(updated.get(dt_field), datetime):
            updated[dt_field] = updated[dt_field].isoformat()
    return updated
