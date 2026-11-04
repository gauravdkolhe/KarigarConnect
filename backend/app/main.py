from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.agents.admin_routes import router as admin_router
from backend.app.agents.auth_routes import router as auth_router
from backend.app.agents.catalog_agent import generate_catalog
from backend.app.agents.image_routes import router as image_router
from backend.app.agents.inquiry_routes import router as inquiry_router
from backend.app.agents.market_linkage_routes import router as market_linkage_router
from backend.app.agents.orchestrator_routes import router as orchestrator_router
from backend.app.agents.pricing_routes import router as pricing_router
from backend.app.agents.workflow_routes import router as workflow_router
from backend.app.database.connection import check_database_connection
from backend.app.middleware.error_handler import register_error_handlers
from backend.app.middleware.rate_limiter import limiter, register_rate_limiter
from backend.app.schemas.catalog import (
    CatalogManualSaveRequest,
    CatalogRequest,
    CatalogResponse,
)
from backend.app.schemas.pricing import (
    PricingRequest,
    PricingResponse,
    PricingScenarioRequest,
    PricingScenarioResponse,
)
from backend.app.services.auth_service import bootstrap_admin_account, init_auth_indexes
from backend.app.services.buyer_service import init_market_linkage_indexes
from backend.app.services.catalog_service import (
    get_catalog,
    save_catalog,
    save_manual_catalog,
)
from backend.app.services.inquiry_notification_service import init_inquiry_notification_indexes
from backend.app.services.pricing_persistence import (
    get_pricing_records,
    init_pricing_indexes,
    save_pricing_record,
)
from backend.app.services.pricing_service import (
    calculate_price,
    calculate_scenarios,
)
from backend.app.services.product_workflow_service import init_workflow_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safe startup initialization: ensure database indexes and admin exist
    init_auth_indexes()
    bootstrap_admin_account()
    init_pricing_indexes()
    init_market_linkage_indexes()
    init_workflow_indexes()
    init_inquiry_notification_indexes()
    print("[STARTUP] All MongoDB indexes initialized. Admin account verified.")
    yield
    print("[SHUTDOWN] KarigarConnect backend shutting down gracefully.")


app = FastAPI(
    title="KarigarConnect API",
    description=(
        "**KarigarConnect** is an AI-powered platform that empowers traditional artisans "
        "to digitize products, generate AI catalogs, receive dynamic pricing recommendations, "
        "and connect with genuine buyers through deterministic market linkage.\n\n"
        "### Core Agents\n"
        "- **Image Processing Agent** — Upload and AI-enhance product photographs\n"
        "- **Product Catalog Agent** — Auto-generate SEO-optimized product listings\n"
        "- **Dynamic Pricing Agent** — Calculate cost-based, value-based, and competitive prices\n"
        "- **Market Linkage Agent** — Match artisan products with genuine buyer requirements\n\n"
        "### Authentication\n"
        "All protected endpoints require a **Bearer JWT token** in the `Authorization` header.\n"
        "Obtain a token via `POST /api/auth/login`."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Health", "description": "Service health and readiness checks."},
        {"name": "Authentication", "description": "User registration, login, JWT tokens, and profile management."},
        {"name": "Prompt Orchestrator Agent", "description": "Master orchestrator that enriches raw artisan input into detailed prompts for all downstream agents."},
        {"name": "Four-Agent Workflow", "description": "Unified artisan product workflow: create → images → catalog → pricing → inventory → publish."},
        {"name": "Image Processing", "description": "Upload and AI-enhance product photographs."},
        {"name": "Dynamic Pricing", "description": "Calculate recommended selling prices with cost breakdowns and scenario analysis."},
        {"name": "Market Linkage", "description": "Deterministic matching between artisan products and genuine buyer requirements."},
        {"name": "Inquiries & Notifications", "description": "Commercial inquiry dispatch and in-app notification management."},
        {"name": "Administrative Oversight", "description": "Platform metrics, user moderation, and product governance (admin-only)."},
        {"name": "Catalog", "description": "Direct catalog generation and retrieval endpoints."},
    ],
)

