from datetime import datetime, timezone
import math
import re
from typing import Any
from uuid import uuid4

from backend.app.database.connection import database
from backend.app.schemas.market_linkage import (
    ArtisanInventory,
    ArtisanProductProfile,
    MatchCompatibility,
    MatchScoreBreakdown,
    ProductMatchResult,
    ProductMatchesResponse,
    BuyerMatchesResponse,
)
from backend.app.services.buyer_service import (
    get_buyer_requirement,
    list_buyer_requirements,
    mask_contact_email,
    mask_contact_phone,
)
from backend.app.services.inventory_service import get_artisan_product_profile

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "it", "this", "that", "these", "those",
    "product", "item", "handmade", "handcrafted", "artisan", "buy", "require",
}


def _tokenize(text: str) -> set[str]:
    """Tokenize, lowercase, and remove non-alphanumeric punctuation and basic stopwords."""
    if not text:
        return set()
    words = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
    return {w for w in words if w not in STOPWORDS}


def _calculate_text_similarity(artisan_tokens: set[str], buyer_tokens: set[str]) -> float:
    """Calculate normalized token overlap ratio (0.0 to 1.0)."""
    if not artisan_tokens or not buyer_tokens:
        return 0.0
    intersection = artisan_tokens.intersection(buyer_tokens)
    if not intersection:
        return 0.0
    # Overlap relative to the smaller set (ensures focused requirement matches comprehensive listing)
    overlap_ratio = len(intersection) / min(len(artisan_tokens), len(buyer_tokens))
    return min(1.0, overlap_ratio)


