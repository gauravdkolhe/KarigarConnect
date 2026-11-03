import re
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

BuyerType = Literal[
    "Retailer",
    "Wholesaler",
    "Distributor",
    "Exporter",
    "Hotel",
    "Interior designer",
    "Corporate buyer",
    "Other business",
]

RequirementStatus = Literal[
    "draft",
    "active",
    "paused",
    "fulfilled",
    "expired",
    "cancelled",
]


class ArtisanInventory(BaseModel):
    """
    Inventory and operational capacity details for an artisan's product.
    Can be stored in artisan_inventory collection or provided with a match request.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(..., min_length=1, max_length=100, description="Product ID from catalog.")
    artisan_id: str = Field(..., min_length=1, max_length=100, description="Unique artisan identifier.")
    available_quantity: int = Field(default=0, ge=0, le=10_000_000, description="Immediate ready stock.")
    production_capacity_per_month: int = Field(
        default=50, ge=0, le=10_000_000, description="Monthly crafting capacity in units."
    )
    minimum_order_quantity: int = Field(default=1, ge=1, le=10_000_000, description="Minimum order batch.")
    unit_price: float | None = Field(
        default=None, ge=0, le=10_000_000, description="Artisan selling price override (or fetched from pricing_records)."
    )
    currency: str = Field(default="INR", min_length=3, max_length=10, description="Currency code (default INR).")
    production_lead_time_days: int = Field(
        default=14, ge=0, le=3650, description="Days needed to produce an order if out of stock."
    )
    location: str = Field(
        default="India", min_length=1, max_length=200, description="Artisan city, state, or region."
    )
    product_status: str = Field(default="available", min_length=1, max_length=50)


class ArtisanProductProfile(BaseModel):
    """
    Combined artisan product profile aggregating catalog, pricing, and inventory.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(..., min_length=1, max_length=100)
    artisan_id: str = Field(default="ARTISAN_DEFAULT", min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=200)
    product_title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="Handicrafts", min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    keywords: list[str] = Field(default_factory=list)
    material: str = Field(..., min_length=1, max_length=100)
    craft_type: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=100)
    available_quantity: int = Field(default=0, ge=0, le=10_000_000)
    production_capacity: int = Field(default=50, ge=0, le=10_000_000)
    minimum_order_quantity: int = Field(default=1, ge=1, le=10_000_000)
    unit_price: float = Field(..., ge=0, le=10_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=10)
    production_lead_time_days: int = Field(default=14, ge=0, le=3650)
    location: str = Field(default="India", min_length=1, max_length=200)
    product_status: str = Field(default="available", min_length=1, max_length=50)


class BuyerRequirementCreate(BaseModel):
    """Request payload to create a new genuine buyer requirement."""
    model_config = ConfigDict(str_strip_whitespace=True)

    buyer_id: str = Field(..., min_length=1, max_length=100, description="Buyer account or business identifier.")
    buyer_name: str = Field(..., min_length=1, max_length=200, description="Buyer full name or enterprise entity.")
    buyer_type: BuyerType = Field(..., description="Classification of the buyer.")
    required_category: str = Field(..., min_length=1, max_length=100, description="Product category required.")
    requirement_title: str = Field(..., min_length=1, max_length=200, description="Summary title of the sourcing requirement.")
    description: str = Field(..., min_length=10, max_length=2000, description="Detailed specifications, design needs, or usage.")
    required_keywords: list[str] = Field(default_factory=list, description="Keywords to match artisan products.")
    preferred_materials: list[str] = Field(default_factory=list, description="Preferred raw materials (e.g. Bamboo, Brass, Silk).")
    preferred_craft_types: list[str] = Field(default_factory=list, description="Preferred craft styles (e.g. Handwoven, Block Print).")
    required_quantity: int = Field(..., gt=0, le=10_000_000, description="Total units required.")
    minimum_budget: float = Field(default=0.0, ge=0, le=100_000_000, description="Target minimum unit budget.")
    maximum_budget: float = Field(..., gt=0, le=100_000_000, description="Maximum ceiling unit budget willing to pay.")
    currency: str = Field(default="INR", min_length=3, max_length=10, description="Currency code (default: INR).")
    delivery_location: str = Field(..., min_length=1, max_length=200, description="Delivery city, state, or country.")
    delivery_deadline_days: int = Field(default=30, gt=0, le=3650, description="Required delivery turnaround time in days.")
    minimum_order_quantity: int = Field(default=1, ge=1, le=10_000_000, description="Minimum batch acceptable.")
    additional_specifications: str | None = Field(default=None, max_length=1000)
    contact_email: EmailStr | None = Field(default=None, description="Contact email (kept private in public listings).")
    contact_phone: str | None = Field(default=None, max_length=50, description="Contact phone (kept private in public listings).")
    requirement_status: RequirementStatus = Field(default="active", description="Requirement lifecycle status.")

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            cleaned = re.sub(r"[\s\-\+\(\)]", "", v.strip())
            if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Contact phone must contain between 7 and 15 digits.")
            return v.strip()
        return None

    @model_validator(mode="after")
    def validate_budgets(self) -> "BuyerRequirementCreate":
        if self.maximum_budget < self.minimum_budget:
            raise ValueError(
                f"maximum_budget ({self.maximum_budget}) cannot be less than minimum_budget ({self.minimum_budget})."
            )
        return self


