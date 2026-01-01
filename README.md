# YNOT Organising Hub - Phase 1 Backend

## Prereqs
- Python 3.11
- MongoDB running locally or a connection string

## Setup
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Configure
Set environment variables (PowerShell):
```
$env:MONGODB_URI = "mongodb://localhost:27017"
$env:DB_NAME = "ynot_hub"
```

## Run
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes
- All API requests require the `X-User-Email` header.
- Health check: `GET /health`
- Landing: `http://localhost:8000/`
- Dashboard: `http://localhost:8000/dashboard`
- Create Task: `http://localhost:8000/create-task`
- Edit Task: `http://localhost:8000/edit-task?id=<task_id>`
