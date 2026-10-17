from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class ProfileRepository:
    @property
    def collection(self):
        return get_database().profiles

    async def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"user_id": str(user_id)})
        return doc_to_dict(doc)

    async def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        profile_data["user_id"] = str(profile_data["user_id"])
        profile_data["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.insert_one(profile_data)
        profile_data["id"] = str(result.inserted_id)
        if "_id" in profile_data:
            del profile_data["_id"]
        return profile_data

    async def update_profile(self, user_id: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        update_fields["updated_at"] = datetime.now(timezone.utc)
        # Ensure protected fields are NOT overwritten here
        update_fields.pop("user_id", None)
        update_fields.pop("role", None)
        update_fields.pop("verification_status", None)
        update_fields.pop("verification", None)

        doc = await self.collection.find_one_and_update(
            {"user_id": str(user_id)},
            {"$set": update_fields},
            return_document=True,
        )
        return doc_to_dict(doc)

    async def list_alumni(
        self,
        skill: Optional[str] = None,
        career_goal: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {
            "role": "alumni",
            "visibility": {"$ne": "private"},
            "mentorship_preferences.accepting_requests": True,
        }
        if skill:
            query["skills"] = {"$regex": f"^{skill}$", "$options": "i"}
        
        cursor = self.collection.find(query).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

    async def count_alumni(
        self,
        skill: Optional[str] = None,
        career_goal: Optional[str] = None,
    ) -> int:
        query: Dict[str, Any] = {
            "role": "alumni",
            "visibility": {"$ne": "private"},
            "mentorship_preferences.accepting_requests": True,
        }
        if skill:
            query["skills"] = {"$regex": f"^{skill}$", "$options": "i"}
        return await self.collection.count_documents(query)

    async def list_faculty(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {
            "role": "faculty",
            "visibility": {"$ne": "private"},
        }
        cursor = self.collection.find(query).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

profile_repo = ProfileRepository()
