
from datetime import datetime, timezone
from typing import Any

from pymongo.errors import PyMongoError

from backend.app.database.connection import database
from backend.app.schemas.pricing import PricingResponse


def init_pricing_indexes() -> None:
    """Create indexes safely on pricing_records collection."""
    try:
        collection = database["pricing_records"]
        collection.create_index(
            [("product_id", 1), ("created_at", -1)],
            background=True,
            name="idx_product_id_created_at",
        )
    except Exception as error:
        print(f"Notice: Index creation on 'pricing_records' skipped or failed: {error}")


def save_pricing_record(result: PricingResponse) -> dict[str, Any]:
    """
    Save a pricing recommendation to MongoDB.
    Raises PyMongoError if persistence fails so caller does not report false success.
    """
    collection = database["pricing_records"]

    now = datetime.now(timezone.utc)
    document = result.model_dump()

    # Store timezone-aware UTC datetime
    document["created_at"] = now

    insert_result = collection.insert_one(document)
    record_id_str = str(insert_result.inserted_id)

    # Populate response object attributes if mutable
    result.record_id = record_id_str
    result.created_at = now.isoformat()

    return {
        "record_id": record_id_str,
        "product_id": result.product_id,
        "suggested_selling_price": result.suggested_selling_price,
        "saved": True,
        "collection": "pricing_records",
        "created_at": now.isoformat(),
    }


def _normalize_pricing_record(doc: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize record for API consumption:
    - Serializes ObjectId to string
    - Serializes datetime to ISO format
    - Ensures backward-compatibility defaults for legacy records
    """
    if "_id" in doc:
        doc["record_id"] = str(doc.pop("_id"))
    elif "record_id" not in doc:
        doc["record_id"] = None

    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()

    # Provide defaults for fields if reading legacy records
    doc.setdefault("shipping_cost", 0.0)
    doc.setdefault("other_variable_costs", 0.0)
    doc.setdefault("discounted_price", None)
    doc.setdefault("pricing_strategy", "exact")
    doc.setdefault("warnings", [])

    return doc


def get_pricing_records(
    product_id: str,
    limit: int = 50,
    skip: int = 0,
) -> list[dict[str, Any]]:
    """
    Retrieve pricing history for a product (newest first).
    Supports pagination via limit and skip.
    """
    collection = database["pricing_records"]

    cursor = (
        collection.find({"product_id": product_id})
        .sort("created_at", -1)
        .skip(max(0, skip))
        .limit(max(1, min(limit, 100)))
    )

    records = [_normalize_pricing_record(doc) for doc in cursor]
    return records


def get_latest_pricing_record(product_id: str) -> dict[str, Any] | None:
    """
    Retrieve the single most recent pricing record for a given product ID.
    Returns None if no record exists.
    """
    collection = database["pricing_records"]

    doc = collection.find_one(
        {"product_id": product_id},
        sort=[("created_at", -1)],
    )

    if doc is None:
        return None

    return _normalize_pricing_record(doc)


def count_pricing_records(product_id: str) -> int:
    """Return the total number of pricing records saved for a product."""
    collection = database["pricing_records"]
    return collection.count_documents({"product_id": product_id})
