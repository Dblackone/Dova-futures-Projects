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


# --- manual entry / edit (no AI needed) ------------------------------------- #
class MilestoneIn(BaseModel):
    name: str
    description: str = ""
    status: str = "not_started"
    target_date: Optional[str] = None


class MilestonePatch(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[str] = None
    completed_date: Optional[str] = None


class ExpenseIn(BaseModel):
    amount: float
    description: str = ""
    category: str = "general"
    vendor: str = ""
    spent_on: Optional[str] = None
    payment_status: str = "paid"


class PaymentIn(BaseModel):
    artisan_name: str
    amount: float
    description: str = ""
    paid_on: Optional[str] = None
    status: str = "paid"
    trade: str = ""


class ArtisanIn(BaseModel):
    name: str
    trade: str = ""
    phone: str = ""
    agreed_rate: Optional[float] = None
    notes: str = ""


class IssueIn(BaseModel):
    title: str
    description: str = ""
    severity: str = "medium"


class IssuePatch(BaseModel):
    status: Optional[str] = None  # "resolved" or "open"
    resolution: str = ""


class NoteIn(BaseModel):
    title: str
    content: str = ""
    category: str = "general"


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
# Manual create / update (works without the AI assistant)
# --------------------------------------------------------------------------- #
@app.post("/api/projects/{project_id}/milestones")
def post_milestone(project_id: int, body: MilestoneIn):
    _require_project(project_id)
    if not body.name.strip():
        raise HTTPException(400, "Milestone name is required.")
    return db.add_milestone(project_id, name=body.name.strip(),
                            description=body.description, status=body.status,
                            target_date=body.target_date)


@app.patch("/api/projects/{project_id}/milestones/{milestone_id}")
def patch_milestone(project_id: int, milestone_id: int, body: MilestonePatch):
    _require_project(project_id)
    m = db.get_milestone(milestone_id)
    if not m or m["project_id"] != project_id:
        raise HTTPException(404, "Milestone not found.")
    completed = body.completed_date
    # Clear a stale completion date when moving a milestone back out of "done".
    if body.status and body.status != "done":
        completed = ""
    return db.update_milestone(milestone_id, status=body.status,
                               description=body.description,
                               target_date=body.target_date,
                               completed_date=completed)


@app.post("/api/projects/{project_id}/expenses")
def post_expense(project_id: int, body: ExpenseIn):
    _require_project(project_id)
    return db.add_expense(project_id, amount=body.amount,
                          description=body.description, category=body.category or "general",
                          vendor=body.vendor, spent_on=body.spent_on,
                          payment_status=body.payment_status or "paid")


@app.post("/api/projects/{project_id}/payments")
def post_payment_manual(project_id: int, body: PaymentIn):
    _require_project(project_id)
    if not body.artisan_name.strip():
        raise HTTPException(400, "Worker name is required.")
    artisan = db.find_artisan(project_id, body.artisan_name)
    if artisan is None:
        artisan = db.add_artisan(project_id, name=body.artisan_name.strip(),
                                 trade=body.trade or "")
    return db.record_payment(project_id, amount=body.amount,
                             artisan_name=artisan["name"], artisan_id=artisan["id"],
                             description=body.description, paid_on=body.paid_on,
                             status=body.status or "paid")


@app.post("/api/projects/{project_id}/artisans")
def post_artisan(project_id: int, body: ArtisanIn):
    _require_project(project_id)
    if not body.name.strip():
        raise HTTPException(400, "Worker name is required.")
    return db.add_artisan(project_id, name=body.name.strip(), trade=body.trade,
                          phone=body.phone, agreed_rate=body.agreed_rate, notes=body.notes)


@app.post("/api/projects/{project_id}/issues")
def post_issue(project_id: int, body: IssueIn):
    _require_project(project_id)
    if not body.title.strip():
        raise HTTPException(400, "Issue title is required.")
    return db.add_issue(project_id, title=body.title.strip(),
                        description=body.description, severity=body.severity or "medium")


@app.patch("/api/projects/{project_id}/issues/{issue_id}")
def patch_issue(project_id: int, issue_id: int, body: IssuePatch):
    _require_project(project_id)
    it = db.get_issue(issue_id)
    if not it or it["project_id"] != project_id:
        raise HTTPException(404, "Issue not found.")
    if body.status == "resolved":
        return db.resolve_issue(issue_id, body.resolution or "")
    if body.status == "open":
        return db.reopen_issue(issue_id)
    raise HTTPException(400, "status must be 'resolved' or 'open'.")


@app.post("/api/projects/{project_id}/notes")
def post_note(project_id: int, body: NoteIn):
    _require_project(project_id)
    if not body.title.strip():
        raise HTTPException(400, "Note title is required.")
    return db.add_note(project_id, title=body.title.strip(),
                       content=body.content, category=body.category or "general")


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
