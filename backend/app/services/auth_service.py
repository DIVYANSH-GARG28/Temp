from datetime import datetime, timezone
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    hash_password,
    revoke_token,
    verify_password,
)
from app.repositories.profile_repository import profile_repo
from app.repositories.user_repository import user_repo
from app.schemas.auth import (
    LogoutResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.core.config import settings

class AuthService:
    async def register(self, req: UserRegisterRequest) -> TokenResponse:
        norm_email = req.email.lower().strip()
        existing = await user_repo.get_by_email(norm_email)
        if existing:
            raise AppException(
                code="DUPLICATE_EMAIL",
                message=f"An account with email '{norm_email}' already exists.",
                status_code=409,
            )

        hashed = hash_password(req.password)
        now = datetime.now(timezone.utc)
        user_data = {
            "email": norm_email,
            "hashed_password": hashed,
            "role": req.role.value,
            "name": req.name,
            "is_active": True,
            "telegram_chat_id": None,
            "created_at": now,
            "updated_at": now,
        }
        created_user = await user_repo.create_user(user_data)
        user_id = created_user["id"]

        # Initialize corresponding role-specific profile document
        profile_data = {
            "user_id": user_id,
            "role": req.role.value,
            "name": req.name,
            "headline": req.headline or f"{req.role.capitalize()} at {req.institution}",
            "institution": req.institution or "connectED University",
            "skills": [],
            "career_goals": [],
            "research_interests": [],
            "mentorship_preferences": {
                "accepting_requests": True,
                "max_mentees": 5,
                "preferred_topics": [],
                "preferred_communication": "Telegram",
            },
            "visibility": "public",
            "verification_status": "verified" if req.role.value == "admin" else "unverified",
            "profile_freshness": "current",
            "updated_at": now,
        }
        await profile_repo.create_profile(profile_data)

        access_token = create_access_token(
            subject=user_id,
            role=req.role.value,
            email=norm_email,
        )

        user_resp = UserResponse(
            id=user_id,
            email=norm_email,
            role=req.role,
            name=req.name,
            is_active=True,
            telegram_linked=False,
            created_at=created_user["created_at"],
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_resp,
        )

    async def login(self, req: UserLoginRequest) -> TokenResponse:
        norm_email = req.email.lower().strip()
        user = await user_repo.get_by_email(norm_email)
        if not user:
            raise AppException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password provided.",
                status_code=401,
            )

        if not verify_password(req.password, user.get("hashed_password", "")):
            raise AppException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password provided.",
                status_code=401,
            )

        if not user.get("is_active", True):
            raise AppException(
                code="ACCOUNT_INACTIVE",
                message="This user account is currently inactive.",
                status_code=403,
            )

        user_id = user["id"]
        role = user["role"]

        access_token = create_access_token(
            subject=user_id,
            role=role,
            email=norm_email,
        )

        user_resp = UserResponse(
            id=user_id,
            email=norm_email,
            role=role,
            name=user.get("name", ""),
            is_active=user.get("is_active", True),
            telegram_linked=bool(user.get("telegram_chat_id")),
            created_at=user["created_at"],
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_resp,
        )

    async def logout(self, token: str) -> LogoutResponse:
        revoke_token(token)
        return LogoutResponse(success=True, message="Logged out successfully.")

    async def get_me(self, user_id: str) -> UserResponse:
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User could not be found.",
                status_code=404,
            )
        return UserResponse(
            id=user["id"],
            email=user["email"],
            role=user["role"],
            name=user.get("name", ""),
            is_active=user.get("is_active", True),
            telegram_linked=bool(user.get("telegram_chat_id")),
            created_at=user["created_at"],
        )

auth_service = AuthService()
