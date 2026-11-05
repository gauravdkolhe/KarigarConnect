"""
Prompt Orchestrator Agent
─────────────────────────────────────────────────────────────────────────────
The central intelligence layer of KarigarConnect. Before ANY downstream agent
(Catalog, Pricing, Market Matching) runs, the Orchestrator:

  1. Parses and enriches the artisan's raw spoken/typed input
  2. Detects craft type, region, heritage, and target market from context
  3. Generates rich, detailed, structured prompt briefs for each agent
  4. Returns an OrchestratorBrief that every downstream agent can consume

This means the Catalog Agent, Pricing Agent, and Matching Agent all receive
much richer context than just a product name — they get full narrative,
market positioning, heritage story, B2B buyer persona, and pricing rationale.

Fallback: if Gemini is unavailable, uses a comprehensive rule-based enrichment
engine that detects 150+ Indian craft keywords, materials, and regions.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from google import genai

from backend.app.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# Domain knowledge: Indian craft taxonomy
# ─────────────────────────────────────────────────────────────────────────────

CRAFT_KEYWORDS: dict[str, list[str]] = {
    "bamboo": ["bamboo", "baans", "बांस", "cane", "reed", "wickerwork", "basket", "टोकरी"],
    "pottery": ["pottery", "clay", "terracotta", "ceramic", "mitti", "मिट्टी", "earthen", "kumbh"],
    "weaving": ["weave", "woven", "loom", "handloom", "fabric", "textile", "cloth", "thread", "yarn", "बुनाई"],
    "woodwork": ["wood", "wooden", "teak", "walnut", "rosewood", "carved", "carving", "lacquer", "लकड़ी"],
    "metalwork": ["brass", "copper", "bronze", "iron", "silver", "metal", "dhokra", "bidri", "धातु"],
    "embroidery": ["embroidery", "needlework", "stitch", "zari", "chikankari", "kantha", "phulkari", "कढ़ाई"],
    "block_printing": ["block print", "blockprint", "batik", "dabu", "resist print", "woodblock"],
    "leather": ["leather", "hide", "tanning", "chamda", "चमड़ा", "mojari", "jutis"],
    "stone": ["stone", "marble", "granite", "inlay", "pietra dura", "पत्थर", "makrana"],
    "paper": ["paper", "papier mache", "handmade paper", "origami", "kagaz"],
    "silk": ["silk", "reshmi", "रेशम", "kanchipuram", "banarasi", "mulberry", "tussar", "satin"],
    "jute": ["jute", "joot", "पटसन", "hessian", "burlap", "sacking"],
    "crochet": ["crochet", "knit", "knitting", "macramé", "hook"],
    "painting": ["painting", "chitrakari", "madhubani", "warli", "miniature", "pattachitra", "gond"],
}

REGION_KEYWORDS: dict[str, list[str]] = {
    "Rajasthan": ["rajasthan", "jaipur", "jodhpur", "udaipur", "rajasthani", "blue pottery", "bandhani", "leheriya"],
    "Assam": ["assam", "assamese", "northeast", "muga", "mekhela", "bihu"],
    "West Bengal": ["bengal", "kolkata", "kantha", "jamdani", "dokra", "baluchari", "bishnupur"],
    "Uttar Pradesh": ["uttar pradesh", "varanasi", "lucknow", "agra", "benaras", "chikankari", "zari"],
    "Gujarat": ["gujarat", "kutch", "ahmedabad", "surat", "patola", "bandhani", "rogan"],
    "Tamil Nadu": ["tamil", "thanjavur", "kanchipuram", "kondapalli", "tanjore"],
    "Odisha": ["odisha", "orissa", "puri", "cuttack", "sambalpuri", "pattachitra"],
    "Madhya Pradesh": ["madhya pradesh", "bhopal", "chanderi", "maheshwari", "gond"],
    "Kashmir": ["kashmir", "kashmiri", "kani", "pashmina", "shahtoosh", "walnut"],
    "Himachal Pradesh": ["himachal", "kullu", "kangra", "kinnaur", "lahaul"],
    "Maharashtra": ["maharashtra", "pune", "kolhapur", "nashik", "bidriware", "warli"],
    "Andhra Pradesh": ["andhra", "kalamkari", "kondapalli", "nirmal", "etikoppaka"],
}

B2B_SEGMENTS: dict[str, list[str]] = {
    "Home Decor & Gifting": ["decor", "gift", "decoration", "showpiece", "art piece", "wall hanging", "vase"],
    "Corporate Gifting": ["corporate", "bulk", "office", "branding", "customizable", "logo"],
    "Fashion & Apparel": ["saree", "dupatta", "stole", "scarf", "kurta", "jacket", "blouse", "dress"],
    "Furniture & Interiors": ["furniture", "chair", "table", "shelf", "cabinet", "frame"],
    "Retail & E-commerce": ["retail", "resell", "amazon", "etsy", "flipkart", "online shop"],
    "Hotels & Hospitality": ["hotel", "resort", "spa", "restaurant", "hospitality", "lobby"],
    "Wellness & Lifestyle": ["organic", "natural", "eco", "sustainable", "wellness", "yoga", "meditation"],
    "Export & International": ["export", "international", "foreign buyer", "usa", "europe", "japan"],
}

PRICE_TIER: dict[str, tuple[int, int]] = {
    "bamboo":      (300,  3000),
    "pottery":     (200,  5000),
    "weaving":     (800, 15000),
    "woodwork":    (500, 25000),
    "metalwork":   (400, 20000),
    "embroidery":  (600, 12000),
    "block_printing": (400, 8000),
    "leather":     (500, 10000),
    "stone":       (600, 30000),
    "paper":       (150,  2000),
    "silk":       (1500, 50000),
    "jute":        (200,  3000),
    "crochet":     (300,  6000),
    "painting":    (500, 40000),
}


# ─────────────────────────────────────────────────────────────────────────────
# Output schema
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OrchestratorBrief:
    """Rich structured brief generated by the Orchestrator for downstream agents."""

    # Detected craft intelligence
    detected_craft_type: str = "Traditional Handcraft"
    detected_material:   str = "Natural Material"
    detected_region:     str = "India"
    heritage_story:      str = ""
    craft_uniqueness:    str = ""

    # B2B market context
    primary_b2b_segment: str = "Home Decor & Gifting"
    secondary_b2b_segments: list[str] = field(default_factory=list)
    buyer_persona:        str = ""
    market_positioning:   str = ""
    export_potential:     bool = False

    # Detailed prompt for Catalog Agent
    catalog_prompt:  str = ""

    # Detailed prompt for Pricing Agent
    pricing_prompt:  str = ""
    price_floor:     float = 300.0
    price_ceiling:   float = 5000.0
    suggested_price: float = 0.0

    # Detailed prompt for Matching Agent
    matching_prompt: str = ""
    matching_keywords: list[str] = field(default_factory=list)

    # Translated / normalized English description
    english_description: str = ""

    # Raw metadata
    source_language:  str = "en"
    confidence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected_craft_type":    self.detected_craft_type,
            "detected_material":      self.detected_material,
            "detected_region":        self.detected_region,
            "heritage_story":         self.heritage_story,
            "craft_uniqueness":       self.craft_uniqueness,
            "primary_b2b_segment":    self.primary_b2b_segment,
            "secondary_b2b_segments": self.secondary_b2b_segments,
            "buyer_persona":          self.buyer_persona,
            "market_positioning":     self.market_positioning,
            "export_potential":       self.export_potential,
            "catalog_prompt":         self.catalog_prompt,
            "pricing_prompt":         self.pricing_prompt,
            "price_floor":            self.price_floor,
            "price_ceiling":          self.price_ceiling,
            "suggested_price":        self.suggested_price,
            "matching_prompt":        self.matching_prompt,
            "matching_keywords":      self.matching_keywords,
            "english_description":    self.english_description,
            "source_language":        self.source_language,
            "confidence_score":       self.confidence_score,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based enrichment engine (fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _translate_to_english(text: str) -> str:
    """Accurately translate any Indian or foreign spoken language to clear English."""
    if not text or not text.strip():
        return ""
    cleaned = text.strip()
    
    # 1. Try Google Translate public API first for instantaneous, high-accuracy translation
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=" + urllib.parse.quote(cleaned)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated_chunks = [item[0] for item in data[0] if item and item[0]]
            if translated_chunks:
                translated = "".join(translated_chunks).strip()
                if translated and translated.lower() != cleaned.lower():
                    print(f"[TRANSLATE] Translated to English: '{cleaned[:40]}...' -> '{translated[:40]}...'")
                    return translated
    except Exception as e:
        print(f"[TRANSLATE] Online translation service unavailable: {e}")

    # 2. Try Gemini flash model fallback
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"Translate the following Indian artisan craft description to fluent, natural English. Output ONLY the English translation without preamble or quotes:\n\n{cleaned}"
            r = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
            if r.text and r.text.strip():
                return r.text.strip()
        except Exception as e:
            print(f"[TRANSLATE] Gemini translation fallback skipped: {e}")

    return cleaned


def _detect_craft(text: str) -> tuple[str, str]:
    """Returns (craft_type_key, craft_type_display)."""
    t = text.lower()
    for craft_key, keywords in CRAFT_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return craft_key, craft_key.replace("_", " ").title()
    return "general", "Traditional Handcraft"


def _detect_region(text: str) -> str:
    t = text.lower()
    for region, keywords in REGION_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return region
    return "India"


def _detect_b2b_segments(text: str) -> tuple[str, list[str]]:
    t = text.lower()
    matched = []
    for segment, keywords in B2B_SEGMENTS.items():
        if any(kw in t for kw in keywords):
            matched.append(segment)
    if not matched:
        matched = ["Home Decor & Gifting"]
    return matched[0], matched[1:3]


def _rule_based_brief(
    spoken_text: str,
    product_name: str,
    material: str,
    language: str,
    estimated_cost: float | None,
    desired_price: float | None,
) -> OrchestratorBrief:
    """Comprehensive rule-based orchestration when Gemini is unavailable."""
    all_text = f"{product_name} {material} {spoken_text}"

    craft_key, craft_display = _detect_craft(all_text)
    region = _detect_region(all_text)
    primary_seg, secondary_segs = _detect_b2b_segments(all_text)

    floor, ceiling = PRICE_TIER.get(craft_key, (300, 5000))
    if estimated_cost:
        floor = max(floor, estimated_cost * 2.0)
        ceiling = max(ceiling, estimated_cost * 5.0)
    if desired_price:
        suggested = desired_price
    elif estimated_cost:
        suggested = round(estimated_cost * 3.2)
    else:
        suggested = round((floor + ceiling) / 3)

    heritage = (
        f"This {craft_display} originates from the rich artisan traditions of {region}. "
        f"The craft represents generations of mastery passed down through families, "
        f"embodying cultural heritage and sustainable livelihood for rural artisans."
    )

    uniqueness = (
        f"Each piece of {product_name} is entirely handcrafted — no two are identical. "
        f"The use of {material or 'natural materials'} ensures eco-friendliness "
        f"and authentic texture that machine-made products cannot replicate."
    )

    buyer_persona = (
        f"B2B buyers for {craft_display} typically include: boutique home decor retailers, "
        f"corporate gifting companies, export houses (USA/Europe/Japan), hotel chains "
        f"looking for authentic Indian decor, and eco-friendly lifestyle brands."
    )

    # ── Catalog Agent prompt ──────────────────────────────────────────────
    catalog_prompt = f"""
