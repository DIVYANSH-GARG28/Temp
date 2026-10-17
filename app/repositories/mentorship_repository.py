from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class MentorshipRepository:
    @property
    def collection(self):
        return get_database().mentorship_requests

    def _id_query(self, request_id: str) -> Dict[str, Any]:
        if ObjectId.is_valid(request_id):
            return {"$or": [{"_id": ObjectId(request_id)}, {"_id": request_id}, {"id": request_id}]}
        return {"$or": [{"_id": request_id}, {"id": request_id}]}

    async def create_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        data["created_at"] = data.get("created_at") or now
        data["updated_at"] = now
        result = await self.collection.insert_one(data)
        data["id"] = str(result.inserted_id)
        if "_id" in data:
            del data["_id"]
        return data

    async def get_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one(self._id_query(request_id))
        return doc_to_dict(doc)

    async def list_for_user(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {
            "$or": [{"student_id": str(user_id)}, {"mentor_id": str(user_id)}]
        }
        if status:
            query["status"] = status
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

    async def count_for_user(self, user_id: str, status: Optional[str] = None) -> int:
        query: Dict[str, Any] = {
            "$or": [{"student_id": str(user_id)}, {"mentor_id": str(user_id)}]
        }
        if status:
            query["status"] = status
        return await self.collection.count_documents(query)

    async def update_status(
        self,
        request_id: str,
        new_status: str,
        allowed_current_statuses: Optional[List[str]] = None,
        response_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        fallback_recommendation_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        query = self._id_query(request_id)
        if allowed_current_statuses:
            query["status"] = {"$in": allowed_current_statuses}

        now = datetime.now(timezone.utc)
        set_fields: Dict[str, Any] = {
            "status": new_status,
            "updated_at": now,
        }
        if response_at:
            set_fields["response_at"] = response_at
        if fallback_recommendation_id:
            set_fields["fallback_recommendation_id"] = fallback_recommendation_id
        if metadata:
            for k, v in metadata.items():
                set_fields[f"metadata.{k}"] = v

        doc = await self.collection.find_one_and_update(
            query,
            {"$set": set_fields},
            return_document=True,
        )
        return doc_to_dict(doc)

    async def find_expired_pending(self, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        current_time = now or datetime.now(timezone.utc)
        cursor = self.collection.find({
            "status": "pending",
            "deadline": {"$lte": current_time},
        })
        docs = await cursor.to_list(length=100)
        return [doc_to_dict(d) for d in docs]

mentorship_repo = MentorshipRepository()
