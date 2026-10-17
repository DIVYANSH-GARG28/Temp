from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class OpportunityRepository:
    @property
    def collection(self):
        return get_database().opportunities

    def _id_query(self, opp_id: str) -> Dict[str, Any]:
        if ObjectId.is_valid(opp_id):
            return {"$or": [{"_id": ObjectId(opp_id)}, {"_id": opp_id}, {"id": opp_id}]}
        return {"$or": [{"_id": opp_id}, {"id": opp_id}]}

    async def create_opportunity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["created_at"] = data.get("created_at") or datetime.now(timezone.utc)
        data["is_active"] = data.get("is_active", True)
        result = await self.collection.insert_one(data)
        data["id"] = str(result.inserted_id)
        if "_id" in data:
            del data["_id"]
        return data

    async def list_opportunities(
        self,
        opp_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"is_active": True}
        if opp_type:
            query["type"] = opp_type
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

    async def count_opportunities(self, opp_type: Optional[str] = None) -> int:
        query: Dict[str, Any] = {"is_active": True}
        if opp_type:
            query["type"] = opp_type
        return await self.collection.count_documents(query)

    async def get_by_id(self, opp_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one(self._id_query(opp_id))
        return doc_to_dict(doc)

opportunity_repo = OpportunityRepository()
