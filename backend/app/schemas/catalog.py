
from pydantic import BaseModel, Field, ConfigDict


class ProductDetails(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    material: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=100)
    purpose: str | None = Field(default=None, max_length=200)
    craft_type: str | None = Field(default=None, max_length=100)


class CatalogRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=200)
    language: str = Field(default="en", min_length=2, max_length=20)
    details: ProductDetails


class CatalogResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str
    product_title: str = Field(min_length=1, max_length=200)
    keywords: list[str] = Field(min_length=3, max_length=8)
    description: str = Field(min_length=1, max_length=1500)
    language: str
    requires_artisan_review: bool = True


class CatalogManualSaveRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=200)
    product_title: str = Field(min_length=1, max_length=200)
    keywords: list[str] = Field(min_length=3, max_length=8)
    description: str = Field(min_length=1, max_length=1500)
    language: str = Field(default="en", min_length=2, max_length=20)
    details: ProductDetails
