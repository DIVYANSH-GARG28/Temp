from typing import Optional
from app.repositories.profile_repository import profile_repo
from app.repositories.research_repository import research_repo
from app.schemas.research import (
    FacultyRecommendationItem,
    FacultyRecommendationsResponse,
    ResearchProjectResponse,
    ResearchProjectsListResponse,
)

class ResearchService:
    async def list_projects(
        self,
        research_area: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> ResearchProjectsListResponse:
        docs = await research_repo.list_projects(research_area=research_area, limit=limit, offset=offset)
        total = await research_repo.count_projects(research_area=research_area)

        items = [
            ResearchProjectResponse(
                id=d["id"],
                faculty_id=d["faculty_id"],
                faculty_name=d.get("faculty_name", "Faculty Lead"),
                title=d["title"],
                description=d["description"],
                research_area=d["research_area"],
                required_skills=d.get("required_skills", []),
                availability=d.get("availability", "open"),
                application_instructions=d.get("application_instructions", "Submit CV and statement of interest."),
                created_at=d["created_at"],
            )
            for d in docs
        ]
        return ResearchProjectsListResponse(items=items, total=total, limit=limit, offset=offset)

    async def get_faculty_recommendations(
        self,
        student_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> FacultyRecommendationsResponse:
        student_profile = await profile_repo.get_by_user_id(student_id)
        student_interests = set(i.lower() for i in (student_profile.get("research_interests", []) if student_profile else []))
        student_skills = set(s.lower() for s in (student_profile.get("skills", []) if student_profile else []))

        faculty_profiles = await profile_repo.list_faculty(limit=50, offset=0)
        items = []
        for fac in faculty_profiles:
            fac_interests = set(i.lower() for i in fac.get("research_interests", []))
            common = student_interests.intersection(fac_interests)
            
            score = 0.5
            if common:
                score = min(1.0, 0.5 + 0.25 * len(common))
                reason = f"Shared research interest in {', '.join(list(common)[:2])}"
            else:
                reason = f"Active research in {fac.get('department', 'Computer Science')}"

            items.append(
                FacultyRecommendationItem(
                    faculty_id=fac["user_id"],
                    name=fac.get("name", "Faculty Member"),
                    department=fac.get("department", "Computer Science"),
                    institution=fac.get("institution", "connectED University"),
                    research_areas=fac.get("research_interests", []),
                    match_score=round(score, 2),
                    match_reason=reason,
                    active_projects_count=1,
                )
            )

        items.sort(key=lambda x: x.match_score, reverse=True)
        paginated = items[offset : offset + limit]
        return FacultyRecommendationsResponse(items=paginated, total=len(items), limit=limit, offset=offset)

research_service = ResearchService()
