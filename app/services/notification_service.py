from app.repositories.community_repository import community_repo
from app.schemas.community import (
    CommunitiesListResponse,
    CommunityResponse,
    NotificationResponse,
    NotificationsListResponse,
)

class NotificationService:
    async def list_communities(self, limit: int = 10, offset: int = 0) -> CommunitiesListResponse:
        docs = await community_repo.list_communities(limit=limit, offset=offset)
        total = await community_repo.count_communities()
        items = [
            CommunityResponse(
                id=d["id"],
                name=d["name"],
                description=d["description"],
                category=d.get("category", "General"),
                member_count=d.get("member_count", 0),
                is_private=d.get("is_private", False),
                created_at=d["created_at"],
            )
            for d in docs
        ]
        return CommunitiesListResponse(items=items, total=total, limit=limit, offset=offset)

    async def list_notifications(self, user_id: str, limit: int = 10, offset: int = 0) -> NotificationsListResponse:
        docs = await community_repo.list_notifications(user_id=user_id, limit=limit, offset=offset)
        total = await community_repo.count_notifications(user_id=user_id)
        items = [
            NotificationResponse(
                id=d["id"],
                user_id=d["user_id"],
                title=d["title"],
                message=d["message"],
                type=d.get("type", "system"),
                read=d.get("read", False),
                link=d.get("link"),
                created_at=d["created_at"],
            )
            for d in docs
        ]
        return NotificationsListResponse(items=items, total=total, limit=limit, offset=offset)

notification_service = NotificationService()
