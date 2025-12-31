from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.db import mongo_client
from app.routers.tasks import router as tasks_router
from app.repositories.task_repo import TaskRepository

app = FastAPI(title="YNOT Organising Hub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    mongo_client.connect()
    repo = TaskRepository(mongo_client.db)
    await repo.create_indexes()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    mongo_client.close()


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


app.include_router(tasks_router)
