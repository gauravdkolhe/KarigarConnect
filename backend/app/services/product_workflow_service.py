from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from fastapi import HTTPException, status

from backend.app.database.connection import database
from backend.app.schemas.catalog import CatalogManualSaveRequest, CatalogRequest, ProductDetails
from backend.app.schemas.market_linkage import ArtisanInventory
from backend.app.schemas.pricing import PricingRequest
from backend.app.schemas.workflow import (
    WorkflowCatalogApprovalRequest,
    WorkflowInventoryRequest,
    WorkflowPricingRequest,
    WorkflowProductCreate,
    WorkflowQuickAssistRequest,
    WorkflowSingleApproveRequest,
    ProductVariation,
    ProductVariationUpsert,
    WorkflowStateResponse,
    WorkflowStatus,
)
from backend.app.agents.catalog_agent import generate_catalog, generate_catalog_with_prompt
from backend.app.agents.orchestrator_agent import orchestrate
from backend.app.services.catalog_service import save_catalog, save_manual_catalog
from backend.app.services.inventory_service import get_artisan_inventory, save_artisan_inventory
from backend.app.services.matching_service import find_matches_for_product
from backend.app.services.pricing_persistence import get_latest_pricing_record, save_pricing_record
from backend.app.services.pricing_service import calculate_price


def init_workflow_indexes() -> None:
    """Initialize MongoDB indexes for product_workflows collection."""
    try:
        col = database["product_workflows"]
        col.create_index("product_id", unique=True, background=True, name="idx_wf_product_id_unique")
        col.create_index([("artisan_id", 1), ("created_at", -1)], background=True, name="idx_wf_artisan_created")
        col.create_index("workflow_status", background=True, name="idx_wf_status")
    except Exception as error:
        print(f"Notice: Workflow index initialization skipped or failed: {error}")


def create_product_draft(artisan_id: str, data: WorkflowProductCreate) -> WorkflowStateResponse:
    """Step 1: Initialize a new product draft and attach it to the authenticated artisan."""
    col = database["product_workflows"]
    now = datetime.now(timezone.utc)
    product_id = f"PROD-{uuid4().hex[:8].upper()}"

    doc = {
        "product_id": product_id,
        "artisan_id": artisan_id,
        "product_name": data.product_name,
        "workflow_status": "draft",
        "steps_completed": ["product_created"],
        "created_at": now,
        "updated_at": now,
    }
    col.insert_one(doc)

    # Initialize initial catalog entry in product_catalogs to satisfy image upload requirements
    initial_catalog_req = CatalogManualSaveRequest(
        product_id=product_id,
        product_name=data.product_name,
        product_title=data.product_name,
        keywords=["handmade", "craft", data.category.lower(), data.initial_material.lower()],
        description=f"Handcrafted {data.product_name} crafted using {data.initial_material}.",
        language=data.language,
        details=ProductDetails(
            material=data.initial_material,
            craft_type=data.initial_craft_type,
            purpose=data.category,
        ),
    )
    save_manual_catalog(initial_catalog_req)

    return get_workflow_state(product_id, artisan_id=artisan_id)


