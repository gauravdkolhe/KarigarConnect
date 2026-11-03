
from backend.app.schemas.catalog import (
    CatalogRequest,
    CatalogResponse,
)
from backend.app.services.catalog_service import (
    get_catalog,
    save_catalog,
)


def main():
    request = CatalogRequest(
        product_id="PROD002",
        product_name="Handmade Bamboo Basket",
        language="en",
        details={
            "material": "bamboo",
            "color": "natural brown",
            "purpose": "storage",
            "craft_type": "handwoven",
        },
    )

    response = CatalogResponse(
        product_id="PROD002",
        product_title="Handwoven Natural Brown Bamboo Storage Basket",
        keywords=[
            "bamboo basket",
            "handmade basket",
            "handwoven basket",
            "storage basket",
        ],
        description=(
            "This handmade basket is handwoven from bamboo "
            "in a natural brown color and is designed for storage."
        ),
        language="en",
        requires_artisan_review=True,
    )

    try:
        saved = save_catalog(request, response)
        print("SAVE RESULT:")
        print(saved)

        retrieved = get_catalog("PROD002")
        print("\nRETRIEVED DOCUMENT:")
        print(retrieved)

        if retrieved and retrieved.get("product_title") == response.product_title:
            print("\nSUCCESS: Catalog saved and retrieved correctly.")
        else:
            raise RuntimeError(
                "Saved catalog could not be verified."
            )
    except Exception as error:
        print(f"\nTEST FAILED: {type(error).__name__}: {error}")
        raise


if __name__ == "__main__":
    main()
