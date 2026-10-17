from fastapi import APIRouter
from app.api.v1 import (
    auth,
    communities_notifications,
    faculty_research,
    graph,
    meetings,
    mentors,
    mentorship,
    opportunities,
    profiles,
    telegram,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(mentors.router)
api_router.include_router(mentorship.router)
api_router.include_router(meetings.router)
api_router.include_router(telegram.router)
api_router.include_router(faculty_research.router)
api_router.include_router(opportunities.router)
api_router.include_router(graph.router)
api_router.include_router(communities_notifications.router)
