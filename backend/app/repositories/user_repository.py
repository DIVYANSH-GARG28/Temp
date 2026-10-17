from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class UserRepository:
    @property
    def collection(self):
        return get_database().users

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_data["email"] = user_data["email"].lower().strip()
        user_data["created_at"] = user_data.get("created_at") or datetime.now(timezone.utc)
        user_data["updated_at"] = datetime.now(timezone.utc)
        user_data["is_active"] = user_data.get("is_active", True)
        result = await self.collection.insert_one(user_data)
        user_data["id"] = str(result.inserted_id)
        if "_id" in user_data:
            del user_data["_id"]
        return user_data

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        norm_email = email.lower().strip()
        doc = await self.collection.find_one({"email": norm_email})
        return doc_to_dict(doc)

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if ObjectId.is_valid(user_id):
            query = {"$or": [{"_id": ObjectId(user_id)}, {"_id": user_id}, {"id": user_id}]}
        else:
            query = {"$or": [{"_id": user_id}, {"id": user_id}]}
        doc = await self.collection.find_one(query)
        return doc_to_dict(doc)

    async def get_by_telegram_chat_id(self, chat_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"telegram_chat_id": str(chat_id)})
        return doc_to_dict(doc)

    async def update_telegram_chat_id(self, user_id: str, chat_id: str) -> bool:
        query: Dict[str, Any] = {}
        if ObjectId.is_valid(user_id):
            query = {"$or": [{"_id": ObjectId(user_id)}, {"_id": user_id}, {"id": user_id}]}
        else:
            query = {"$or": [{"_id": user_id}, {"id": user_id}]}
        res = await self.collection.update_one(
            query,
            {"$set": {"telegram_chat_id": str(chat_id), "updated_at": datetime.now(timezone.utc)}},
        )
        return res.modified_count > 0

    async def list_users(self, role: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        query = {"role": role} if role else {}
        cursor = self.collection.find(query).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

user_repo = UserRepository()