# CORS middleware for seamless frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized error handling (uniform JSON error responses)
register_error_handlers(app)

# Rate limiting (per-IP + per-user throttling)
register_rate_limiter(app)

# Register routers
app.include_router(auth_router)
app.include_router(orchestrator_router)
app.include_router(image_router)
app.include_router(pricing_router)
app.include_router(market_linkage_router)
app.include_router(workflow_router)
app.include_router(inquiry_router)
app.include_router(admin_router)


_dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@app.get("/", tags=["Health"])
def home(request: Request):
    """Root endpoint: serves frontend SPA for browser requests, JSON status for API clients."""
    accept = request.headers.get("accept", "")
    index_html = _dist_dir / "index.html"
    if "text/html" in accept and index_html.is_file():
        return FileResponse(index_html)
    return {
        "project": "KarigarConnect",
        "status": "running",
        "version": "2.0.0",
        "message": "Welcome to KarigarConnect API — AI-powered artisan marketplace platform.",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint for monitoring and deployment readiness probes.

    Returns:
        - `status`: "healthy" if database is reachable, "degraded" otherwise.
        - `database`: "connected" or "disconnected".
    """
    database_connected = check_database_connection()

    return {
        "status": "healthy" if database_connected else "degraded",
        "service": "karigarconnect-backend",
        "version": "2.0.0",
        "database": "connected" if database_connected else "disconnected",
    }


@app.post(
    "/api/catalog/generate",
    response_model=CatalogResponse,
    tags=["Catalog"],
    summary="Generate AI product catalog",
    description="Uses Google Gemini to auto-generate a structured product catalog entry from the provided product details.",
)
def generate_product_catalog(request: CatalogRequest):
    try:
        catalog = generate_catalog(request)
        save_catalog(request, catalog)
        return catalog

    except Exception as error:
        print(
            f"Catalog generation or saving failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=502,
            detail=(
                "Catalog generation or saving failed. "
                "Check the backend terminal for details."
            ),
        ) from error


@app.get(
    "/api/catalog/{product_id}",
    tags=["Catalog"],
    summary="Retrieve product catalog",
    description="Fetch the stored product catalog for a given product ID.",
)
def get_product_catalog(product_id: str):
    try:
        catalog = get_catalog(product_id)

        if catalog is None:
            raise HTTPException(
                status_code=404,
                detail="Catalog not found for this product ID.",
            )

        return catalog

    except HTTPException:
        raise

    except Exception as error:
        print(
            f"Catalog retrieval failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Catalog retrieval failed. Check the backend terminal.",
        ) from error


@app.put(
    "/api/catalog/{product_id}/approve",
    tags=["Catalog"],
    summary="Approve and save artisan-edited catalog",
    description="Saves the artisan-reviewed and potentially edited catalog as the final approved version.",
)
def approve_product_catalog(
    product_id: str,
    request: CatalogManualSaveRequest,
):
    if product_id != request.product_id:
        raise HTTPException(
            status_code=400,
            detail="Path product_id must match request product_id.",
        )

    try:
        result = save_manual_catalog(request)
        return {
            **result,
            "requires_artisan_review": False,
            "message": "Artisan-approved catalog saved successfully.",
        }

    except Exception as error:
        print(
            f"Manual catalog save failed: "
            f"{type(error).__name__}: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail="Manual catalog save failed. Check the backend terminal.",
        ) from error


# Serve frontend assets and SPA fallback
if (_dist_dir / "index.html").is_file():
    if (_dist_dir / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=str(_dist_dir / "assets")), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_spa(full_path: str):
        if full_path.startswith(("api", "health", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Endpoint not found")
        target_file = _dist_dir / full_path
        if full_path and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(_dist_dir / "index.html")
