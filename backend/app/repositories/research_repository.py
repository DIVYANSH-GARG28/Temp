from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class ResearchRepository:
    @property
    def collection(self):
        return get_database().research_projects

    def _id_query(self, project_id: str) -> Dict[str, Any]:
        if ObjectId.is_valid(project_id):
            return {"$or": [{"_id": ObjectId(project_id)}, {"_id": project_id}, {"id": project_id}]}
        return {"$or": [{"_id": project_id}, {"id": project_id}]}

    async def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data["created_at"] = data.get("created_at") or datetime.now(timezone.utc)
        result = await self.collection.insert_one(data)
        data["id"] = str(result.inserted_id)
        if "_id" in data:
            del data["_id"]
        return data

    async def list_projects(
        self,
        research_area: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if research_area:
            query["research_area"] = {"$regex": f"^{research_area}$", "$options": "i"}
        cursor = self.collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [doc_to_dict(d) for d in docs]

    async def count_projects(self, research_area: Optional[str] = None) -> int:
        query: Dict[str, Any] = {}
        if research_area:
            query["research_area"] = {"$regex": f"^{research_area}$", "$options": "i"}
        return await self.collection.count_documents(query)

    async def get_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one(self._id_query(project_id))
        return doc_to_dict(doc)

research_repo = ResearchRepository()
