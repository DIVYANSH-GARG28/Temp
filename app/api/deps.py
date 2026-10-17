from typing import Any, Dict, List
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.repositories.user_repository import user_repo

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise AppException(
            code="AUTHENTICATION_REQUIRED",
            message="Bearer authentication token is required.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AppException(
            code="INVALID_TOKEN",
            message="Token payload is missing subject.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException(
            code="USER_NOT_FOUND",
            message="Authenticated user could not be found.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.get("is_active", True):
        raise AppException(
            code="ACCOUNT_INACTIVE",
            message="User account is inactive.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in self.allowed_roles:
            raise AppException(
                code="INSUFFICIENT_PERMISSIONS",
                message=f"Access denied for role '{user_role}'. Required roles: {', '.join(self.allowed_roles)}.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user
