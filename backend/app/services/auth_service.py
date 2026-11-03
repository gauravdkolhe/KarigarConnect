from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import uuid4
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.errors import DuplicateKeyError

from backend.app.config import settings
from backend.app.database.connection import database
from backend.app.schemas.auth import (
    UserProfileResponse,
    UserRegisterRequest,
    UserUpdateRequest,
)

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Generate a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


def _doc_to_user_profile(doc: dict[str, Any]) -> UserProfileResponse:
    """Normalize MongoDB user document into UserProfileResponse schema."""
    doc_copy = dict(doc)
    doc_copy.pop("_id", None)
    doc_copy.pop("password_hash", None)

    for dt_field in ("created_at", "updated_at"):
        val = doc_copy.get(dt_field)
        if isinstance(val, datetime):
            doc_copy[dt_field] = val.isoformat()
        elif val is None:
            doc_copy[dt_field] = datetime.now(timezone.utc).isoformat()

    return UserProfileResponse(**doc_copy)


def init_auth_indexes() -> None:
    """Safely initialize MongoDB indexes for users collection."""
    try:
        col = database["users"]
        col.create_index("user_id", unique=True, background=True, name="idx_users_user_id_unique")
        col.create_index("email", unique=True, background=True, name="idx_users_email_unique")
        col.create_index("role", background=True, name="idx_users_role")
    except Exception as error:
        print(f"Notice: User index initialization failed or skipped: {error}")


def bootstrap_admin_account() -> None:
    """Ensure a default administrator account exists for platform oversight."""
    try:
        col = database["users"]
        admin_email = "admin@karigarconnect.com"
        existing = col.find_one({"email": admin_email})
        if existing is None:
            now = datetime.now(timezone.utc)
            admin_doc = {
                "user_id": f"USER-ADMIN-{uuid4().hex[:6].upper()}",
                "email": admin_email,
                "password_hash": hash_password("Admin@Karigar2026"),
                "full_name": "KarigarConnect System Admin",
                "role": "admin",
                "status": "active",
                "phone": "+91-9999999999",
                "location": "India",
                "business_name": "KarigarConnect Operations",
                "created_at": now,
                "updated_at": now,
            }
            col.insert_one(admin_doc)
            print("System admin account provisioned: admin@karigarconnect.com")
    except Exception as error:
        print(f"Notice: Admin bootstrap skipped or failed: {error}")


def register_user(request: UserRegisterRequest) -> UserProfileResponse:
    """Register a new artisan or buyer."""
    col = database["users"]
    email_clean = request.email.lower().strip()

    # Check for duplicate email
    if col.find_one({"email": email_clean}) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{email_clean}' already exists.",
        )

    now = datetime.now(timezone.utc)
    role_prefix = "ART" if request.role == "artisan" else "BUY"
    user_id = f"USER-{role_prefix}-{uuid4().hex[:8].upper()}"

    doc = request.model_dump()
    doc["user_id"] = user_id
    doc["email"] = email_clean
    doc["password_hash"] = hash_password(request.password)
    doc.pop("password")
    doc["status"] = "active"
    doc["created_at"] = now
    doc["updated_at"] = now

    try:
        col.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists.",
        )

    return _doc_to_user_profile(doc)


def authenticate_user(email: str, password: str) -> tuple[str, UserProfileResponse]:
    """Authenticate credentials and return (jwt_token, user_profile)."""
    col = database["users"]
    email_clean = email.lower().strip()

    if email_clean == "admin@karigarconnect.com":
        bootstrap_admin_account()

    user_doc = col.find_one({"email": email_clean})

    if user_doc is None or not verify_password(password, user_doc.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if user_doc.get("status") == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact platform support.",
        )

    user_profile = _doc_to_user_profile(user_doc)
    token = create_access_token(user_profile.user_id, user_profile.email, user_profile.role)
    return token, user_profile


def get_user_by_id(user_id: str) -> UserProfileResponse | None:
    """Retrieve user profile by user_id."""
    col = database["users"]
    doc = col.find_one({"user_id": user_id})
    if doc is None:
        return None
    return _doc_to_user_profile(doc)


def update_user_profile(user_id: str, updates: UserUpdateRequest) -> UserProfileResponse:
    """Update profile details of an authenticated user."""
    col = database["users"]
    update_data = {k: v for k, v in updates.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
        curr = get_user_by_id(user_id)
        if curr is None:
            raise HTTPException(status_code=404, detail="User not found.")
        return curr

    update_data["updated_at"] = datetime.now(timezone.utc)

    result = col.find_one_and_update(
        {"user_id": user_id},
        {"$set": update_data},
        return_document=True,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return _doc_to_user_profile(result)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
) -> UserProfileResponse:
    """FastAPI dependency to extract and validate the authenticated user from Bearer token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject claim.")

    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or deleted.")
    if user.status == "suspended":
        raise HTTPException(status_code=403, detail="Account is suspended.")

    return user


def require_role(allowed_roles: list[str]) -> Callable:
    """Dependency factory ensuring current user possesses one of the required roles."""
    def role_checker(current_user: UserProfileResponse = Depends(get_current_user)) -> UserProfileResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of the following roles: {', '.join(allowed_roles)}.",
            )
        return current_user
    return role_checker
