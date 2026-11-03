from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

InquiryStatus = Literal["pending", "accepted", "replied", "declined", "closed"]


class InquiryCreateRequest(BaseModel):
    """Buyer inquiry submission payload."""
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(..., min_length=1, max_length=100)
    requirement_id: str | None = Field(default=None, max_length=100)
    quantity_requested: int = Field(..., gt=0, le=10_000_000)
    target_price_per_unit: float | None = Field(default=None, gt=0, le=100_000_000)
    delivery_destination: str = Field(..., min_length=2, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)


class InquiryStatusUpdateRequest(BaseModel):
    """Inquiry status transition payload."""
    model_config = ConfigDict(str_strip_whitespace=True)

    status: InquiryStatus
    artisan_response_note: str | None = Field(default=None, max_length=1000)


class InquiryResponse(BaseModel):
    """Inquiry representation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    inquiry_id: str
    product_id: str
    product_name: str
    artisan_id: str
    buyer_id: str
    buyer_name: str
    buyer_business: str | None = None
    buyer_contact_email: str | None = None
    buyer_contact_phone: str | None = None
    requirement_id: str | None = None
    quantity_requested: int
    target_price_per_unit: float | None = None
    delivery_destination: str
    message: str
    status: InquiryStatus
    artisan_response_note: str | None = None
    created_at: str
    updated_at: str


class NotificationResponse(BaseModel):
    """In-app notification representation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str  # e.g., "new_match", "new_inquiry", "inquiry_update", "workflow_step"
    reference_id: str | None = None
    is_read: bool = False
    created_at: str
