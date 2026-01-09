from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["users"]

    async def create_indexes(self) -> None:
        await self._collection.create_index("email", unique=True)
        await self._collection.create_index(
            [("provider", 1), ("provider_id", 1)],
            unique=True,
        )

    async def upsert_oauth_user(
        self,
        *,
        email: str,
        name: Optional[str],
        provider: str,
        provider_id: str,
        avatar: Optional[str],
    ) -> dict:
        now = datetime.now(timezone.utc)
        result = await self._collection.find_one_and_update(
            {"provider": provider, "provider_id": provider_id},
            {
                "$set": {
                    "email": email,
                    "name": name,
                    "avatar": avatar,
                    "provider": provider,
                    "provider_id": provider_id,
                    "updated_at": now,
                    "last_login": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            # Fallback: fetch by email after upsert
            result = await self._collection.find_one({"email": email})
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(user_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(user_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_by_email(self, email: str) -> Optional[dict]:
        doc = await self._collection.find_one({"email": email})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
