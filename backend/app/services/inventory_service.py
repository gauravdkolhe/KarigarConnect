from datetime import datetime, timezone
from typing import Any

from backend.app.database.connection import database
from backend.app.schemas.market_linkage import ArtisanInventory, ArtisanProductProfile


def save_artisan_inventory(data: ArtisanInventory) -> dict[str, Any]:
    """Persist or update artisan operational inventory parameters."""
    collection = database["artisan_inventory"]
    now = datetime.now(timezone.utc)

    doc = data.model_dump()
    doc["updated_at"] = now

    collection.update_one(
        {"product_id": data.product_id},
        {
            "$set": doc,
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )

    doc.pop("_id", None)
    doc["updated_at"] = now.isoformat()
    return doc


def get_artisan_inventory(product_id: str) -> dict[str, Any] | None:
    """Retrieve saved artisan inventory record by product ID."""
    collection = database["artisan_inventory"]
    doc = collection.find_one({"product_id": product_id}, {"_id": 0})
    return doc


def get_artisan_product_profile(
    product_id: str,
    inventory_override: ArtisanInventory | None = None,
) -> tuple[ArtisanProductProfile | None, list[str]]:
    """
    Assemble the complete artisan product profile by aggregating:
    1. product_catalogs (title, description, keywords, materials, craft type)
    2. pricing_records (latest suggested selling price)
    3. artisan_inventory (ready stock, monthly capacity, lead time, location)
    
    Returns (profile, warnings).
    """
    warnings: list[str] = []

    # 1. Fetch Catalog Document
    cat_doc = database["product_catalogs"].find_one({"product_id": product_id}, {"_id": 0})
    if cat_doc is None:
        warnings.append(f"Catalog not found for product_id '{product_id}'.")
        return None, warnings

    prod_details = cat_doc.get("product_details", {})
    material = prod_details.get("material", "Natural Material")
    craft_type = prod_details.get("craft_type")
    color = prod_details.get("color")
    purpose = prod_details.get("purpose", "")

    # Category heuristic from purpose/details or default
    category = purpose if purpose else "Handicrafts"

    # 2. Fetch Latest Pricing Record
    price_doc = database["pricing_records"].find_one(
        {"product_id": product_id},
        sort=[("created_at", -1)],
    )

    unit_price = 0.0
    currency = "INR"

    if price_doc is not None and "suggested_selling_price" in price_doc:
        unit_price = float(price_doc["suggested_selling_price"])
        currency = price_doc.get("currency", "INR")
    else:
        warnings.append(
            f"No pricing recommendation found for product '{product_id}'. "
            "Please run dynamic pricing first or provide price in inventory."
        )

    # 3. Fetch or Apply Inventory
    inv_doc = inventory_override.model_dump() if inventory_override else get_artisan_inventory(product_id)

    if inv_doc is None:
        warnings.append(
            "Artisan operational inventory record not found. "
            "Applying baseline defaults (Available: 10, Capacity: 50/mo, Lead time: 14 days, Location: India)."
        )
        inv_doc = {
            "artisan_id": "ARTISAN_DEFAULT",
            "available_quantity": 10,
            "production_capacity_per_month": 50,
            "minimum_order_quantity": 1,
            "production_lead_time_days": 14,
            "location": "India",
            "product_status": "available",
        }

    # If inventory specifies a unit_price override, respect it
    if inv_doc.get("unit_price") is not None and inv_doc["unit_price"] > 0:
        unit_price = float(inv_doc["unit_price"])
        currency = inv_doc.get("currency", currency)

    profile = ArtisanProductProfile(
        product_id=product_id,
        artisan_id=inv_doc.get("artisan_id", "ARTISAN_DEFAULT"),
        product_name=cat_doc.get("product_name", product_id),
        product_title=cat_doc.get("product_title", cat_doc.get("product_name", product_id)),
        category=category,
        description=cat_doc.get("description", ""),
        keywords=cat_doc.get("keywords", []),
        material=material,
        craft_type=craft_type,
        color=color,
        available_quantity=inv_doc.get("available_quantity", 0),
        production_capacity=inv_doc.get("production_capacity_per_month", 50),
        minimum_order_quantity=inv_doc.get("minimum_order_quantity", 1),
        unit_price=unit_price,
        currency=currency,
        production_lead_time_days=inv_doc.get("production_lead_time_days", 14),
        location=inv_doc.get("location", "India"),
        product_status=inv_doc.get("product_status", "available"),
    )

    return profile, warnings
