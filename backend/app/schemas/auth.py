from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re

UserRole = Literal["artisan", "buyer", "admin"]
UserStatus = Literal["active", "suspended"]


class UserRegisterRequest(BaseModel):
    """Registration request payload."""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(..., description="Unique user email address.")
    password: str = Field(..., min_length=6, max_length=128, description="User password (min 6 chars).")
    full_name: str = Field(..., min_length=2, max_length=150, description="User full name.")
    role: Literal["artisan", "buyer"] = Field(
        ..., description="Account role: artisan or buyer. Admin cannot be self-registered."
    )
    phone: str | None = Field(default=None, max_length=50, description="Contact phone number.")
    location: str | None = Field(default=None, max_length=200, description="City, state, or region.")
    business_name: str | None = Field(default=None, max_length=200, description="Artisan workshop or buyer company.")

    # Artisan-specific fields
    craft_type: str | None = Field(default=None, max_length=100, description="Primary craft style (e.g., Bamboo, Pottery, Silk).")
    product_categories: list[str] = Field(default_factory=list, description="Categories of products crafted.")
    workshop_location: str | None = Field(default=None, max_length=200, description="Artisan workshop location.")
    bio: str | None = Field(default=None, max_length=1000, description="Short artisan story or business background.")

    # Buyer-specific fields
    buyer_type: str | None = Field(
        default=None, max_length=100, description="Retailer, Wholesaler, Distributor, Exporter, Hotel, etc."
    )
    procurement_interests: list[str] = Field(default_factory=list, description="Target craft materials or categories.")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            cleaned = re.sub(r"[\s\-\+\(\)]", "", v.strip())
            if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Contact phone must contain between 7 and 15 digits.")
            return v.strip()
        return None


class UserLoginRequest(BaseModel):
    """Login credentials payload."""
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserProfileResponse(BaseModel):
    """Authenticated user profile representation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus = "active"
    phone: str | None = None
    location: str | None = None
    business_name: str | None = None
    craft_type: str | None = None
    product_categories: list[str] = Field(default_factory=list)
    workshop_location: str | None = None
    bio: str | None = None
    buyer_type: str | None = None
    procurement_interests: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TokenResponse(BaseModel):
    """JWT access token response."""
    model_config = ConfigDict(str_strip_whitespace=True)

    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


class UserUpdateRequest(BaseModel):
    """Payload to update permitted user profile fields."""
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = None
    location: str | None = Field(default=None, max_length=200)
    business_name: str | None = Field(default=None, max_length=200)
    craft_type: str | None = Field(default=None, max_length=100)
    product_categories: list[str] | None = None
    workshop_location: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=1000)
    buyer_type: str | None = Field(default=None, max_length=100)
    procurement_interests: list[str] | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            cleaned = re.sub(r"[\s\-\+\(\)]", "", v.strip())
            if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Contact phone must contain between 7 and 15 digits.")
            return v.strip()
        return None