def evaluate_match(
    product: ArtisanProductProfile,
    requirement: dict[str, Any],
) -> ProductMatchResult:
    """
    Deterministically evaluate the compatibility between an artisan product
    and an active buyer requirement across 8 business dimensions.
    """
    warnings: list[str] = []

    # -------------------------------------------------------------
    # 1. Category Matching (Max 20 points)
    # -------------------------------------------------------------
    req_cat = (requirement.get("required_category") or "").strip().lower()
    prod_cat = product.category.strip().lower()
    prod_text_full = f"{product.product_name} {product.product_title} {product.description}".lower()

    if req_cat and prod_cat and req_cat == prod_cat:
        category_score = 20.0
        cat_compat = True
    elif req_cat in prod_text_full:
        category_score = 15.0
        cat_compat = True
    elif any(token in prod_text_full for token in req_cat.split()):
        category_score = 10.0
        cat_compat = True
    else:
        category_score = 0.0
        cat_compat = False
        warnings.append(
            f"Category difference: Buyer requires '{requirement.get('required_category')}' "
            f"while product is categorized under '{product.category}'."
        )

    # -------------------------------------------------------------
    # 2. Keyword & Text Similarity (Max 20 points)
    # -------------------------------------------------------------
    artisan_words = _tokenize(
        f"{product.product_name} {product.product_title} {product.description} "
        f"{' '.join(product.keywords)} {product.material} {product.craft_type or ''}"
    )

    buyer_words = _tokenize(
        f"{requirement.get('requirement_title', '')} {requirement.get('description', '')} "
        f"{' '.join(requirement.get('required_keywords', []))} {req_cat}"
    )

    overlap = _calculate_text_similarity(artisan_words, buyer_words)
    keyword_score = round(min(20.0, overlap * 20.0 * 1.5), 2)

    # -------------------------------------------------------------
    # 3. Material Compatibility (Max 15 points)
    # -------------------------------------------------------------
    pref_materials = [m.lower().strip() for m in requirement.get("preferred_materials", [])]
    prod_material = product.material.lower().strip()

    if not pref_materials:
        material_score = 15.0
        mat_compat = True
    elif any(pm in prod_material or prod_material in pm for pm in pref_materials):
        material_score = 15.0
        mat_compat = True
    elif any(set(pm.split()).intersection(set(prod_material.split())) for pm in pref_materials):
        material_score = 10.0
        mat_compat = True
    else:
        material_score = 0.0
        mat_compat = False
        warnings.append(
            f"Material mismatch: Buyer prefers {', '.join(requirement.get('preferred_materials', []))}, "
            f"artisan crafts with '{product.material}'."
        )

    # -------------------------------------------------------------
    # 4. Craft-Type Compatibility (Max 10 points)
    # -------------------------------------------------------------
    pref_crafts = [c.lower().strip() for c in requirement.get("preferred_craft_types", [])]
    prod_craft = (product.craft_type or "").lower().strip()

    if not pref_crafts:
        craft_score = 10.0
        craft_compat = True
    elif prod_craft and any(pc in prod_craft or prod_craft in pc for pc in pref_crafts):
        craft_score = 10.0
        craft_compat = True
    elif any(pc in prod_text_full for pc in pref_crafts):
        craft_score = 8.0
        craft_compat = True
    else:
        craft_score = 0.0
        craft_compat = False
        warnings.append(
            f"Craft style mismatch: Buyer prefers {', '.join(requirement.get('preferred_craft_types', []))}."
        )

    # -------------------------------------------------------------
    # 5. Price & Budget Compatibility (Max 15 points)
    # -------------------------------------------------------------
    req_currency = requirement.get("currency", "INR")
    unit_price = product.unit_price
    min_budget = float(requirement.get("minimum_budget", 0.0))
    max_budget = float(requirement.get("maximum_budget", 0.0))

    if req_currency.upper() != product.currency.upper():
        price_score = 0.0
        budget_compat = False
        warnings.append(
            f"Currency mismatch: Product is priced in {product.currency}, but buyer specified {req_currency}."
        )
    elif unit_price <= 0:
        price_score = 0.0
        budget_compat = False
        warnings.append("Artisan product has no valid pricing record.")
    elif unit_price <= max_budget:
        if unit_price >= min_budget:
            price_score = 15.0
        else:
            # Below minimum expected budget (favorable to buyer)
            price_score = 13.0
        budget_compat = True
    else:
        # Unit price exceeds buyer's maximum budget
        pct_over = ((unit_price - max_budget) / max_budget) * 100.0
        if pct_over <= 10.0:
            price_score = 5.0
            budget_compat = False
            warnings.append(
                f"Slight budget stretch: Artisan price ({product.currency} {unit_price:.2f}) is "
                f"{pct_over:.1f}% above buyer ceiling ({req_currency} {max_budget:.2f})."
            )
        else:
            price_score = 0.0
            budget_compat = False
            warnings.append(
                f"Budget mismatch: Artisan unit price ({product.currency} {unit_price:.2f}) "
                f"substantially exceeds buyer maximum budget ({req_currency} {max_budget:.2f})."
            )

    # -------------------------------------------------------------
    # 6. Quantity Feasibility (Max 10 points)
    # -------------------------------------------------------------
    req_qty = int(requirement.get("required_quantity", 1))
    avail_qty = product.available_quantity
    monthly_cap = product.production_capacity
    lead_days = product.production_lead_time_days
    deadline_days = int(requirement.get("delivery_deadline_days", 30))

    if avail_qty >= req_qty:
        quantity_score = 10.0
        qty_compat = True
    else:
        # Check production over deadline
        months_available = max(0.2, deadline_days / 30.0)
        potential_units = avail_qty + int(monthly_cap * months_available)
        if potential_units >= req_qty:
            quantity_score = 7.0
            qty_compat = True
            warnings.append(
                f"Quantity condition: Ready stock is {avail_qty} units (buyer needs {req_qty}). "
                f"Fulfillment requires crafting over {deadline_days} days at capacity {monthly_cap}/mo."
            )
        else:
            quantity_score = 0.0
            qty_compat = False
            warnings.append(
                f"Capacity shortfall: Buyer requested {req_qty} units. "
                f"Artisan ready stock ({avail_qty}) + production capacity can only produce ~{potential_units} units."
            )

    # -------------------------------------------------------------
    # 7. Delivery-Time Compatibility (Max 5 points)
    # -------------------------------------------------------------
    if avail_qty >= req_qty:
        # In stock, ready to dispatch
        delivery_score = 5.0
        delivery_compat = True
    elif lead_days <= deadline_days:
        delivery_score = 5.0
        delivery_compat = True
    else:
        delivery_score = 0.0
        delivery_compat = False
        warnings.append(
            f"Delivery infeasible: Production lead time ({lead_days} days) exceeds buyer deadline ({deadline_days} days)."
        )

    # -------------------------------------------------------------
    # 8. Location Compatibility (Max 5 points)
    # -------------------------------------------------------------
    b_loc = (requirement.get("delivery_location") or "").lower()
    a_loc = product.location.lower()

    if any(term in b_loc for term in ["india", "pan india", "all india"]) or any(
        term in a_loc for term in ["india", "pan india", "all india"]
    ):
        location_score = 5.0
        loc_compat = True
    elif b_loc in a_loc or a_loc in b_loc:
        location_score = 5.0
        loc_compat = True
    else:
        # Inter-city / inter-state domestic logistics
        location_score = 4.0
        loc_compat = True

    # -------------------------------------------------------------
    # Total Score Calculation & Categorization
    # -------------------------------------------------------------
    total_score = round(
        category_score
        + keyword_score
        + material_score
        + craft_score
        + price_score
        + quantity_score
        + delivery_score
        + location_score,
        2,
    )

    # Evaluate classification
    has_hard_budget_fail = not budget_compat and price_score == 0.0
    has_hard_category_fail = not cat_compat and keyword_score < 4.0

    if has_hard_budget_fail or has_hard_category_fail or req_currency.upper() != product.currency.upper():
        category_label = "Not eligible"
        recommendation = (
            "Not eligible for immediate transaction due to fundamental category, currency, "
            "or severe budget mismatch."
        )
    elif total_score >= 80.0 and cat_compat and budget_compat and qty_compat:
        category_label = "Excellent"
        recommendation = (
            "Strong mutual match across category, materials, budget, and quantity. "
            "Proceed with direct outreach and sample submission."
        )
    elif total_score >= 65.0 and cat_compat and budget_compat:
        category_label = "Good"
        recommendation = (
            "Solid commercial opportunity. Check specific specifications and delivery terms before quotation."
        )
    elif total_score >= 50.0 and budget_compat:
        category_label = "Moderate"
        recommendation = (
            "Moderate alignment. Product can fulfill buyer requirement with minor adjustments."
        )
    elif not qty_compat or not delivery_compat or price_score == 5.0:
        category_label = "Conditional"
        recommendation = (
            "Conditional opportunity. Confirm artisan production schedule, batch size, or price negotiation."
        )
    else:
        category_label = "Not eligible"
        recommendation = "Low compatibility. Not recommended for primary outreach."

    # Buyer summary with masked contact
    buyer_summary = {
        "buyer_id": requirement.get("buyer_id"),
        "buyer_name": requirement.get("buyer_name"),
        "buyer_type": requirement.get("buyer_type"),
        "delivery_location": requirement.get("delivery_location"),
        "required_quantity": req_qty,
        "budget_range": f"{req_currency} {min_budget:,.2f} - {max_budget:,.2f}",
        "delivery_deadline_days": deadline_days,
        "contact_email_masked": mask_contact_email(requirement.get("contact_email")),
        "contact_phone_masked": mask_contact_phone(requirement.get("contact_phone")),
    }

    artisan_summary = {
        "product_id": product.product_id,
        "product_title": product.product_title,
        "unit_price": f"{product.currency} {product.unit_price:.2f}",
        "material": product.material,
        "craft_type": product.craft_type,
        "available_quantity": product.available_quantity,
        "monthly_capacity": product.production_capacity,
        "lead_time_days": product.production_lead_time_days,
    }

    match_id = f"MATCH-{uuid4().hex[:10].upper()}"

    return ProductMatchResult(
        match_id=match_id,
        product_id=product.product_id,
        requirement_id=requirement.get("requirement_id", "REQ-UNKNOWN"),
        product_title=product.product_title,
        buyer_name=requirement.get("buyer_name", "Unknown Buyer"),
        buyer_type=requirement.get("buyer_type", "Other business"),
        match_score=total_score,
        match_category=category_label,
        compatibility=MatchCompatibility(
            category=cat_compat,
            material=mat_compat,
            craft_type=craft_compat,
            budget=budget_compat,
            quantity=qty_compat,
            delivery=delivery_compat,
            location=loc_compat,
        ),
        score_breakdown=MatchScoreBreakdown(
            category_score=category_score,
            keyword_score=keyword_score,
            material_score=material_score,
            craft_type_score=craft_score,
            price_score=price_score,
            quantity_score=quantity_score,
            location_score=location_score,
            delivery_score=delivery_score,
            total_score=total_score,
        ),
        warnings=warnings,
        recommendation=recommendation,
        buyer_summary=buyer_summary,
        artisan_summary=artisan_summary,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def find_matches_for_product(
    product_id: str,
    min_score: float = 40.0,
    max_results: int = 20,
    status: str = "active",
    category_filter: str | None = None,
    inventory_override: ArtisanInventory | None = None,
) -> ProductMatchesResponse:
    """
    Find matching genuine buyer requirements for an artisan product.
    Only evaluates genuine active requirements in MongoDB.
    """
    profile, warnings = get_artisan_product_profile(product_id, inventory_override)
    if profile is None:
        raise ValueError(f"Product '{product_id}' not found in catalog. Create product catalog first.")

    # Retrieve real buyer requirements from MongoDB
    requirements, _ = list_buyer_requirements(
        status=status,
        category=category_filter,
        limit=100,
        mask_contact=False,  # Evaluates genuine data; masking applied in buyer_summary
    )

    matches: list[ProductMatchResult] = []
    for req in requirements:
        result = evaluate_match(profile, req)
        if result.match_score >= min_score:
            # Propagate profile setup warnings (e.g. unpriced)
            if warnings:
                result.warnings.extend([w for w in warnings if w not in result.warnings])
            matches.append(result)

    # Sort descending by match_score
    matches.sort(key=lambda m: m.match_score, reverse=True)
    matches = matches[:max_results]

    return ProductMatchesResponse(
        product_id=product_id,
        product_title=profile.product_title,
        total_matches=len(matches),
        matches=matches,
    )


def find_matches_for_buyer(
    requirement_id: str,
    min_score: float = 40.0,
    max_results: int = 20,
) -> BuyerMatchesResponse:
    """
    Find matching artisan products for a genuine buyer requirement.
    Scans existing catalog products and compares them deterministically.
    """
    req_doc = get_buyer_requirement(requirement_id, mask_contact=False)
    if req_doc is None:
        raise ValueError(f"Buyer requirement '{requirement_id}' not found.")

    # Find existing catalog products
    catalogs = list(database["product_catalogs"].find({}, {"product_id": 1}).limit(100))

    matches: list[ProductMatchResult] = []
    for cat in catalogs:
        pid = cat["product_id"]
        profile, warnings = get_artisan_product_profile(pid)
        if profile is not None:
            res = evaluate_match(profile, req_doc)
            if res.match_score >= min_score:
                matches.append(res)

    matches.sort(key=lambda m: m.match_score, reverse=True)
    matches = matches[:max_results]

    return BuyerMatchesResponse(
        requirement_id=requirement_id,
        requirement_title=req_doc.get("requirement_title", requirement_id),
        total_matches=len(matches),
        matches=matches,
    )


def persist_match_result(match: ProductMatchResult) -> dict[str, Any]:
    """Optional persistence of an agreed or evaluated match record into MongoDB."""
    collection = database["market_linkage_matches"]
    now = datetime.now(timezone.utc)

    doc = match.model_dump()
    doc["created_at"] = now

    collection.insert_one(doc)
    doc.pop("_id", None)
    doc["created_at"] = now.isoformat()
    return doc