def get_workflow_state(product_id: str, artisan_id: str | None = None) -> WorkflowStateResponse:
    """Retrieve consolidated product state across all 4 agents."""
    wf_doc = database["product_workflows"].find_one({"product_id": product_id}, {"_id": 0})
    if wf_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product workflow '{product_id}' not found.",
        )

    # Check artisan ownership if requested
    if artisan_id and wf_doc.get("artisan_id") != artisan_id and artisan_id != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view or manage this product.",
        )

    # Images
    images_cursor = database["product_images"].find({"product_id": product_id}, {"_id": 1, "enhanced_filename": 1, "created_at": 1, "enhanced_dimensions": 1}).sort("created_at", -1)
    images = []
    for img in images_cursor:
        images.append({
            "image_id": str(img["_id"]),
            "enhanced_filename": img.get("enhanced_filename"),
            "file_url": f"/api/images/{img['_id']}/file",
        })

    # Catalog
    catalog_doc = database["product_catalogs"].find_one({"product_id": product_id}, {"_id": 0})

    # Pricing
    pricing_doc = get_latest_pricing_record(product_id)

    # Inventory
    inventory_doc = get_artisan_inventory(product_id)

    # Match count (safely computed if catalog & pricing exist)
    match_count = 0
    if catalog_doc is not None and pricing_doc is not None:
        try:
            matches_res = find_matches_for_product(product_id, min_score=40.0, max_results=50)
            match_count = matches_res.total_matches
        except Exception:
            match_count = 0

    return WorkflowStateResponse(
        product_id=product_id,
        artisan_id=wf_doc.get("artisan_id", "UNKNOWN"),
        product_name=wf_doc.get("product_name", product_id),
        workflow_status=wf_doc.get("workflow_status", "draft"),
        steps_completed=wf_doc.get("steps_completed", []),
        images=images,
        catalog=catalog_doc,
        pricing=pricing_doc,
        inventory=inventory_doc,
        variations=wf_doc.get("variations", []),
        match_count=match_count,
        created_at=wf_doc.get("created_at", datetime.now(timezone.utc)).isoformat() if isinstance(wf_doc.get("created_at"), datetime) else str(wf_doc.get("created_at")),
        updated_at=wf_doc.get("updated_at", datetime.now(timezone.utc)).isoformat() if isinstance(wf_doc.get("updated_at"), datetime) else str(wf_doc.get("updated_at")),
    )


def list_artisan_workflows(artisan_id: str, limit: int = 50, skip: int = 0) -> tuple[list[dict[str, Any]], int]:
    """List all products belonging to an artisan with status and progress."""
    col = database["product_workflows"]
    query = {"artisan_id": artisan_id} if artisan_id != "admin" else {}

    total = col.count_documents(query)
    cursor = col.find(query, {"_id": 0}).sort("created_at", -1).skip(max(0, skip)).limit(max(1, min(limit, 100)))

    results = []
    for doc in cursor:
        pid = doc["product_id"]
        # Fetch thumbnail if available
        first_img = database["product_images"].find_one({"product_id": pid}, {"_id": 1})
        thumb_url = f"/api/images/{first_img['_id']}/file" if first_img else None

        # Fetch latest price if available
        price_rec = database["pricing_records"].find_one({"product_id": pid}, sort=[("created_at", -1)])
        price_val = price_rec.get("suggested_selling_price") if price_rec else None

        results.append({
            "product_id": pid,
            "artisan_id": doc.get("artisan_id"),
            "product_name": doc.get("product_name"),
            "workflow_status": doc.get("workflow_status"),
            "steps_completed": doc.get("steps_completed", []),
            "thumbnail_url": thumb_url,
            "suggested_selling_price": price_val,
            "created_at": doc.get("created_at").isoformat() if isinstance(doc.get("created_at"), datetime) else str(doc.get("created_at")),
            "updated_at": doc.get("updated_at").isoformat() if isinstance(doc.get("updated_at"), datetime) else str(doc.get("updated_at")),
        })

    return results, total


def generate_workflow_catalog_ai(product_id: str, artisan_id: str) -> WorkflowStateResponse:
    """Step 3: Auto-generate catalog using Gemini AI (Agent 2) with artisan draft context."""
    wf = _check_product_ownership(product_id, artisan_id)
    catalog_doc = database["product_catalogs"].find_one({"product_id": product_id}) or {}
    prod_details = catalog_doc.get("product_details", {}) or {}

    cat_req = CatalogRequest(
        product_id=product_id,
        product_name=wf.get("product_name", product_id),
        language=catalog_doc.get("language", "en"),
        details=ProductDetails(
            material=prod_details.get("material", "Natural Artisan Material"),
            craft_type=prod_details.get("craft_type", "Traditional Indian Craft"),
            color=prod_details.get("color", "Natural Amber"),
            purpose=prod_details.get("purpose", "Utility & Decor"),
        ),
    )

    generated = generate_catalog(cat_req)
    save_catalog(cat_req, generated)
    _update_workflow_step(product_id, "catalog_pending", "catalog_generated")
    return get_workflow_state(product_id, artisan_id=artisan_id)