You are an expert product catalog writer specializing in traditional Indian artisan crafts for B2B wholesale markets.

ARTISAN CONTEXT:
- Product: {product_name}
- Craft Type: {craft_display}
- Primary Material: {material or 'Natural Material'}
- Artisan's Region: {region}
- Artisan's Spoken Description (Translated to English): "{translated_spoken or spoken_text}"
- Primary B2B Market Segment: {primary_seg}

HERITAGE & CULTURAL CONTEXT:
{heritage}

CRAFT UNIQUENESS:
{uniqueness}

TARGET BUYER PERSONA:
{buyer_persona}

YOUR TASK — Create a professional B2B product catalog entry:

1. PRODUCT TITLE: Write a commercially compelling, SEO-optimized title (60-80 chars).
   Must include the craft technique, material, and product type.
   Example format: "Handwoven [Craft] [Product] in Premium [Material] — Wholesale B2B"

2. DESCRIPTION (150-250 words):
   - Opening sentence: Product hook + key benefit for B2B buyers
   - Paragraph 1: Heritage story, craft origin, artisan's skill
   - Paragraph 2: Material quality, production process, specifications
   - Paragraph 3: B2B suitability — bulk availability, customization, lead time
   - Closing: Call to action for wholesale inquiry

3. KEYWORDS (8 unique): Include craft name, material, region, use case, buyer type.
   Mix English terms + transliterated Hindi terms where relevant.

