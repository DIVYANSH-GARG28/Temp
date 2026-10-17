from datetime import datetime, timezone
from typing import Optional
from app.core.exceptions import AppException
from app.repositories.opportunity_repository import opportunity_repo
from app.schemas.opportunity import (
    OpportunitiesListResponse,
    OpportunityCreate,
    OpportunityResponse,
    OpportunityType,
)

class OpportunityService:
    ALLOWED_CREATOR_ROLES = {"recruiter", "founder", "faculty", "alumni", "admin"}

    async def list_opportunities(
        self,
        opp_type: Optional[OpportunityType] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> OpportunitiesListResponse:
        type_str = opp_type.value if opp_type else None
        docs = await opportunity_repo.list_opportunities(opp_type=type_str, limit=limit, offset=offset)
        total = await opportunity_repo.count_opportunities(opp_type=type_str)

        items = [
            OpportunityResponse(
                id=d["id"],
                creator_id=d["creator_id"],
                creator_role=d["creator_role"],
                type=OpportunityType(d["type"]),
                title=d["title"],
                description=d["description"],
                organization=d["organization"],
                location=d.get("location", "Remote"),
                required_skills=d.get("required_skills", []),
                deadline=d.get("deadline"),
                application_url=d.get("application_url"),
                contact_email=d.get("contact_email"),
                is_active=d.get("is_active", True),
                created_at=d["created_at"],
            )
            for d in docs
        ]
        return OpportunitiesListResponse(items=items, total=total, limit=limit, offset=offset)

    async def create_opportunity(
        self,
        user_id: str,
        user_role: str,
        data: OpportunityCreate,
    ) -> OpportunityResponse:
        if user_role not in self.ALLOWED_CREATOR_ROLES:
            raise AppException(
                code="INSUFFICIENT_PERMISSIONS",
                message=f"Role '{user_role}' is not authorized to create opportunities.",
                status_code=403,
            )

        now = datetime.now(timezone.utc)
        opp_dict = {
            "creator_id": str(user_id),
            "creator_role": str(user_role),
            "type": data.type.value,
            "title": data.title,
            "description": data.description,
            "organization": data.organization,
            "location": data.location,
            "required_skills": data.required_skills,
            "deadline": data.deadline,
            "application_url": data.application_url,
            "contact_email": data.contact_email,
            "is_active": True,
            "created_at": now,
        }
        created = await opportunity_repo.create_opportunity(opp_dict)

        return OpportunityResponse(
            id=created["id"],
            creator_id=created["creator_id"],
            creator_role=created["creator_role"],
            type=OpportunityType(created["type"]),
            title=created["title"],
            description=created["description"],
            organization=created["organization"],
            location=created.get("location", "Remote"),
            required_skills=created.get("required_skills", []),
            deadline=created.get("deadline"),
            application_url=created.get("application_url"),
            contact_email=created.get("contact_email"),
            is_active=created.get("is_active", True),
            created_at=created["created_at"],
        )

opportunity_service = OpportunityService()
