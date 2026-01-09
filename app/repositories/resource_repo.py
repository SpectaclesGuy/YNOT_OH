from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.models.resource import ResourceCreate, ResourceUpdate


class ResourceRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["resources"]

    async def create_indexes(self) -> None:
        await self._collection.create_index("category")
        await self._collection.create_index("tags")
        await self._collection.create_index("created_at")
        await self._collection.create_index([("title", "text"), ("description", "text")])

    def _normalize(self, doc: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
        return doc

    def _build_query(self, filters: dict[str, Any]) -> dict[str, Any]:
        query: dict[str, Any] = {}
        if "category" in filters and filters["category"]:
            query["category"] = filters["category"]
        if "tags" in filters and filters["tags"]:
            query["tags"] = filters["tags"]
        if "q" in filters and filters["q"]:
            regex = {"$regex": filters["q"], "$options": "i"}
            query["$or"] = [{"title": regex}, {"description": regex}]
        return query

    async def create(
        self,
        data: ResourceCreate,
        uploaded_by: str,
        file_info: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        payload = data.model_dump(mode="json")
        payload.update(
            {
                "uploaded_by": uploaded_by,
                "created_at": now,
                "updated_at": now,
            }
        )
        if file_info:
            payload.update(file_info)
        result = await self._collection.insert_one(payload)
        return await self.get_by_id(str(result.inserted_id))

    async def get_by_id(self, resource_id: str) -> Optional[dict[str, Any]]:
        if not ObjectId.is_valid(resource_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(resource_id)})
        return self._normalize(doc)

    async def list(
        self,
        filters: dict[str, Any],
        *,
        limit: int = 50,
        skip: int = 0,
        sort: Optional[Iterable[tuple[str, int]]] = None,
    ) -> list[dict[str, Any]]:
        query = self._build_query(filters)
        cursor = self._collection.find(query)
        if sort:
            cursor = cursor.sort(list(sort))
        cursor = cursor.skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._normalize(doc) for doc in docs if doc]

    async def count(self, filters: dict[str, Any]) -> int:
        query = self._build_query(filters)
        return await self._collection.count_documents(query)

    async def update(self, resource_id: str, data: ResourceUpdate) -> Optional[dict[str, Any]]:
        if not ObjectId.is_valid(resource_id):
            return None
        update_data = data.model_dump(mode="json", exclude_unset=True)
        if not update_data:
            return await self.get_by_id(resource_id)
        update_data["updated_at"] = datetime.now(timezone.utc)
        doc = await self._collection.find_one_and_update(
            {"_id": ObjectId(resource_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER,
        )
        return self._normalize(doc)

    async def delete(self, resource_id: str) -> Optional[dict[str, Any]]:
        if not ObjectId.is_valid(resource_id):
            return None
        doc = await self._collection.find_one_and_delete({"_id": ObjectId(resource_id)})
        return self._normalize(doc)
