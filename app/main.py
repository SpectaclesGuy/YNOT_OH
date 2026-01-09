from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.db import mongo_client
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.repositories.resource_repo import ResourceRepository
from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router
from app.routers.resources import router as resources_router

app = FastAPI(title="YNOT Organising Hub API", version="0.1.0")
designs_dir = Path(__file__).resolve().parent.parent / "Designs"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    mongo_client.connect()
    task_repo = TaskRepository(mongo_client.db)
    user_repo = UserRepository(mongo_client.db)
    resource_repo = ResourceRepository(mongo_client.db)
    await task_repo.create_indexes()
    await user_repo.create_indexes()
    await resource_repo.create_indexes()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    mongo_client.close()


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


app.include_router(tasks_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(resources_router)


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    return FileResponse(designs_dir / "index.html")


@app.get("/dashboard", include_in_schema=False)
async def dashboard_page() -> FileResponse:
    return FileResponse(designs_dir / "dashboard.html")


@app.get("/create-task", include_in_schema=False)
async def create_task_page() -> FileResponse:
    return FileResponse(designs_dir / "create_task.html")


@app.get("/edit-task", include_in_schema=False)
async def edit_task_page() -> FileResponse:
    return FileResponse(designs_dir / "edit_task.html")


@app.get("/resource-hub", include_in_schema=False)
async def resource_hub_page() -> FileResponse:
    return FileResponse(designs_dir / "resource_hub.html")


@app.get("/settings", include_in_schema=False)
async def settings_page() -> FileResponse:
    return FileResponse(designs_dir / "settings.html")