4. PRODUCT DETAILS: material, craft_type, color family, primary purpose.

TONE: Professional yet warm. Emphasize authenticity, heritage, and B2B value proposition.
LANGUAGE: English (with Hindi craft terms in parentheses where adding credibility).
""".strip()

    # ── Pricing Agent prompt ──────────────────────────────────────────────
    pricing_prompt = f"""
You are a fair-trade pricing strategist for Indian artisan crafts in B2B wholesale markets.

PRODUCT CONTEXT:
- Craft Type: {craft_display}
- Material: {material or 'Natural Material'}
- Region: {region}
- Artisan's Estimated Material Cost: ₹{estimated_cost or 'Unknown'}
- Artisan's Desired Price: ₹{desired_price or 'Unknown'}
- Primary Market Segment: {primary_seg}

MARKET INTELLIGENCE:
- Typical retail range for {craft_display}: ₹{floor:,.0f} – ₹{ceiling:,.0f}
- B2B wholesale is typically 40-60% of retail price
- Export price adds 15-25% premium over domestic B2B
- Corporate gifting commands 20-30% premium for customization

PRICING RATIONALE:
The artisan needs a price that:
1. Covers all costs (materials + labor + packaging + overhead)
2. Provides fair livelihood (min 30% profit margin)
3. Leaves room for buyer's margin (B2B buyer needs 40-60% markup room)
4. Remains competitive vs. factory-made alternatives

