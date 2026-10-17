from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class MeetingRepository:
    @property
    def collection(self):
        return get_database().meeting_proposals

    def _id_query(self, proposal_id: str) -> Dict[str, Any]:
        if ObjectId.is_valid(proposal_id):
            return {"$or": [{"_id": ObjectId(proposal_id)}, {"_id": proposal_id}, {"id": proposal_id}]}
        return {"$or": [{"_id": proposal_id}, {"id": proposal_id}]}

    async def create_proposal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        data["created_at"] = data.get("created_at") or now
        data["updated_at"] = now
        result = await self.collection.insert_one(data)
        data["id"] = str(result.inserted_id)
        if "_id" in data:
            del data["_id"]
        return data

    async def get_by_id(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one(self._id_query(proposal_id))
        return doc_to_dict(doc)

    async def list_by_request_id(self, request_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"mentorship_request_id": str(request_id)}).sort("created_at", -1)
        docs = await cursor.to_list(length=50)
        return [doc_to_dict(d) for d in docs]

    async def update_response(
        self,
        proposal_id: str,
        user_id: str,
        action: str,
        new_status: str,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        doc = await self.collection.find_one_and_update(
            self._id_query(proposal_id),
            {
                "$set": {
                    f"responses.{user_id}": action,
                    "status": new_status,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        return doc_to_dict(doc)

meeting_repo = MeetingRepository()
