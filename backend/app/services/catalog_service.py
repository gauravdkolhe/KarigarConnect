
from datetime import datetime, timezone

from backend.app.database.connection import database
from backend.app.schemas.catalog import CatalogRequest, CatalogResponse


def save_catalog(
    request: CatalogRequest,
    response: CatalogResponse,
) -> dict:
    """Save generated catalog content to MongoDB."""

    collection = database["product_catalogs"]
    now = datetime.now(timezone.utc)

    document = {
        "product_id": response.product_id,
        "product_name": request.product_name,
        "product_title": response.product_title,
        "keywords": response.keywords,
        "description": response.description,
        "language": response.language,
        "requires_artisan_review": True,
        "product_details": request.details.model_dump(),
        "updated_at": now,
    }

    collection.update_one(
        {"product_id": response.product_id},
        {
            "$set": document,
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )

    return {
        "product_id": response.product_id,
        "product_title": response.product_title,
        "saved": True,
        "collection": "product_catalogs",
    }


def get_catalog(product_id: str) -> dict | None:
    """Retrieve a saved catalog document by product ID."""

    collection = database["product_catalogs"]

    document = collection.find_one(
        {"product_id": product_id},
        {"_id": 0},
    )

    return document


def save_manual_catalog(request) -> dict:
    """Save an artisan-approved catalog without calling Gemini."""

    from datetime import datetime, timezone

    collection = database["product_catalogs"]
    now = datetime.now(timezone.utc)

    document = {
        "product_id": request.product_id,
        "product_name": request.product_name,
        "product_title": request.product_title,
        "keywords": request.keywords,
        "description": request.description,
        "language": request.language,
        "requires_artisan_review": False,
        "product_details": request.details.model_dump(),
        "updated_at": now,
    }

    collection.update_one(
        {"product_id": request.product_id},
        {
            "$set": document,
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )

    return {
        "product_id": request.product_id,
        "product_title": request.product_title,
        "saved": True,
        "collection": "product_catalogs",
    }
