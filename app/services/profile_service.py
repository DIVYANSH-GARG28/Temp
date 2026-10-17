from app.core.exceptions import AppException
from app.repositories.profile_repository import profile_repo
from app.repositories.user_repository import user_repo
from app.schemas.profile import (
    AlumniProfileResponse,
    AlumniVerificationResponse,
    ProfileMeResponse,
    ProfilePatchRequest,
    ProfileVisibility,
    StudentProfileResponse,
    VerificationStatus,
)

class ProfileService:
    async def get_my_profile(self, user_id: str) -> ProfileMeResponse:
        profile = await profile_repo.get_by_user_id(user_id)
        if not profile:
            raise AppException(
                code="PROFILE_NOT_FOUND",
                message="Profile not found for this user.",
                status_code=404,
            )
        return ProfileMeResponse(
            user_id=profile["user_id"],
            role=profile["role"],
            name=profile.get("name", ""),
            headline=profile.get("headline"),
            institution=profile.get("institution"),
            department=profile.get("department"),
            degree=profile.get("degree"),
            graduation_year=profile.get("graduation_year"),
            current_organization=profile.get("current_organization"),
            current_role=profile.get("current_role"),
            skills=profile.get("skills", []),
            career_goals=profile.get("career_goals", []),
            bio=profile.get("bio"),
            experience=profile.get("experience", []),
            research_interests=profile.get("research_interests", []),
            mentorship_preferences=profile.get("mentorship_preferences", {}),
            visibility=profile.get("visibility", ProfileVisibility.PUBLIC),
            verification_status=profile.get("verification_status", VerificationStatus.UNVERIFIED),
            profile_freshness=profile.get("profile_freshness", "current"),
            updated_at=profile["updated_at"],
        )

    async def update_my_profile(self, user_id: str, patch: ProfilePatchRequest) -> ProfileMeResponse:
        update_data = patch.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_my_profile(user_id)

        # Handle nested mentorship preferences if passed
        if "mentorship_preferences" in update_data and update_data["mentorship_preferences"] is not None:
            if hasattr(update_data["mentorship_preferences"], "model_dump"):
                update_data["mentorship_preferences"] = update_data["mentorship_preferences"].model_dump()

        updated = await profile_repo.update_profile(user_id, update_data)
        if not updated:
            raise AppException(
                code="PROFILE_NOT_FOUND",
                message="Profile not found to update.",
                status_code=404,
            )
        return await self.get_my_profile(user_id)

    async def get_student_profile(self, requesting_user_id: str, target_user_id: str) -> StudentProfileResponse:
        profile = await profile_repo.get_by_user_id(target_user_id)
        if not profile or profile.get("role") != "student":
            raise AppException(
                code="STUDENT_NOT_FOUND",
                message="Student profile not found.",
                status_code=404,
            )

        visibility = profile.get("visibility", ProfileVisibility.PUBLIC)
        if visibility == ProfileVisibility.PRIVATE and requesting_user_id != str(target_user_id):
            raise AppException(
                code="PROFILE_NOT_VISIBLE",
                message="This student profile is private.",
                status_code=404,
            )

        return StudentProfileResponse(
            user_id=profile["user_id"],
            name=profile.get("name", ""),
            headline=profile.get("headline"),
            institution=profile.get("institution"),
            department=profile.get("department"),
            degree=profile.get("degree"),
            graduation_year=profile.get("graduation_year"),
            skills=profile.get("skills", []),
            career_goals=profile.get("career_goals", []),
            bio=profile.get("bio"),
            research_interests=profile.get("research_interests", []),
            visibility=visibility,
            updated_at=profile["updated_at"],
        )

    async def get_alumni_profile(self, requesting_user_id: str, target_user_id: str) -> AlumniProfileResponse:
        profile = await profile_repo.get_by_user_id(target_user_id)
        if not profile or profile.get("role") != "alumni":
            raise AppException(
                code="ALUMNI_NOT_FOUND",
                message="Alumni profile not found.",
                status_code=404,
            )

        visibility = profile.get("visibility", ProfileVisibility.PUBLIC)
        if visibility == ProfileVisibility.PRIVATE and requesting_user_id != str(target_user_id):
            raise AppException(
                code="PROFILE_NOT_VISIBLE",
                message="This alumni profile is private.",
                status_code=404,
            )

        return AlumniProfileResponse(
            user_id=profile["user_id"],
            name=profile.get("name", ""),
            headline=profile.get("headline"),
            institution=profile.get("institution"),
            degree=profile.get("degree"),
            graduation_year=profile.get("graduation_year"),
            current_organization=profile.get("current_organization"),
            current_role=profile.get("current_role"),
            skills=profile.get("skills", []),
            bio=profile.get("bio"),
            mentorship_preferences=profile.get("mentorship_preferences", {}),
            visibility=visibility,
            verification_status=profile.get("verification_status", VerificationStatus.UNVERIFIED),
            profile_freshness=profile.get("profile_freshness", "current"),
            updated_at=profile["updated_at"],
        )

    async def get_alumni_verification(self, target_user_id: str) -> AlumniVerificationResponse:
        profile = await profile_repo.get_by_user_id(target_user_id)
        if not profile or profile.get("role") != "alumni":
            raise AppException(
                code="ALUMNI_NOT_FOUND",
                message="Alumni profile not found.",
                status_code=404,
            )

        return AlumniVerificationResponse(
            user_id=profile["user_id"],
            name=profile.get("name", ""),
            verification_status=profile.get("verification_status", VerificationStatus.UNVERIFIED),
            verified_at=profile.get("verified_at"),
            evidence_source=profile.get("evidence_source", "University Registrar / LinkedIn"),
            freshness_score=float(profile.get("freshness_score", 0.95)),
            profile_freshness=profile.get("profile_freshness", "current"),
            last_verified_by=profile.get("last_verified_by", "connectED Academic Services"),
            notes=profile.get("verification_notes", "Verified alumni record."),
        )

profile_service = ProfileService()
