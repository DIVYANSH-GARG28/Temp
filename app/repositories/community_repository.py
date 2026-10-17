from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class CommunityRepository:
    @property
    def communities_coll(self):
        return get_database().communities

    @property
    def notifications_coll(self):
        return get_database().notifications

    async def list_communities(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.communities_coll.find({"is_private": False}).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

    async def count_communities(self) -> int:
        return await self.communities_coll.count_documents({"is_private": False})

    async def create_community(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["created_at"] = data.get("created_at") or datetime.now(timezone.utc)
        result = await self.communities_coll.insert_one(data)
        data["id"] = str(result.inserted_id)
        if "_id" in data:
            del data["_id"]
        return data

    async def list_notifications(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        cursor = self.notifications_coll.find({"user_id": str(user_id)}).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

    async def count_notifications(self, user_id: str) -> int:
        return await self.notifications_coll.count_documents({"user_id": str(user_id)})

    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notif_type: str = "system",
        link: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = {
            "user_id": str(user_id),
            "title": title,
            "message": message,
            "type": notif_type,
            "read": False,
            "link": link,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self.notifications_coll.insert_one(data)
        data["id"] = str(result.inserted_id)
        if "_id" in data:
            del data["_id"]
        return data

community_repo = CommunityRepository()
