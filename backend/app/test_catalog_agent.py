
from backend.app.schemas.catalog import CatalogRequest
from backend.app.agents.catalog_agent import generate_catalog


request = CatalogRequest(
    product_id="PROD001",
    product_name="Bamboo Basket",
    language="en",
    details={
        "material": "Bamboo",
        "color": "Natural brown",
        "purpose": "Storage",
        "craft_type": "Handcrafted",
    },
)

result = generate_catalog(request)
print("\n--- CATALOG RESULT ---")
print(result.model_dump_json(indent=2))
