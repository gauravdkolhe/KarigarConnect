
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class CompetitorObservation(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    price: float = Field(
        ...,
        gt=0,
        le=10_000_000,
        description="Observed selling price of a comparable product.",
    )
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=10,
        description="ISO currency code (default: INR).",
    )
    source: str | None = Field(
        default=None,
        max_length=255,
        description="Authorized source name, seller, or URL.",
    )
    observation_date: str | None = Field(
        default=None,
        max_length=50,
        description="Observation date formatted as YYYY-MM-DD.",
    )
    product_similarity: str | None = Field(
        default=None,
        max_length=255,
        description="Notes regarding material, size, or quality similarity.",
    )
    is_verified: bool = Field(
        default=False,
        description="Whether the observed price has been verified.",
    )


class CompetitorMarketAnalysis(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    market_data_available: bool = Field(
        default=False,
        description="Indicates whether valid competitor price observations were provided.",
    )
    observation_count: int = Field(
        default=0,
        ge=0,
        description="Number of valid competitor price observations evaluated.",
    )
    min_price: float | None = Field(
        default=None,
        description="Lowest observed competitor price.",
    )
    max_price: float | None = Field(
        default=None,
        description="Highest observed competitor price.",
    )
    median_price: float | None = Field(
        default=None,
        description="Median observed competitor price.",
    )
    price_position: str | None = Field(
        default=None,
        description="Machine identifier: below_competitor_median, near_competitor_median, or above_competitor_median.",
    )
    position_label: str | None = Field(
        default=None,
        description="Human-readable market positioning summary.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Informational notes and disclaimers on competitor data.",
    )


class CostBreakdown(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    material_cost: float = Field(description="Raw materials cost in specified currency.")
    labor_cost: float = Field(description="Artisan labor cost in specified currency.")
    packaging_cost: float = Field(description="Packaging materials cost.")
    overhead_cost: float = Field(description="Allocated fixed overhead expenses.")
    shipping_cost: float = Field(default=0.0, description="Artisan-paid fulfillment/shipping expense.")
    other_variable_costs: float = Field(default=0.0, description="Additional direct variable costs.")
    base_production_cost: float = Field(description="Base cost (material + labor + packaging + overhead + other).")
    total_seller_cost: float = Field(description="Total seller direct cost including shipping.")


class FeeBreakdown(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    marketplace_commission_percent: float = Field(
        default=0.0,
        description="Commission percentage charged by the marketplace on the transaction price.",
    )
    marketplace_commission_amount: float = Field(
        default=0.0,
        description="Calculated monetary commission amount.",
    )
    discount_percent: float = Field(
        default=0.0,
        description="Promotional discount percentage off listing price.",
    )
    discount_amount: float = Field(
        default=0.0,
        description="Calculated discount amount per unit.",
    )
    tax_rate_percent: float | None = Field(
        default=None,
        description="Applicable tax/GST rate percentage if configured.",
    )
    tax_amount: float = Field(
        default=0.0,
        description="Calculated tax amount (statutory pass-through, not artisan profit).",
    )
    tax_inclusive: bool = Field(
        default=False,
        description="True if final selling price includes tax; False if tax is added to selling price.",
    )
    tax_disclaimer: str = Field(
        default="Tax amounts are statutory pass-through estimates and not seller profit. KarigarConnect is not a tax-compliance authority.",
        description="Statutory tax disclaimer.",
    )


class PricingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique product identifier (e.g., PROD004).",
    )
    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Artisan craft or product name.",
    )

    material_cost: float = Field(
        ...,
        ge=0,
        le=10_000_000,
        description="Raw material cost (non-negative, <= 10,000,000 INR).",
    )
    labor_cost: float = Field(
        ...,
        ge=0,
        le=10_000_000,
        description="Artisan labor cost (non-negative, <= 10,000,000 INR).",
    )
    packaging_cost: float = Field(
        default=0,
        ge=0,
        le=10_000_000,
        description="Packaging cost (non-negative, default: 0).",
    )
    overhead_cost: float = Field(
        default=0,
        ge=0,
        le=10_000_000,
        description="Allocated workshop or tool overhead cost (default: 0).",
    )
    shipping_cost: float = Field(
        default=0,
        ge=0,
        le=10_000_000,
        description="Seller-paid shipping and fulfillment expense (default: 0).",
    )
    other_variable_costs: float = Field(
        default=0,
        ge=0,
        le=10_000_000,
        description="Other direct variable costs (default: 0).",
    )

    # Desired profit as a percentage of the selling price.
    target_profit_margin_percent: float = Field(
        default=25.0,
        gt=0,
        lt=100,
        description="Desired net profit margin percentage of the selling price (0 < margin < 100).",
    )

    marketplace_commission_percent: float = Field(
        default=0.0,
        ge=0,
        lt=100,
        description="Marketplace commission rate as a percentage of transaction revenue (0 <= fee < 100).",
    )

    discount_percent: float = Field(
        default=0.0,
        ge=0,
        lt=100,
        description="Optional promotional discount percentage (0 <= discount < 100).",
    )

    tax_rate_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Optional statutory tax/GST percentage. Disabled by default.",
    )

    tax_inclusive: bool = Field(
        default=False,
        description="If True, customer-facing price includes tax. If False, tax is added separately.",
    )

    pricing_strategy: Literal["exact", "round_nearest_rupee", "psychological_99"] = Field(
        default="exact",
        description="Rounding strategy: 'exact' (2 decimal places), 'round_nearest_rupee', or 'psychological_99' (e.g. ₹799).",
    )

    competitor_prices: list[CompetitorObservation] | None = Field(
        default=None,
        description="Optional list of explicitly supplied competitor observations.",
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=10,
        description="Currency code for costs and recommendations (default: INR).",
    )

    @model_validator(mode="after")
    def validate_pricing_configuration(self) -> "PricingRequest":
        # Check that deductions don't exceed 100% of revenue.
        combined_rate = self.target_profit_margin_percent + self.marketplace_commission_percent
        if combined_rate >= 100.0:
            raise ValueError(
                f"Combined target profit margin ({self.target_profit_margin_percent}%) "
                f"and marketplace commission ({self.marketplace_commission_percent}%) "
                f"is {combined_rate}%, which is >= 100%. "
                f"Deductions would leave zero or negative net revenue to cover costs."
            )

        # Check competitor currencies if provided
        if self.competitor_prices:
            for obs in self.competitor_prices:
                if obs.currency.upper() != self.currency.upper():
                    raise ValueError(
                        f"Competitor price observation currency '{obs.currency}' does not match "
                        f"request currency '{self.currency}'. Mixed currencies are not permitted "
                        f"without explicit exchange rates."
                    )
        return self


class PricingResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(description="Product identifier.")
    product_name: str = Field(description="Product name.")

    material_cost: float = Field(description="Raw material cost.")
    labor_cost: float = Field(description="Labor cost.")
    packaging_cost: float = Field(description="Packaging cost.")
    overhead_cost: float = Field(description="Allocated overhead.")
    shipping_cost: float = Field(default=0.0, description="Artisan shipping expense.")
    other_variable_costs: float = Field(default=0.0, description="Other variable costs.")
    total_cost: float = Field(description="Total seller direct cost.")

    target_profit_margin_percent: float = Field(description="Requested target profit margin percentage.")
    suggested_selling_price: float = Field(description="Recommended customer-facing selling / listing price.")
    discounted_price: float | None = Field(
        default=None,
        description="Effective price paid by buyer after applying promotional discount, if configured.",
    )
    estimated_profit: float = Field(description="Estimated artisan net profit in monetary terms.")
    estimated_profit_margin_percent: float = Field(description="Actual achieved net profit margin percentage.")

    currency: str = Field(default="INR", description="Currency of calculation.")
    pricing_method: str = Field(default="cost_plus_target_margin", description="Pricing methodology applied.")
    pricing_strategy: str = Field(default="exact", description="Applied rounding strategy.")
    requires_market_validation: bool = Field(
        default=True,
        description="Whether artisan review and market validation is advised.",
    )

    cost_breakdown: CostBreakdown | None = Field(
        default=None,
        description="Detailed itemization of direct costs.",
    )
    fee_breakdown: FeeBreakdown | None = Field(
        default=None,
        description="Detailed itemization of marketplace commission, discounts, and taxes.",
    )
    competitor_analysis: CompetitorMarketAnalysis | None = Field(
        default=None,
        description="Statistical summary of valid observed competitor prices.",
    )

    explanation: str = Field(
        default="",
        description="Human-readable breakdown of the pricing calculation and assumptions.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Validation flags, market positioning notes, and warnings.",
    )

    record_id: str | None = Field(
        default=None,
        description="MongoDB record identifier if persisted.",
    )
    created_at: str | None = Field(
        default=None,
        description="UTC creation timestamp in ISO 8601 format.",
    )


class PricingScenarioItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    scenario_name: str = Field(description="Descriptive scenario name (e.g. Conservative, Standard, Growth).")
    target_profit_margin_percent: float = Field(description="Scenario target margin percentage.")
    suggested_selling_price: float = Field(description="Recommended selling price for this scenario.")
    discounted_price: float | None = Field(default=None, description="Discounted price if promotional discount active.")
    total_seller_cost: float = Field(description="Total seller cost.")
    marketplace_commission_amount: float = Field(description="Estimated marketplace commission.")
    shipping_cost: float = Field(description="Shipping expense.")
    tax_amount: float = Field(description="Estimated tax amount.")
    estimated_profit: float = Field(description="Estimated monetary profit.")
    actual_profit_margin_percent: float = Field(description="Actual achieved margin percentage.")
    meets_target_margin: bool = Field(description="True if final rounded price meets or exceeds target margin.")
    warnings: list[str] = Field(default_factory=list, description="Scenario-specific warnings.")


class PricingScenarioRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=200)

    material_cost: float = Field(ge=0, le=10_000_000)
    labor_cost: float = Field(ge=0, le=10_000_000)
    packaging_cost: float = Field(default=0, ge=0, le=10_000_000)
    overhead_cost: float = Field(default=0, ge=0, le=10_000_000)
    shipping_cost: float = Field(default=0, ge=0, le=10_000_000)
    other_variable_costs: float = Field(default=0, ge=0, le=10_000_000)

    # Scenarios: list of target margins to test
    target_profit_margins: list[float] = Field(
        default=[15.0, 25.0, 35.0],
        min_length=1,
        max_length=10,
        description="List of target profit margins to simulate (e.g. [15.0, 25.0, 35.0]).",
    )

    marketplace_commission_percent: float = Field(default=0.0, ge=0, lt=100)
    discount_percent: float = Field(default=0.0, ge=0, lt=100)
    tax_rate_percent: float | None = Field(default=None, ge=0, le=100)
    tax_inclusive: bool = Field(default=False)
    pricing_strategy: Literal["exact", "round_nearest_rupee", "psychological_99"] = Field(default="exact")
    competitor_prices: list[CompetitorObservation] | None = Field(default=None)
    currency: str = Field(default="INR", min_length=3, max_length=10)

    @model_validator(mode="after")
    def validate_scenarios(self) -> "PricingScenarioRequest":
        for margin in self.target_profit_margins:
            if margin <= 0 or margin >= 100:
                raise ValueError(f"Target margin {margin}% is invalid; must be between 0 and 100 exclusive.")
            if margin + self.marketplace_commission_percent >= 100:
                raise ValueError(
                    f"Scenario margin {margin}% + marketplace commission "
                    f"{self.marketplace_commission_percent}% is >= 100%."
                )
        return self


class PricingScenarioResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str
    product_name: str
    currency: str = "INR"
    cost_summary: CostBreakdown
    scenarios: list[PricingScenarioItem]
    explanation: str