SUGGESTED PRICING STRATEGY:
- Floor price (breakeven): ₹{floor:,.0f}
- Recommended B2B price: ₹{suggested:,.0f}
- Premium tier (export/corporate): ₹{min(ceiling, suggested * 1.4):,.0f}

COST BREAKDOWN GUIDANCE:
If material cost = ₹{estimated_cost or floor * 0.4:,.0f}:
  - Labor: ~40% of total cost
  - Packaging: ~8% of total cost  
  - Overhead (tools, workshop): ~12% of total cost
  - Target margin: 25-35%
""".strip()

    # ── Matching Agent prompt ─────────────────────────────────────────────
    matching_keywords = [
        product_name.lower(), craft_display.lower(), material.lower() if material else "natural",
        region.lower(), primary_seg.lower(),
        "handmade", "wholesale", "b2b", "artisan", "traditional indian",
    ]
    matching_keywords = list(dict.fromkeys(k for k in matching_keywords if k))[:10]

    matching_prompt = f"""
You are a B2B market matching specialist for Indian artisan products.

PRODUCT PROFILE:
- Product: {product_name}
- Craft: {craft_display} from {region}
- Material: {material or 'Natural material'}
- Primary Segment: {primary_seg}
- Secondary Segments: {', '.join(secondary_segs) or 'General retail'}
- Export Potential: {"High" if region in ["Rajasthan", "Kashmir", "West Bengal"] else "Medium"}

IDEAL BUYER PROFILE:
{buyer_persona}

