"""
Orchestrator Agent REST API
────────────────────────────────────────────────────────────────────────────
Exposes the Prompt Orchestrator as a standalone endpoint so the frontend
(and other systems) can call it directly to get enriched agent briefs.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from backend.app.agents.orchestrator_agent import OrchestratorBrief, orchestrate
from backend.app.schemas.auth import UserProfileResponse
from backend.app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/orchestrator", tags=["Prompt Orchestrator Agent"])


class OrchestratorRequest(BaseModel):
    """Input for the Prompt Orchestrator Agent."""
    spoken_text: str = Field(..., min_length=2, max_length=3000,
                             description="Artisan's spoken or typed description in any language")
    product_name: str = Field(..., min_length=1, max_length=200)
    material: str = Field(default="", max_length=100)
    language: str = Field(default="en", description="BCP-47 or display name of language (e.g. hi, Hindi, mr)")
    estimated_cost: float | None = Field(default=None, ge=0, description="Material/production cost in INR")
    desired_price: float | None = Field(default=None, ge=0, description="Artisan's target selling price in INR")


class OrchestratorResponse(BaseModel):
    """Full orchestrator brief with detailed prompts for all downstream agents."""
    detected_craft_type: str
    detected_material: str
    detected_region: str
    heritage_story: str
    craft_uniqueness: str
    primary_b2b_segment: str
    secondary_b2b_segments: list[str]
    buyer_persona: str
    market_positioning: str
    export_potential: bool
    catalog_prompt: str
    pricing_prompt: str
    price_floor: float
    price_ceiling: float
    suggested_price: float
    matching_prompt: str
    matching_keywords: list[str]
    english_description: str
    source_language: str
    confidence_score: float


@router.post(
    "/enrich",
    response_model=OrchestratorResponse,
    status_code=status.HTTP_200_OK,
    summary="Orchestrate artisan input into detailed agent briefs",
    description=(
        "The Prompt Orchestrator Agent analyses raw artisan input (spoken text, product name, material) "
        "and produces richly detailed, context-aware prompts for the Catalog Agent, Pricing Agent, "
        "and Market Matching Agent. Use this before calling downstream agents for significantly "
        "better output quality."
    ),
)
def enrich_artisan_input(
    req: OrchestratorRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
) -> OrchestratorResponse:
    """Run the Orchestrator Agent and return the full enriched brief."""
    brief: OrchestratorBrief = orchestrate(
        spoken_text=req.spoken_text,
        product_name=req.product_name,
        material=req.material,
        language=req.language,
        estimated_cost=req.estimated_cost,
        desired_price=req.desired_price,
    )
    return OrchestratorResponse(**brief.to_dict())


@router.get(
    "/health",
    summary="Orchestrator Agent health check",
    status_code=status.HTTP_200_OK,
)
def orchestrator_health() -> dict:
    from backend.app.config import settings
    return {
        "agent": "Prompt Orchestrator",
        "status": "operational",
        "gemini_available": bool(settings.GEMINI_API_KEY),
        "fallback_engine": "rule-based craft taxonomy (150+ keywords, 14 craft types, 11 regions)",
        "downstream_agents": ["Catalog Agent", "Pricing Agent", "Market Matching Agent"],
        "version": "1.0.0",
    }

