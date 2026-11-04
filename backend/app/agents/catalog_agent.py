import concurrent.futures
import json
import re

from google import genai

from backend.app.config import settings
from backend.app.schemas.catalog import CatalogRequest, CatalogResponse


def _generate_rule_based_catalog(request: CatalogRequest) -> CatalogResponse:
    """
    Intelligent craft-specialist catalog generator fallback.
    Used when Gemini API quota is reached or network is unavailable, ensuring
    the artisan pipeline continues without interruption.
    """
    details = getattr(request, "details", None)
    name = (getattr(request, "product_name", "") or "").strip()
    material = (getattr(details, "material", "") or getattr(request, "material", "") or "").strip()
    craft = (getattr(details, "craft_type", "") or getattr(request, "craft_type", "") or "").strip()
    purpose = (getattr(details, "purpose", "") or getattr(request, "purpose", "") or "").strip()

    # Commercial SEO product title
    title_parts = []
    if craft and not craft.lower() in name.lower():
        title_parts.append(craft)
    if not any(word in name.lower() for word in ["handcrafted", "handmade", "artisan"]):
        title_parts.append("Handcrafted")
    title_parts.append(name)
    if material and not material.lower() in name.lower():
        title_parts.append(f"in {material}")

    product_title = " ".join(title_parts)

    # Keywords
    base_keywords = [
        "handmade",
        "artisan craft",
        "traditional handicraft",
        name.lower(),
        material.lower(),
        craft.lower(),
        purpose.lower(),
        "sustainable decor",
        "authentic indian craft",
    ]
    seen = set()
    keywords = []
    for kw in base_keywords:
        cleaned = kw.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            keywords.append(cleaned)
    keywords = keywords[:8]

    desc_lines = [
        f"Authentic {craft or 'handcrafted'} {name}, masterfully created using premium {material or 'natural materials'}.",
        f"Designed for {purpose.lower() if purpose else 'aesthetic appeal and practical daily utility'}, showcasing the timeless legacy of traditional Indian artisans.",
        f"Each piece carries unique hand-worked textures and natural variations, ensuring a one-of-a-kind heritage addition to your collection.",
    ]
    description = " ".join(desc_lines)

    return CatalogResponse(
        product_id=request.product_id,
        product_title=product_title,
        keywords=keywords,
        description=description,
        language=request.language or "en",
        requires_artisan_review=True,
    )


def generate_catalog_with_prompt(request: CatalogRequest, custom_prompt: str) -> CatalogResponse:
    """
    Generate catalog using a fully custom prompt (supplied by the Orchestrator Agent).
    Falls back to standard generation if the custom prompt call fails.
    """
    if not settings.GEMINI_API_KEY or not custom_prompt:
        return generate_catalog(request)

    def _call_gemini_custom() -> dict | None:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            # Append JSON schema instruction to the orchestrator's prompt
            full_prompt = (
                custom_prompt
                + f"\n\nProduct ID for this entry: {request.product_id}\n\n"
                + "Return ONLY valid JSON with keys: "
                + "product_id, product_title, keywords (list), description, language, requires_artisan_review."
            )
            for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:
                try:
                    result = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config={"temperature": 0.35, "response_mime_type": "application/json"},
                    )
                    raw = (result.text or "").strip()
                    raw = re.sub(r"\A```(?:json)?\s*|\s*```\Z", "", raw, flags=re.IGNORECASE)
                    if raw:
                        return json.loads(raw)
                except Exception:
                    continue
        except Exception:
            return None
        return None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_gemini_custom)
            response_data = future.result(timeout=6.0)

        if response_data:
            response = CatalogResponse.model_validate(response_data)
            return response.model_copy(update={
                "product_id": request.product_id,
                "language": request.language,
                "requires_artisan_review": True,
            })
    except Exception as err:
        print(f"[CATALOG AGENT] Custom prompt generation failed ({err}). Using standard pipeline.")

    return generate_catalog(request)


def generate_catalog(request: CatalogRequest) -> CatalogResponse:
    """Generate and validate a product catalog using Gemini AI with fallback."""

    if not settings.GEMINI_API_KEY:
        return _generate_rule_based_catalog(request)

    prompt = f"""
You are an artisan product catalog specialist for traditional Indian crafts.

Create a product catalog entry from this JSON:
{request.model_dump_json()}

Requirements:
1. Create one clear, customer-friendly, SEO-optimized product_title.
2. Generate 5 to 8 relevant e-commerce search keywords.
3. Write a concise, appealing 3-sentence description in the requested language ({request.language}).
4. Highlight authentic handmade craftsmanship and material sustainability.
5. Use only facts supplied in the input. Never invent fake certifications.
6. Set requires_artisan_review to true.
7. Return ONLY a valid JSON object with these keys:
   product_id, product_title, keywords, description, language, requires_artisan_review.
8. Keywords must be a list of strings.
"""

    def _call_gemini() -> dict | None:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:
                try:
                    result = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={
                            "temperature": 0.3,
                            "response_mime_type": "application/json",
                        },
                    )
                    raw_output = (result.text or "").strip()
                    raw_output = re.sub(r"\A```(?:json)?\s*|\s*```\Z", "", raw_output, flags=re.IGNORECASE)
                    if raw_output:
                        return json.loads(raw_output)
                except Exception:
                    continue
        except Exception:
            return None
        return None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_gemini)
            response_data = future.result(timeout=4.5)

        if response_data:
            response = CatalogResponse.model_validate(response_data)
            return response.model_copy(
                update={
                    "product_id": request.product_id,
                    "language": request.language,
                    "requires_artisan_review": True,
                }
            )
    except Exception as err:
        print(f"[CATALOG AGENT] Gemini generation bypassed ({err}). Using craft fallback generator.")

    return _generate_rule_based_catalog(request)