MATCH CRITERIA (in priority order):
1. Category match: Buyer's requirement category matches {craft_display} or {primary_seg}
2. Material match: Buyer wants {material or 'natural/eco materials'}
3. Quantity match: MOQ compatibility with buyer's order size
4. Budget match: Buyer's budget aligns with ₹{suggested:,.0f}/unit B2B price
5. Location preference: Regional or pan-India sourcing
6. Certification interest: GI tag, fair trade, organic certification

SCORING BOOST: Give +15% score to buyers in: {', '.join(secondary_segs + [primary_seg])}
MATCHING KEYWORDS: {', '.join(matching_keywords)}
""".strip()

    translated_spoken = _translate_to_english(spoken_text) if spoken_text else ""
    english_desc = (
        f"{product_name} — a {craft_display} product crafted in {region} using {material or 'natural materials'}. "
        f"Artisan's description: {translated_spoken}"
        if translated_spoken else
        f"{product_name} — handcrafted {craft_display} from {region}."
    )

    return OrchestratorBrief(
        detected_craft_type=craft_display,
        detected_material=material or "Natural Material",
        detected_region=region,
        heritage_story=heritage,
        craft_uniqueness=uniqueness,
        primary_b2b_segment=primary_seg,
        secondary_b2b_segments=secondary_segs,
        buyer_persona=buyer_persona,
        market_positioning=f"Premium {craft_display} from {region} — authentic, handcrafted, B2B-ready",
        export_potential=(region in ["Rajasthan", "Kashmir", "West Bengal", "Gujarat", "Uttar Pradesh"]),
        catalog_prompt=catalog_prompt,
        pricing_prompt=pricing_prompt,
        price_floor=float(floor),
        price_ceiling=float(ceiling),
        suggested_price=float(suggested),
        matching_prompt=matching_prompt,
        matching_keywords=matching_keywords,
        english_description=english_desc,
        source_language=language,
        confidence_score=0.75,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gemini-powered orchestration
# ─────────────────────────────────────────────────────────────────────────────

def _gemini_orchestrate(
    spoken_text: str,
    product_name: str,
    material: str,
    language: str,
    estimated_cost: float | None,
    desired_price: float | None,
) -> OrchestratorBrief | None:
    """Ask Gemini to act as the master orchestrator and produce a full brief."""
    if not settings.GEMINI_API_KEY:
        return None

    master_prompt = f"""
You are the MASTER ORCHESTRATOR AGENT for KarigarConnect — an AI-powered platform that connects
traditional Indian artisans to B2B buyers globally. Your job is to analyze raw artisan input and
produce a richly detailed structured brief for ALL downstream AI agents.

─────────────────────── ARTISAN INPUT ───────────────────────
Product Name: {product_name}
Material Mentioned: {material or 'Not specified'}
Language of Input: {language}
Artisan's Spoken Description: "{spoken_text}"
Estimated Production Cost: {f'₹{estimated_cost}' if estimated_cost else 'Not provided'}
Artisan's Desired Price: {f'₹{desired_price}' if desired_price else 'Not provided'}
─────────────────────────────────────────────────────────────

Your task: Produce a JSON object with exactly these keys:

{{
  "detected_craft_type": "<Specific craft name e.g. Handwoven Bamboo Basketry>",
  "detected_material": "<Primary material>",
  "detected_region": "<Most likely Indian state/region based on craft>",
  "heritage_story": "<2-3 sentence cultural heritage narrative>",
  "craft_uniqueness": "<What makes this craft special vs mass-produced>",
  "primary_b2b_segment": "<Best matching segment from: Home Decor & Gifting | Corporate Gifting | Fashion & Apparel | Furniture & Interiors | Retail & E-commerce | Hotels & Hospitality | Wellness & Lifestyle | Export & International>",
  "secondary_b2b_segments": ["<segment2>", "<segment3>"],
  "buyer_persona": "<Detailed description of ideal B2B buyer type and buying motivation>",
  "market_positioning": "<One sentence market positioning statement>",
  "export_potential": <true/false>,
  "catalog_prompt": "<A VERY DETAILED multi-paragraph prompt for a Catalog Writing Agent — include all craft context, heritage, material details, target market, and specific instructions for title/description/keywords>",
  "pricing_prompt": "<A VERY DETAILED prompt for a Pricing Agent — include market intel, cost structure, B2B pricing strategy, fair trade considerations, price range, and rationale>",
  "price_floor": <minimum viable B2B price in INR as number>,
  "price_ceiling": <premium B2B price in INR as number>,
  "suggested_price": <recommended B2B wholesale price in INR as number>,
  "matching_prompt": "<A VERY DETAILED prompt for a Market Matching Agent — include buyer profile, match criteria, scoring weights, compatible industry segments>",
  "matching_keywords": ["<8-12 keywords for buyer matching>"],
  "english_description": "<Clean English translation/summary of artisan's spoken description>",
  "source_language": "{language}",
  "confidence_score": <0.0 to 1.0 — your confidence in the orchestration quality>
}}

