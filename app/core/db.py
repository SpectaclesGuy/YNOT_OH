from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


class MongoClient:
    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None

    def connect(self) -> None:
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.mongodb_uri)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def db(self):
        if self._client is None:
            raise RuntimeError("Mongo client is not initialized")
        return self._client[settings.db_name]


mongo_client = MongoClient()
