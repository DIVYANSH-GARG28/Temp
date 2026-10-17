from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user
from app.schemas.profile import (
    AlumniProfileResponse,
    AlumniVerificationResponse,
    ProfileMeResponse,
    ProfilePatchRequest,
    StudentProfileResponse,
)
from app.services.profile_service import profile_service

router = APIRouter(tags=["User Profiles"])

@router.get("/profiles/me", response_model=ProfileMeResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Retrieve the authenticated user's profile."""
    return await profile_service.get_my_profile(current_user["id"])

@router.patch("/profiles/me", response_model=ProfileMeResponse, status_code=status.HTTP_200_OK)
async def update_my_profile(
    patch: ProfilePatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Partially update the authenticated user's profile fields."""
    return await profile_service.update_my_profile(current_user["id"], patch)

@router.get("/students/{user_id}", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def get_student_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve a visible student profile by user_id."""
    return await profile_service.get_student_profile(current_user["id"], user_id)

@router.get("/alumni/{user_id}", response_model=AlumniProfileResponse, status_code=status.HTTP_200_OK)
async def get_alumni_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve a visible alumni profile by user_id."""
    return await profile_service.get_alumni_profile(current_user["id"], user_id)

@router.get("/alumni/{user_id}/verification", response_model=AlumniVerificationResponse, status_code=status.HTTP_200_OK)
async def get_alumni_verification(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve alumni verification and profile freshness information."""
    return await profile_service.get_alumni_verification(user_id)