def approve_workflow_catalog(
    product_id: str,
    artisan_id: str,
    data: WorkflowCatalogApprovalRequest,
) -> WorkflowStateResponse:
    """Step 3: Artisan review, edit, and approve catalog."""
    _check_product_ownership(product_id, artisan_id)

    # Save to product_catalogs collection
    save_req = CatalogManualSaveRequest(
        product_id=product_id,
        product_name=data.product_title,
        product_title=data.product_title,
        keywords=data.keywords,
        description=data.description,
        language="en",
        details=ProductDetails(
            material=data.material,
            craft_type=data.craft_type,
            color=data.color,
            purpose=data.purpose,
        ),
    )
    save_manual_catalog(save_req)

    # Update workflow state
    _update_workflow_step(product_id, "catalog_approved", "catalog_generation")
    return get_workflow_state(product_id, artisan_id=artisan_id)


def calculate_workflow_pricing(
    product_id: str,
    artisan_id: str,
    data: WorkflowPricingRequest,
) -> WorkflowStateResponse:
    """Step 4: Execute deterministic dynamic pricing and persist recommendation."""
    wf = _check_product_ownership(product_id, artisan_id)

    pricing_req = PricingRequest(
        product_id=product_id,
        product_name=wf.get("product_name", product_id),
        material_cost=data.material_cost,
        labor_cost=data.labor_cost,
        packaging_cost=data.packaging_cost,
        overhead_cost=data.overhead_cost,
        shipping_cost=data.shipping_cost,
        target_profit_margin_percent=data.target_profit_margin_percent,
        marketplace_commission_percent=data.marketplace_commission_percent,
        pricing_strategy=data.pricing_strategy,
    )
    result = calculate_price(pricing_req)
    save_pricing_record(result)

    _update_workflow_step(product_id, "pricing_calculated", "pricing_recommendation")
    return get_workflow_state(product_id, artisan_id=artisan_id)


def configure_workflow_inventory(
    product_id: str,
    artisan_id: str,
    data: WorkflowInventoryRequest,
) -> WorkflowStateResponse:
    """Step 5: Configure operational inventory ready stock, monthly capacity, and lead times."""
    _check_product_ownership(product_id, artisan_id)

    # Fetch latest price to attach to inventory
    price_rec = get_latest_pricing_record(product_id)
    unit_price = float(price_rec["suggested_selling_price"]) if price_rec else None

    inv = ArtisanInventory(
        product_id=product_id,
        artisan_id=artisan_id,
        available_quantity=data.available_quantity,
        production_capacity_per_month=data.production_capacity_per_month,
        minimum_order_quantity=data.minimum_order_quantity,
        unit_price=unit_price,
        production_lead_time_days=data.production_lead_time_days,
        location=data.location,
    )
    save_artisan_inventory(inv)

    _update_workflow_step(product_id, "inventory_configured", "inventory_configuration")
    return get_workflow_state(product_id, artisan_id=artisan_id)


def publish_workflow_product(product_id: str, artisan_id: str) -> WorkflowStateResponse:
    """Step 7: Final artisan review and public publishing."""
    _check_product_ownership(product_id, artisan_id)

    # Verify prerequisite steps
    cat = database["product_catalogs"].find_one({"product_id": product_id})
    if not cat:
        raise HTTPException(status_code=400, detail="Cannot publish: Catalog approval is required.")

    price = get_latest_pricing_record(product_id)
    if not price:
        raise HTTPException(status_code=400, detail="Cannot publish: Pricing calculation is required.")

    _update_workflow_step(product_id, "published", "product_published")
    return get_workflow_state(product_id, artisan_id=artisan_id)