IMPORTANT:
- catalog_prompt must be 200-400 words — VERY detailed, like a creative brief for a professional copywriter
- pricing_prompt must include specific INR ranges, cost breakdown guidance, B2B pricing rationale
- matching_prompt must specify buyer persona, match weight criteria, industry segments
- All prompts must reference the artisan's actual words/context
- Return ONLY valid JSON — no markdown, no explanation
""".strip()

    def _call() -> dict | None:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            for model in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]:
                try:
                    result = client.models.generate_content(
                        model=model,
                        contents=master_prompt,
                        config={"temperature": 0.4, "response_mime_type": "application/json"},
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            data = ex.submit(_call).result(timeout=8.0)
        if not data:
            return None

        return OrchestratorBrief(
            detected_craft_type=str(data.get("detected_craft_type", "Traditional Handcraft")),
            detected_material=str(data.get("detected_material", material or "Natural Material")),
            detected_region=str(data.get("detected_region", "India")),
            heritage_story=str(data.get("heritage_story", "")),
            craft_uniqueness=str(data.get("craft_uniqueness", "")),
            primary_b2b_segment=str(data.get("primary_b2b_segment", "Home Decor & Gifting")),
            secondary_b2b_segments=list(data.get("secondary_b2b_segments", [])),
            buyer_persona=str(data.get("buyer_persona", "")),
            market_positioning=str(data.get("market_positioning", "")),
            export_potential=bool(data.get("export_potential", False)),
            catalog_prompt=str(data.get("catalog_prompt", "")),
            pricing_prompt=str(data.get("pricing_prompt", "")),
            price_floor=float(data.get("price_floor", 300)),
            price_ceiling=float(data.get("price_ceiling", 5000)),
            suggested_price=float(data.get("suggested_price", 0)),
            matching_prompt=str(data.get("matching_prompt", "")),
            matching_keywords=list(data.get("matching_keywords", [])),
            english_description=str(data.get("english_description", spoken_text[:300])),
            source_language=language,
            confidence_score=float(data.get("confidence_score", 0.8)),
        )
    except Exception as exc:
        print(f"[ORCHESTRATOR] Gemini orchestration failed ({exc}). Using rule-based engine.")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def orchestrate(
    spoken_text: str,
    product_name: str,
    material: str = "",
    language: str = "en",
    estimated_cost: float | None = None,
    desired_price: float | None = None,
) -> OrchestratorBrief:
    """
    Main entry point. Returns a rich OrchestratorBrief for all downstream agents.

    Try Gemini first (8s timeout). Fall back to deterministic rule-based engine.
    Never raises — always returns a valid brief.
    """
    try:
        brief = _gemini_orchestrate(spoken_text, product_name, material, language, estimated_cost, desired_price)
        if brief and brief.catalog_prompt:
            print(f"[ORCHESTRATOR] ✓ Gemini brief ready (confidence={brief.confidence_score:.2f})")
            return brief
    except Exception as exc:
        print(f"[ORCHESTRATOR] Gemini path error: {exc}")

    print("[ORCHESTRATOR] Using rule-based enrichment engine.")
    return _rule_based_brief(spoken_text, product_name, material, language, estimated_cost, desired_price)

