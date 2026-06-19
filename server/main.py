"""FastAPI app: REST endpoints for the dashboard + the Claude chat endpoint.

Run with:  uvicorn server.main:app --reload
The static frontend in ../web is served at the root URL.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # python-dotenv is optional
    pass

from . import db
from . import agent
from . import seed

app = FastAPI(title="Construction Project Tracker")

db.init_db()
seed.maybe_seed()  # pre-load the Ibafo pool on a fresh database (SEED_POOL=0 to skip)

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #
class ProjectIn(BaseModel):
    name: str
    budget: float = 0
    currency: str = "$"
    location: str = ""
    description: str = ""
    start_date: Optional[str] = None
    target_end_date: Optional[str] = None


class ChatIn(BaseModel):
    message: str
    history: list[dict] = []


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
@app.get("/api/projects")
def get_projects():
    return db.list_projects()


@app.post("/api/projects")
def post_project(body: ProjectIn):
    if not body.name.strip():
        raise HTTPException(400, "Project name is required.")
    return db.create_project(
        name=body.name.strip(),
        budget=body.budget,
        currency=body.currency or "$",
        location=body.location,
        description=body.description,
        start_date=body.start_date,
        target_end_date=body.target_end_date,
    )


@app.patch("/api/projects/{project_id}")
def patch_project(project_id: int, body: ProjectIn):
    if not db.get_project(project_id):
        raise HTTPException(404, "Project not found.")
    return db.update_project(
        project_id,
        name=body.name,
        budget=body.budget,
        currency=body.currency,
        location=body.location,
        description=body.description,
        start_date=body.start_date,
        target_end_date=body.target_end_date,
    )


@app.delete("/api/projects/{project_id}")
def remove_project(project_id: int):
    db.delete_project(project_id)
    return {"ok": True}


def _require_project(project_id: int) -> dict:
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found.")
    return project


# --------------------------------------------------------------------------- #
# Dashboard data
# --------------------------------------------------------------------------- #
@app.get("/api/projects/{project_id}/summary")
def get_summary(project_id: int):
    _require_project(project_id)
    return db.get_summary(project_id)


@app.get("/api/projects/{project_id}/expenses")
def get_expenses(project_id: int):
    _require_project(project_id)
    return db.list_expenses(project_id)


@app.get("/api/projects/{project_id}/payments")
def get_payments(project_id: int):
    _require_project(project_id)
    return db.list_payments(project_id)


@app.get("/api/projects/{project_id}/milestones")
def get_milestones(project_id: int):
    _require_project(project_id)
    return db.list_milestones(project_id)


@app.get("/api/projects/{project_id}/artisans")
def get_artisans(project_id: int):
    _require_project(project_id)
    return db.list_artisans(project_id)


@app.get("/api/projects/{project_id}/issues")
def get_issues(project_id: int):
    _require_project(project_id)
    return db.list_issues(project_id)


@app.get("/api/projects/{project_id}/notes")
def get_notes(project_id: int):
    _require_project(project_id)
    return db.list_notes(project_id)


@app.delete("/api/projects/{project_id}/{table}/{record_id}")
def delete_record(project_id: int, table: str, record_id: int):
    _require_project(project_id)
    if not db.delete_record(table, record_id, project_id):
        raise HTTPException(404, "Record not found or not deletable.")
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Claude chat
# --------------------------------------------------------------------------- #
@app.post("/api/projects/{project_id}/chat")
def post_chat(project_id: int, body: ChatIn):
    _require_project(project_id)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            503,
            "ANTHROPIC_API_KEY is not set on the server. Add it to your .env file to "
            "enable the assistant.",
        )
    if not body.message.strip():
        raise HTTPException(400, "Message is required.")
    try:
        return agent.chat(project_id, body.message.strip(), body.history)
    except Exception as exc:  # surface a friendly error to the UI
        raise HTTPException(500, f"Assistant error: {exc}")


@app.get("/api/health")
def health():
    return {"ok": True, "ai_enabled": bool(os.environ.get("ANTHROPIC_API_KEY"))}


# --------------------------------------------------------------------------- #
# Static frontend (mounted last so /api routes win)
# --------------------------------------------------------------------------- #
@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


app.mount("/", StaticFiles(directory=WEB_DIR), name="web")
