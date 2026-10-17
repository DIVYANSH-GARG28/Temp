from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pymongo.errors import DuplicateKeyError
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class TelegramRepository:
    @property
    def links_collection(self):
        return get_database().telegram_links

    @property
    def updates_collection(self):
        return get_database().telegram_updates

    async def create_linking_token(self, user_id: str, token: str, expires_at: datetime) -> Dict[str, Any]:
        data = {
            "user_id": str(user_id),
            "token": token,
            "expires_at": expires_at,
            "is_consumed": False,
            "created_at": datetime.now(timezone.utc),
        }
        await self.links_collection.insert_one(data)
        return doc_to_dict(data)

    async def find_and_consume_token(self, token: str) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        # Atomically find and consume token if not consumed and not expired
        doc = await self.links_collection.find_one_and_update(
            {
                "token": token,
                "is_consumed": False,
                "expires_at": {"$gt": now},
            },
            {
                "$set": {
                    "is_consumed": True,
                    "consumed_at": now,
                }
            },
            return_document=True,
        )
        return doc_to_dict(doc)

    async def is_update_processed(self, update_id: int) -> bool:
        doc = await self.updates_collection.find_one({"update_id": update_id})
        return doc is not None

    async def record_update(self, update_id: int) -> bool:
        try:
            await self.updates_collection.insert_one({
                "update_id": update_id,
                "received_at": datetime.now(timezone.utc),
            })
            return True
        except DuplicateKeyError:
            return False

telegram_repo = TelegramRepository()