class BuyerRequirementUpdate(BaseModel):
    """Payload to update an existing buyer requirement."""
    model_config = ConfigDict(str_strip_whitespace=True)

    buyer_name: str | None = Field(default=None, min_length=1, max_length=200)
    buyer_type: BuyerType | None = None
    required_category: str | None = Field(default=None, min_length=1, max_length=100)
    requirement_title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    required_keywords: list[str] | None = None
    preferred_materials: list[str] | None = None
    preferred_craft_types: list[str] | None = None
    required_quantity: int | None = Field(default=None, gt=0, le=10_000_000)
    minimum_budget: float | None = Field(default=None, ge=0, le=100_000_000)
    maximum_budget: float | None = Field(default=None, gt=0, le=100_000_000)
    currency: str | None = Field(default=None, min_length=3, max_length=10)
    delivery_location: str | None = Field(default=None, min_length=1, max_length=200)
    delivery_deadline_days: int | None = Field(default=None, gt=0, le=3650)
    minimum_order_quantity: int | None = Field(default=None, ge=1)
    additional_specifications: str | None = Field(default=None, max_length=1000)
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    requirement_status: RequirementStatus | None = None

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            cleaned = re.sub(r"[\s\-\+\(\)]", "", v.strip())
            if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Contact phone must contain between 7 and 15 digits.")
            return v.strip()
        return None

    @model_validator(mode="after")
    def validate_budgets(self) -> "BuyerRequirementUpdate":
        if self.minimum_budget is not None and self.maximum_budget is not None:
            if self.maximum_budget < self.minimum_budget:
                raise ValueError("maximum_budget cannot be less than minimum_budget.")
        return self


class BuyerRequirementStatusUpdate(BaseModel):
    """Payload to transition requirement status."""
    model_config = ConfigDict(str_strip_whitespace=True)
    requirement_status: RequirementStatus


class BuyerRequirementResponse(BaseModel):
    """Complete requirement representation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    requirement_id: str
    buyer_id: str
    buyer_name: str
    buyer_type: str
    required_category: str
    requirement_title: str
    description: str
    required_keywords: list[str]
    preferred_materials: list[str]
    preferred_craft_types: list[str]
    required_quantity: int
    minimum_budget: float
    maximum_budget: float
    currency: str
    delivery_location: str
    delivery_deadline_days: int
    minimum_order_quantity: int
    additional_specifications: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    requirement_status: str
    created_at: str
    updated_at: str


class MatchCompatibility(BaseModel):
    """Boolean indicator flags for multidimensional compatibility."""
    model_config = ConfigDict(str_strip_whitespace=True)

    category: bool = Field(description="Category alignment.")
    material: bool = Field(description="Material compatibility.")
    craft_type: bool = Field(description="Craft style compatibility.")
    budget: bool = Field(description="Price is within buyer's budget.")
    quantity: bool = Field(description="Artisan capacity can satisfy required quantity.")
    delivery: bool = Field(description="Production lead time satisfies delivery deadline.")
    location: bool = Field(description="Fulfillment/location alignment.")


class MatchScoreBreakdown(BaseModel):
    """Granular points contributed by each evaluation dimension (Total: 100)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    category_score: float = Field(description="Points from category alignment (Max 20).")
    keyword_score: float = Field(description="Points from title, description & keyword overlap (Max 20).")
    material_score: float = Field(description="Points from material compatibility (Max 15).")
    craft_type_score: float = Field(description="Points from craft technique matching (Max 10).")
    price_score: float = Field(description="Points from unit price vs buyer budget (Max 15).")
    quantity_score: float = Field(description="Points from inventory & production capacity (Max 10).")
    location_score: float = Field(description="Points from geographic proximity/serviceability (Max 5).")
    delivery_score: float = Field(description="Points from turnaround lead time (Max 5).")
    total_score: float = Field(description="Total weighted score out of 100.")


class ProductMatchResult(BaseModel):
    """Individual match between an artisan product and a buyer requirement."""
    model_config = ConfigDict(str_strip_whitespace=True)

    match_id: str
    product_id: str
    requirement_id: str
    product_title: str
    buyer_name: str
    buyer_type: str
    match_score: float = Field(description="Overall match score between 0 and 100.")
    match_category: Literal["Excellent", "Good", "Moderate", "Conditional", "Not eligible"]
    compatibility: MatchCompatibility
    score_breakdown: MatchScoreBreakdown
    warnings: list[str] = Field(default_factory=list)
    recommendation: str
    buyer_summary: dict = Field(description="Buyer requirements summary with contact info masked.")
    artisan_summary: dict = Field(description="Artisan product specifications and price.")
    created_at: str | None = None


class ProductMatchesResponse(BaseModel):
    """Matches found for a specific artisan product."""
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str
    product_title: str
    total_matches: int
    matches: list[ProductMatchResult]


class BuyerMatchesResponse(BaseModel):
    """Artisan products matched with a specific buyer requirement."""
    model_config = ConfigDict(str_strip_whitespace=True)

    requirement_id: str
    requirement_title: str
    total_matches: int
    matches: list[ProductMatchResult]
