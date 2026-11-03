from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
    UserUpdateRequest,
)
from backend.app.services.auth_service import (
    authenticate_user,
    get_current_user,
    register_user,
    update_user_profile,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Artisan or Buyer)",
    description="Register as an Artisan or Buyer with role-specific profile details. Administrative accounts cannot be registered publicly.",
)
def register(request: UserRegisterRequest):
    return register_user(request)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description="Authenticates credentials and returns a signed JWT access token along with user profile and role claims.",
)
def login(request: UserLoginRequest):
    token, profile = authenticate_user(request.email, request.password)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=profile,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Retrieves the authenticated user's profile details based on Bearer token.",
)
def get_me(current_user: UserProfileResponse = Depends(get_current_user)):
    return current_user


@router.put(
    "/me",
    response_model=UserProfileResponse,
    summary="Update current user profile",
    description="Updates permitted profile fields (e.g. bio, location, categories, phone) for the authenticated user.",
)
def update_me(
    request: UserUpdateRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    return update_user_profile(current_user.user_id, request)
