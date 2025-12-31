from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.task import TaskCreate, TaskUpdate


class TaskRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db["tasks"]

    async def create_indexes(self) -> None:
        await self._collection.create_index("assigned_to")
        await self._collection.create_index("status")
        await self._collection.create_index("created_at")

    async def create_task(self, data: TaskCreate, created_by: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        payload = data.model_dump(mode="json")
        payload.update({
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
        })
        result = await self._collection.insert_one(payload)
        return await self.get_task_by_id(str(result.inserted_id))

    async def get_task_by_id(self, task_id: str) -> Optional[dict[str, Any]]:
        if not ObjectId.is_valid(task_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(task_id)})
        if not doc:
            return None
        doc["_id"] = str(doc["_id"])
        return doc

    async def list_tasks(
        self,
        filters: dict[str, Any],
        sort: Optional[Iterable[tuple[str, int]]] = None,
    ) -> list[dict[str, Any]]:
        cursor = self._collection.find(filters)
        if sort:
            cursor = cursor.sort(list(sort))
        docs = await cursor.to_list(length=200)
        for doc in docs:
            doc["_id"] = str(doc["_id"])
        return docs

    async def update_task(self, task_id: str, data: TaskUpdate) -> Optional[dict[str, Any]]:
        if not ObjectId.is_valid(task_id):
            return None
        update_data = {k: v for k, v in data.model_dump(mode="json", exclude_unset=True).items()}
        if not update_data:
            return await self.get_task_by_id(task_id)
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = await self._collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data},
        )
        if result.matched_count == 0:
            return None
        return await self.get_task_by_id(task_id)

    async def delete_task(self, task_id: str) -> bool:
        if not ObjectId.is_valid(task_id):
            return False
        result = await self._collection.delete_one({"_id": ObjectId(task_id)})
        return result.deleted_count == 1
