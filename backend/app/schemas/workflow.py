from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

WorkflowStatus = Literal[
    "draft",
    "image_uploaded",
    "catalog_pending",
    "catalog_approved",
    "pricing_calculated",
    "inventory_configured",
    "published",
    "archived",
]


class WorkflowProductCreate(BaseModel):
    """Initial product draft creation request."""
    model_config = ConfigDict(str_strip_whitespace=True)

    product_name: str = Field(..., min_length=2, max_length=200, description="Artisan craft or product name.")
    category: str = Field(default="Handicrafts", min_length=1, max_length=100, description="Product category.")
    initial_material: str = Field(default="Natural Material", min_length=1, max_length=100)
    initial_craft_type: str | None = Field(default=None, max_length=100)
    language: str = Field(default="en", min_length=2, max_length=20)


class WorkflowCatalogApprovalRequest(BaseModel):
    """Catalog review and approval payload."""
    model_config = ConfigDict(str_strip_whitespace=True)

    product_title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    keywords: list[str] = Field(..., min_length=1, max_length=15)
    material: str = Field(..., min_length=1, max_length=100)
    craft_type: str | None = None
    color: str | None = None
    purpose: str | None = None


class WorkflowPricingRequest(BaseModel):
    """Pricing calculation within workflow."""
    model_config = ConfigDict(str_strip_whitespace=True)

    material_cost: float = Field(..., ge=0, le=10_000_000)
    labor_cost: float = Field(..., ge=0, le=10_000_000)
    packaging_cost: float = Field(default=0.0, ge=0, le=10_000_000)
    overhead_cost: float = Field(default=0.0, ge=0, le=10_000_000)
    shipping_cost: float = Field(default=0.0, ge=0, le=10_000_000)
    target_profit_margin_percent: float = Field(default=25.0, gt=0, lt=100)
    marketplace_commission_percent: float = Field(default=0.0, ge=0, lt=100)
    pricing_strategy: Literal["exact", "round_nearest_rupee", "psychological_99"] = "exact"


class WorkflowInventoryRequest(BaseModel):
    """Inventory configuration within workflow."""
    model_config = ConfigDict(str_strip_whitespace=True)

    available_quantity: int = Field(default=10, ge=0, le=10_000_000)
    production_capacity_per_month: int = Field(default=50, ge=0, le=10_000_000)
    minimum_order_quantity: int = Field(default=1, ge=1, le=10_000_000)
    production_lead_time_days: int = Field(default=14, ge=0, le=3650)
    location: str = Field(default="India", min_length=1, max_length=200)


class WorkflowStateResponse(BaseModel):
    """Consolidated product state across all 4 agents."""
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str
    artisan_id: str
    product_name: str
    workflow_status: WorkflowStatus
    steps_completed: list[str] = Field(default_factory=list)
    images: list[dict[str, Any]] = Field(default_factory=list)
    catalog: dict[str, Any] | None = None
    pricing: dict[str, Any] | None = None
    inventory: dict[str, Any] | None = None
    match_count: int = 0
    created_at: str
    updated_at: str


class WorkflowQuickAssistRequest(BaseModel):
    """Voice/spoken input from artisan to trigger AI auto-generation of catalog and fair pricing."""
    model_config = ConfigDict(str_strip_whitespace=True)

    spoken_text: str = Field(..., min_length=2, max_length=2000, description="Spoken or typed description by artisan in local language")
    language: str = Field(default="en", description="Language of voice input (e.g. en, hi, mr, bn, etc.)")
    estimated_cost: float | None = Field(default=None, ge=0, description="Optional raw cost estimate mentioned by artisan")
    desired_price: float | None = Field(default=None, ge=0, description="Optional desired price mentioned by artisan")


class WorkflowSingleApproveRequest(BaseModel):
    """One-click approval/edit of catalog, pricing, and inventory by artisan to publish directly to B2B."""
    model_config = ConfigDict(str_strip_whitespace=True)

    product_title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="Handcrafted artisan product.", min_length=1, max_length=2500)
    keywords: list[str] = Field(default_factory=list)
    material: str = Field(default="Handcrafted Natural Material", min_length=1, max_length=100)
    craft_type: str | None = None
    suggested_price: float = Field(..., gt=0)
    available_quantity: int = Field(default=20, ge=1)
    minimum_order_quantity: int = Field(default=2, ge=1)
    location: str = Field(default="India", max_length=200)
