from fastapi import APIRouter, Depends, Query, status

from backend.app.schemas.auth import UserProfileResponse
from backend.app.schemas.inquiry_notification import (
    InquiryCreateRequest,
    InquiryResponse,
    InquiryStatusUpdateRequest,
)
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.inquiry_notification_service import (
    create_inquiry,
    list_inquiries,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    update_inquiry_status,
)

router = APIRouter(
    tags=["Inquiries & Notifications"],
)


@router.post(
    "/api/inquiries",
    response_model=InquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a buyer inquiry for an artisan product",
    description="Submits a genuine commercial inquiry with requested quantity and delivery destination. Accessible to authenticated buyers.",
)
def submit_inquiry(
    request: InquiryCreateRequest,
    current_user: UserProfileResponse = Depends(require_role(["buyer", "admin"])),
):
    return create_inquiry(current_user, request)


@router.get(
    "/api/inquiries",
    summary="List inquiries",
    description="Lists inquiries related to authenticated user (artisans view received inquiries; buyers view sent inquiries).",
)
def get_inquiries(
    status_filter: str | None = Query(default=None, description="Filter by status (pending, accepted, replied, declined, closed)"),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    records, total = list_inquiries(
        user=current_user,
        status_filter=status_filter,
        limit=limit,
        skip=skip,
    )
    return {
        "total_records": total,
        "limit": limit,
        "skip": skip,
        "inquiries": records,
    }


@router.patch(
    "/api/inquiries/{inquiry_id}/status",
    summary="Update inquiry status",
    description="Transition inquiry status (accept, reply, decline, close). Accessible to inquiry participants.",
)
def update_inquiry(
    inquiry_id: str,
    request: InquiryStatusUpdateRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    return update_inquiry_status(inquiry_id, current_user, request)


@router.get(
    "/api/notifications",
    summary="List in-app notifications",
    description="Retrieves notifications for the current authenticated user (newest first).",
)
def get_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    records, total = list_notifications(current_user.user_id, limit=limit, skip=skip)
    return {
        "total_records": total,
        "limit": limit,
        "skip": skip,
        "notifications": records,
    }


@router.patch(
    "/api/notifications/{notification_id}/read",
    summary="Mark notification as read",
)
def read_notification(
    notification_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    success = mark_notification_read(notification_id, current_user.user_id)
    return {"status": "success" if success else "not_found"}


@router.post(
    "/api/notifications/read-all",
    summary="Mark all notifications as read",
)
def read_all_notifications(
    current_user: UserProfileResponse = Depends(get_current_user),
):
    count = mark_all_notifications_read(current_user.user_id)
    return {"status": "success", "marked_read": count}