def quick_assist_workflow(
    product_id: str,
    artisan_id: str,
    req: WorkflowQuickAssistRequest,
) -> WorkflowStateResponse:
    """
    Step 2: Voice-to-Catalog & AI Fair Pricing Assistant — powered by Orchestrator Agent.

    Flow:
      1. Orchestrator Agent analyses spoken text → produces rich brief for all agents
      2. Catalog Agent uses Orchestrator's detailed prompt → better title/description/keywords
      3. Pricing Agent uses Orchestrator's price intelligence → fairer suggested price
    """
    wf = _check_product_ownership(product_id, artisan_id)

    spoken = req.spoken_text.strip()
    product_name = wf.get("product_name") or "Artisanal Craft"

    # ── 1. ORCHESTRATOR: enrich raw artisan input into detailed agent briefs ──
    print(f"[WORKFLOW] Running Orchestrator Agent for product '{product_name}'…")
    brief = orchestrate(
        spoken_text=spoken,
        product_name=product_name,
        material=wf.get("initial_material", ""),
        language=req.language or "en",
        estimated_cost=req.estimated_cost,
        desired_price=req.desired_price,
    )
    print(f"[ORCHESTRATOR] Craft={brief.detected_craft_type}, Region={brief.detected_region}, "
          f"Segment={brief.primary_b2b_segment}, Price=₹{brief.suggested_price}")

    # ── 2. CATALOG AGENT: use Orchestrator's detailed prompt ─────────────────
    cat_req = CatalogRequest(
        product_id=product_id,
        product_name=product_name,
        language="en",
        details=ProductDetails(
            material=brief.detected_material,
            craft_type=brief.detected_craft_type,
            color="Natural Artisan Finish",
            purpose=brief.primary_b2b_segment,
        ),
    )

    # Pass the Orchestrator's catalog_prompt if available (richer output)
    if brief.catalog_prompt:
        generated = generate_catalog_with_prompt(cat_req, brief.catalog_prompt)
    else:
        generated = generate_catalog(cat_req)

    # Ensure english description is woven into catalog
    if brief.english_description and brief.english_description.lower() not in generated.description.lower():
        generated.description = f"{generated.description}\n\nArtisan's Story: {brief.english_description}"

    save_catalog(cat_req, generated)

    # ── 3. PRICING AGENT: use Orchestrator's price intelligence ──────────────
    base_material = req.estimated_cost or (brief.price_floor * 0.4)
    base_labor    = max(80.0, base_material * 0.6) if not req.desired_price else max(80.0, req.desired_price * 0.25)
    base_pack     = round(base_material * 0.08, 2)
    base_over     = round(base_material * 0.12, 2)
    base_ship     = 40.0

    pricing_req = PricingRequest(
        product_id=product_id,
        product_name=generated.product_title,
        material_cost=base_material,
        labor_cost=base_labor,
        packaging_cost=base_pack,
        overhead_cost=base_over,
        shipping_cost=base_ship,
        target_profit_margin_percent=28.0,
        marketplace_commission_percent=10.0,
        rounding_rule="round_nearest_rupee",
    )
    pricing_res = calculate_price(pricing_req)

    # Override with Orchestrator's smarter price if artisan gave a desired price
    # or if orchestrator's suggested price is significantly different
    if req.desired_price and req.desired_price > 0:
        pricing_res.suggested_selling_price = req.desired_price
    elif brief.suggested_price and brief.suggested_price > pricing_res.suggested_selling_price:
        pricing_res.suggested_selling_price = brief.suggested_price

    save_pricing_record(pricing_res)

    # ── 4. Store orchestrator brief in workflow doc for UI display ────────────
    database["product_workflows"].update_one(
        {"product_id": product_id},
        {"$set": {"orchestrator_brief": brief.to_dict()}}
    )

    _update_workflow_step(product_id, "catalog_pending", "quick_assist_generated")
    return get_workflow_state(product_id, artisan_id=artisan_id)


