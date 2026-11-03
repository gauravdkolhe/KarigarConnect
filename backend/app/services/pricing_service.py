
from decimal import Decimal, ROUND_HALF_UP
import math
from typing import Sequence

from backend.app.schemas.pricing import (
    CompetitorMarketAnalysis,
    CompetitorObservation,
    CostBreakdown,
    FeeBreakdown,
    PricingRequest,
    PricingResponse,
    PricingScenarioItem,
    PricingScenarioRequest,
    PricingScenarioResponse,
)


def _to_decimal(value: float | int | str | Decimal) -> Decimal:
    """Convert a numeric input to Decimal safely."""
    return Decimal(str(value))


def _round_currency(value: Decimal) -> float:
    """Round a Decimal to standard 2-decimal currency float."""
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def analyze_competitors(
    observations: Sequence[CompetitorObservation] | None,
    recommended_price: float,
    total_cost: float,
    currency: str = "INR",
) -> tuple[CompetitorMarketAnalysis, list[str]]:
    """
    Perform deterministic statistical analysis on supplied competitor observations.
    Never fabricates data; returns explicit disclaimers if no data is provided.
    """
    warnings: list[str] = []

    if not observations:
        analysis = CompetitorMarketAnalysis(
            market_data_available=False,
            observation_count=0,
            notes=[
                "No competitor observations provided. Price is based strictly on cost and margin parameters."
            ],
        )
        return analysis, warnings

    prices = sorted([obs.price for obs in observations])
    count = len(prices)
    min_p = prices[0]
    max_p = prices[-1]

    # Calculate median
    if count % 2 == 1:
        median_p = prices[count // 2]
    else:
        median_p = round((prices[count // 2 - 1] + prices[count // 2]) / 2.0, 2)

    # Position relative to median (5% band)
    if recommended_price < median_p * 0.95:
        position = "below_competitor_median"
        label = "Below observed competitor median"
    elif recommended_price > median_p * 1.05:
        position = "above_competitor_median"
        label = "Above observed competitor median"
    else:
        position = "near_competitor_median"
        label = "Near observed competitor median"

    notes = [
        f"Evaluated {count} valid competitor observation(s) in {currency}.",
        "Competitor prices are contextual and do not guarantee market demand, quality equivalence, or sales velocity.",
    ]

    # Warnings for edge cases
    if recommended_price > max_p:
        warning_msg = (
            f"Recommended price ({currency} {recommended_price:.2f}) exceeds the highest observed competitor price "
            f"({currency} {max_p:.2f}). Artisan storytelling, premium materials, or custom branding may be required."
        )
        warnings.append(warning_msg)
        notes.append(warning_msg)

    if median_p < total_cost:
        warning_msg = (
            f"Observed competitor median ({currency} {median_p:.2f}) is below your direct production cost "
            f"({currency} {total_cost:.2f}). Matching competitor median would generate a financial loss."
        )
        warnings.append(warning_msg)
        notes.append(warning_msg)

    analysis = CompetitorMarketAnalysis(
        market_data_available=True,
        observation_count=count,
        min_price=min_p,
        max_price=max_p,
        median_price=median_p,
        price_position=position,
        position_label=label,
        notes=notes,
    )

    return analysis, warnings


def apply_rounding_strategy(
    required_price: Decimal,
    strategy: str,
) -> Decimal:
    """
    Apply configured rounding strategy without violating target margin.
    Guarantees final_price >= required_price.
    """
    if strategy == "round_nearest_rupee":
        p_float = float(required_price)
        rounded_int = round(p_float)
        # Never round down below required minimum price
        if Decimal(str(rounded_int)) < required_price:
            rounded_int = math.ceil(p_float)
        return Decimal(str(rounded_int))

    elif strategy == "psychological_99":
        p_float = float(required_price)
        base_hundred = math.floor(p_float / 100.0) * 100.0
        candidate = base_hundred + 99.0
        if candidate < p_float:
            candidate += 100.0
        return Decimal(str(round(candidate, 2)))

    # Default: "exact" (2 decimal places)
    return required_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_price(request: PricingRequest) -> PricingResponse:
    """
    Calculate a transparent, explainable selling price using deterministic arithmetic.
    
    Formulation:
      Base Production Cost (B) = material + labor + packaging + overhead + other_variable
      Total Seller Cost (C) = Base Cost + shipping
      Commission Rate (c) = marketplace_commission_percent / 100
      Discount Rate (d) = discount_percent / 100
      Target Margin (m) = target_profit_margin_percent / 100

      Transaction Revenue (P_trans) is the price paid by customer after discount:
        P_trans = C / (1 - c - m)
      Listing / Selling Price (P_list):
        P_list = P_trans / (1 - d)
      
      Marketplace Commission Amount = P_trans * c
      Net Artisan Revenue = P_trans - Commission Amount
      Estimated Profit = Net Artisan Revenue - C
      Actual Profit Margin = (Estimated Profit / P_trans) * 100
    """
    warnings: list[str] = []

    mat = _to_decimal(request.material_cost)
    lab = _to_decimal(request.labor_cost)
    pkg = _to_decimal(request.packaging_cost)
    ovh = _to_decimal(request.overhead_cost)
    oth = _to_decimal(request.other_variable_costs)
    shp = _to_decimal(request.shipping_cost)

    base_production_cost = mat + lab + pkg + ovh + oth
    total_seller_cost = base_production_cost + shp

    # Zero-cost edge case
    if total_seller_cost == Decimal("0"):
        warnings.append("Total cost is zero; price set to zero.")
        cost_breakdown = CostBreakdown(
            material_cost=float(mat),
            labor_cost=float(lab),
            packaging_cost=float(pkg),
            overhead_cost=float(ovh),
            shipping_cost=float(shp),
            other_variable_costs=float(oth),
            base_production_cost=0.0,
            total_seller_cost=0.0,
        )
        fee_breakdown = FeeBreakdown()
        comp_analysis, comp_warnings = analyze_competitors(
            request.competitor_prices, 0.0, 0.0, request.currency
        )
        warnings.extend(comp_warnings)

        return PricingResponse(
            product_id=request.product_id,
            product_name=request.product_name,
            material_cost=float(mat),
            labor_cost=float(lab),
            packaging_cost=float(pkg),
            overhead_cost=float(ovh),
            shipping_cost=float(shp),
            other_variable_costs=float(oth),
            total_cost=0.0,
            target_profit_margin_percent=request.target_profit_margin_percent,
            suggested_selling_price=0.0,
            discounted_price=None,
            estimated_profit=0.0,
            estimated_profit_margin_percent=0.0,
            currency=request.currency,
            pricing_method="cost_plus_target_margin",
            pricing_strategy=request.pricing_strategy,
            requires_market_validation=True,
            cost_breakdown=cost_breakdown,
            fee_breakdown=fee_breakdown,
            competitor_analysis=comp_analysis,
            explanation="Total cost is ₹0.00. No commercial price could be computed.",
            warnings=warnings,
        )

    m = _to_decimal(request.target_profit_margin_percent) / Decimal("100")
    c = _to_decimal(request.marketplace_commission_percent) / Decimal("100")
    d = _to_decimal(request.discount_percent) / Decimal("100")

    denominator = Decimal("1") - c - m
    if denominator <= Decimal("0"):
        raise ValueError(
            f"Impossible pricing model: marketplace commission ({request.marketplace_commission_percent}%) + "
            f"target profit margin ({request.target_profit_margin_percent}%) >= 100%. "
            f"Deductions exceed selling revenue."
        )

    # Required transaction price to clear margin m
    required_transaction_price = total_seller_cost / denominator

    # Required listing price before discount
    if d > Decimal("0"):
        required_listing_price = required_transaction_price / (Decimal("1") - d)
    else:
        required_listing_price = required_transaction_price

    # Apply Rounding Strategy
    final_listing_price = apply_rounding_strategy(
        required_listing_price,
        request.pricing_strategy,
    )

    # Compute realized transaction price based on final rounded listing price
    if d > Decimal("0"):
        realized_trans_price = (final_listing_price * (Decimal("1") - d)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        discount_amount = (final_listing_price - realized_trans_price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        realized_trans_price = final_listing_price
        discount_amount = Decimal("0.00")

    # Marketplace commission
    commission_amount = (realized_trans_price * c).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Net artisan revenue before production costs
    net_artisan_revenue = realized_trans_price - commission_amount

    # Net monetary profit
    estimated_profit = (net_artisan_revenue - total_seller_cost).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Realized profit margin on final transaction price
    actual_margin_percent = (
        (estimated_profit / realized_trans_price) * Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Tax calculation (statutory pass-through)
    tax_amount = Decimal("0.00")
    if request.tax_rate_percent is not None and request.tax_rate_percent > 0:
        t = _to_decimal(request.tax_rate_percent) / Decimal("100")
        if request.tax_inclusive:
            pre_tax = realized_trans_price / (Decimal("1") + t)
            tax_amount = (realized_trans_price - pre_tax).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            tax_amount = (realized_trans_price * t).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

    cost_breakdown = CostBreakdown(
        material_cost=_round_currency(mat),
        labor_cost=_round_currency(lab),
        packaging_cost=_round_currency(pkg),
        overhead_cost=_round_currency(ovh),
        shipping_cost=_round_currency(shp),
        other_variable_costs=_round_currency(oth),
        base_production_cost=_round_currency(base_production_cost),
        total_seller_cost=_round_currency(total_seller_cost),
    )

    fee_breakdown = FeeBreakdown(
        marketplace_commission_percent=request.marketplace_commission_percent,
        marketplace_commission_amount=_round_currency(commission_amount),
        discount_percent=request.discount_percent,
        discount_amount=_round_currency(discount_amount),
        tax_rate_percent=request.tax_rate_percent,
        tax_amount=_round_currency(tax_amount),
        tax_inclusive=request.tax_inclusive,
    )

    # Competitor analysis
    comp_analysis, comp_warnings = analyze_competitors(
        request.competitor_prices,
        _round_currency(final_listing_price),
        _round_currency(total_seller_cost),
        currency=request.currency,
    )
    warnings.extend(comp_warnings)

    # Construct deterministic human-readable explanation
    explanation_parts = [
        f"Product: {request.product_name} ({request.product_id})",
        f"1. Base Production Cost: {request.currency} {_round_currency(base_production_cost):.2f} "
        f"(Material: {_round_currency(mat):.2f}, Labor: {_round_currency(lab):.2f}, "
        f"Packaging: {_round_currency(pkg):.2f}, Overhead: {_round_currency(ovh):.2f}, Other: {_round_currency(oth):.2f}).",
    ]
    if float(shp) > 0:
        explanation_parts.append(
            f"2. Direct Shipping & Fulfillment: {request.currency} {_round_currency(shp):.2f}."
        )
    explanation_parts.append(
        f"3. Total Direct Seller Cost: {request.currency} {_round_currency(total_seller_cost):.2f}."
    )
    if request.marketplace_commission_percent > 0:
        explanation_parts.append(
            f"4. Marketplace Commission: {request.marketplace_commission_percent}% "
            f"({request.currency} {_round_currency(commission_amount):.2f} on realized transaction)."
        )
    if request.discount_percent > 0:
        explanation_parts.append(
            f"5. Promotional Discount: {request.discount_percent}% "
            f"(Listing: {request.currency} {_round_currency(final_listing_price):.2f} -> "
            f"Realized: {request.currency} {_round_currency(realized_trans_price):.2f})."
        )
    explanation_parts.append(
        f"6. Target Margin: {request.target_profit_margin_percent}% | "
        f"Actual Achieved Margin: {float(actual_margin_percent):.2f}%."
    )
    explanation_parts.append(
        f"7. Estimated Artisan Profit: {request.currency} {_round_currency(estimated_profit):.2f} per unit."
    )
    if request.tax_rate_percent:
        treatment = "inclusive" if request.tax_inclusive else "exclusive"
        explanation_parts.append(
            f"8. Statutory Tax Estimate: {request.tax_rate_percent}% ({treatment}, "
            f"{request.currency} {_round_currency(tax_amount):.2f}). Tax is not seller profit."
        )
    if comp_analysis.market_data_available:
        explanation_parts.append(
            f"9. Market Position: {comp_analysis.position_label} "
            f"(Median: {request.currency} {comp_analysis.median_price:.2f})."
        )

    explanation = "\n".join(explanation_parts)

    return PricingResponse(
        product_id=request.product_id,
        product_name=request.product_name,
        material_cost=_round_currency(mat),
        labor_cost=_round_currency(lab),
        packaging_cost=_round_currency(pkg),
        overhead_cost=_round_currency(ovh),
        shipping_cost=_round_currency(shp),
        other_variable_costs=_round_currency(oth),
        total_cost=_round_currency(total_seller_cost),
        target_profit_margin_percent=request.target_profit_margin_percent,
        suggested_selling_price=_round_currency(final_listing_price),
        discounted_price=_round_currency(realized_trans_price) if request.discount_percent > 0 else None,
        estimated_profit=_round_currency(estimated_profit),
        estimated_profit_margin_percent=float(actual_margin_percent),
        currency=request.currency,
        pricing_method="cost_plus_target_margin",
        pricing_strategy=request.pricing_strategy,
        requires_market_validation=True,
        cost_breakdown=cost_breakdown,
        fee_breakdown=fee_breakdown,
        competitor_analysis=comp_analysis,
        explanation=explanation,
        warnings=warnings,
    )


def calculate_scenarios(request: PricingScenarioRequest) -> PricingScenarioResponse:
    """
    Evaluate multiple target profit margin scenarios against identical cost structures.
    """
    scenarios: list[PricingScenarioItem] = []

    names = ["Conservative Margin", "Standard Margin", "Growth / Premium Margin"]

    for idx, target_margin in enumerate(request.target_profit_margins):
        scenario_name = names[idx] if idx < len(names) else f"Scenario {idx + 1}"

        single_req = PricingRequest(
            product_id=request.product_id,
            product_name=request.product_name,
            material_cost=request.material_cost,
            labor_cost=request.labor_cost,
            packaging_cost=request.packaging_cost,
            overhead_cost=request.overhead_cost,
            shipping_cost=request.shipping_cost,
            other_variable_costs=request.other_variable_costs,
            target_profit_margin_percent=target_margin,
            marketplace_commission_percent=request.marketplace_commission_percent,
            discount_percent=request.discount_percent,
            tax_rate_percent=request.tax_rate_percent,
            tax_inclusive=request.tax_inclusive,
            pricing_strategy=request.pricing_strategy,
            competitor_prices=request.competitor_prices,
            currency=request.currency,
        )

        res = calculate_price(single_req)

        meets_margin = res.estimated_profit_margin_percent >= (target_margin - 0.05)

        item = PricingScenarioItem(
            scenario_name=f"{scenario_name} ({target_margin}%)",
            target_profit_margin_percent=target_margin,
            suggested_selling_price=res.suggested_selling_price,
            discounted_price=res.discounted_price,
            total_seller_cost=res.total_cost,
            marketplace_commission_amount=(
                res.fee_breakdown.marketplace_commission_amount
                if res.fee_breakdown
                else 0.0
            ),
            shipping_cost=res.shipping_cost,
            tax_amount=(
                res.fee_breakdown.tax_amount if res.fee_breakdown else 0.0
            ),
            estimated_profit=res.estimated_profit,
            actual_profit_margin_percent=res.estimated_profit_margin_percent,
            meets_target_margin=meets_margin,
            warnings=res.warnings,
        )
        scenarios.append(item)

    # Shared cost breakdown
    mat = _to_decimal(request.material_cost)
    lab = _to_decimal(request.labor_cost)
    pkg = _to_decimal(request.packaging_cost)
    ovh = _to_decimal(request.overhead_cost)
    oth = _to_decimal(request.other_variable_costs)
    shp = _to_decimal(request.shipping_cost)
    base_cost = mat + lab + pkg + ovh + oth
    total_cost = base_cost + shp

    cost_summary = CostBreakdown(
        material_cost=_round_currency(mat),
        labor_cost=_round_currency(lab),
        packaging_cost=_round_currency(pkg),
        overhead_cost=_round_currency(ovh),
        shipping_cost=_round_currency(shp),
        other_variable_costs=_round_currency(oth),
        base_production_cost=_round_currency(base_cost),
        total_seller_cost=_round_currency(total_cost),
    )

    explanation = (
        f"Compared {len(scenarios)} target margin scenarios for '{request.product_name}'. "
        f"Direct seller costs remain constant at {request.currency} {_round_currency(total_cost):.2f} across all options."
    )

    return PricingScenarioResponse(
        product_id=request.product_id,
        product_name=request.product_name,
        currency=request.currency,
        cost_summary=cost_summary,
        scenarios=scenarios,
        explanation=explanation,
    )