def single_approve_workflow(
    product_id: str,
    artisan_id: str,
    req: WorkflowSingleApproveRequest,
) -> WorkflowStateResponse:
    """
    Step 2 -> 3: Artisan one-click approval & edit.
    Saves artisan's approved title, story, price, and stock, then publishes straight to B2B market.
    """
    _check_product_ownership(product_id, artisan_id)

    # 1. Save artisan-edited catalog
    safe_description = req.description.strip() if req.description and len(req.description.strip()) >= 5 else f"Handcrafted {req.product_title} — authentic artisan product."
    safe_keywords = req.keywords if req.keywords else ["handmade", "artisan", "b2b wholesale"]
    # Ensure minimum 3 keywords for catalog schema
    while len(safe_keywords) < 3:
        safe_keywords.append("handcrafted")

    save_req = CatalogManualSaveRequest(
        product_id=product_id,
        product_name=req.product_title,
        product_title=req.product_title,
        keywords=safe_keywords,
        description=safe_description,
        language="en",
        details=ProductDetails(
            material=req.material,
            craft_type=req.craft_type or "Handcrafted",
            color="Natural",
            purpose="Commercial Wholesale & Retail",
        ),
    )
    save_manual_catalog(save_req)

    # 2. Save approved pricing record
    target_price = float(req.suggested_price)
    est_cost = round(target_price * 0.65, 2)
    pricing_req = PricingRequest(
        product_id=product_id,
        product_name=req.product_title,
        material_cost=round(est_cost * 0.55, 2),
        labor_cost=round(est_cost * 0.35, 2),
        packaging_cost=round(est_cost * 0.05, 2),
        overhead_cost=round(est_cost * 0.05, 2),
        shipping_cost=0.0,
        target_profit_margin_percent=25.0,
        marketplace_commission_percent=10.0,
        rounding_rule="round_nearest_rupee",
    )
    pricing_res = calculate_price(pricing_req)
    # Set explicit approved selling price
    pricing_res.suggested_selling_price = target_price
    pricing_res.estimated_profit = round(target_price - est_cost - (target_price * 0.10), 2)
    save_pricing_record(pricing_res)

    # 3. Configure inventory for B2B buyer ordering
    inv_data = ArtisanInventory(
        product_id=product_id,
        artisan_id=artisan_id,
        available_quantity=req.available_quantity,
        production_capacity_per_month=max(50, req.available_quantity * 3),
        minimum_order_quantity=req.minimum_order_quantity,
        production_lead_time_days=10,
        location=req.location,
    )
    save_artisan_inventory(inv_data)

    # 4. Mark published to B2B
    _update_workflow_step(product_id, "published", "product_published")
    return get_workflow_state(product_id, artisan_id=artisan_id)


def _check_product_ownership(product_id: str, artisan_id: str) -> dict[str, Any]:
    """Helper verifying that product belongs to the artisan (or admin)."""
    doc = database["product_workflows"].find_one({"product_id": product_id})
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Product workflow '{product_id}' not found.")
    if artisan_id != "admin" and doc.get("artisan_id") != artisan_id:
        raise HTTPException(status_code=403, detail="You do not own this product.")
    return doc


def _update_workflow_step(product_id: str, new_status: WorkflowStatus, step_name: str) -> None:
    """Helper updating workflow step list, status, and updated_at timestamp."""
    col = database["product_workflows"]
    now = datetime.now(timezone.utc)
    col.update_one(
        {"product_id": product_id},
        {
            "$set": {
                "workflow_status": new_status,
                "updated_at": now,
            },
            "$addToSet": {"steps_completed": step_name},
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Product Variations
# ─────────────────────────────────────────────────────────────────────────────

def save_product_variations(
    product_id: str,
    artisan_id: str,
    req: ProductVariationUpsert,
) -> list[dict]:
    """Save (replace) all variations for a product. Returns the saved list."""
    _check_product_ownership(product_id, artisan_id)

    now = datetime.now(timezone.utc)
    variations = []
    for v in req.variations:
        vid = v.variation_id.strip() if v.variation_id else f"VAR-{uuid4().hex[:6].upper()}"
        variations.append({
            "variation_id":    vid,
            "variation_type":  v.variation_type,
            "label":           v.label,
            "price_adjustment": v.price_adjustment,
            "available_quantity": v.available_quantity,
            "emoji":           v.emoji,
        })

    database["product_workflows"].update_one(
        {"product_id": product_id},
        {"$set": {"variations": variations, "updated_at": now}},
    )
    return variations


def get_product_variations(product_id: str) -> list[dict]:
    """Return all saved variations for a product."""
    doc = database["product_workflows"].find_one({"product_id": product_id}, {"variations": 1})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    return doc.get("variations") or []


def delete_product_variation(product_id: str, artisan_id: str, variation_id: str) -> list[dict]:
    """Remove a single variation by ID and return the remaining list."""
    _check_product_ownership(product_id, artisan_id)
    now = datetime.now(timezone.utc)
    database["product_workflows"].update_one(
        {"product_id": product_id},
        {
            "$pull":  {"variations": {"variation_id": variation_id}},
            "$set":   {"updated_at": now},
        },
    )
    return get_product_variations(product_id)
