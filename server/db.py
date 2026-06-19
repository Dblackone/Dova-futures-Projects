"""SQLite data layer for the construction project tracker.

Everything is stored in a single SQLite file (no server to run, no setup).
Each helper returns plain dicts so the rest of the app never touches sqlite
Row objects directly.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, date
from typing import Any, Optional

DB_PATH = os.environ.get(
    "TRACKER_DB",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tracker.db"),
)

# --- valid value sets, kept here so the API and the Claude tools agree -------
MILESTONE_STATUSES = ("not_started", "in_progress", "blocked", "done")
PAYMENT_STATUSES = ("paid", "pending", "partial")
EXPENSE_STATUSES = ("paid", "pending")
ISSUE_SEVERITIES = ("low", "medium", "high", "critical")
ISSUE_STATUSES = ("open", "resolved")
NOTE_CATEGORIES = ("design", "construction", "material", "general")


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _today() -> str:
    return date.today().isoformat()


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    description     TEXT DEFAULT '',
    location        TEXT DEFAULT '',
    budget          REAL DEFAULT 0,
    currency        TEXT DEFAULT '$',
    start_date      TEXT,
    target_end_date TEXT,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS milestones (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    description    TEXT DEFAULT '',
    status         TEXT NOT NULL DEFAULT 'not_started',
    target_date    TEXT,
    completed_date TEXT,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artisans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    trade       TEXT DEFAULT '',
    phone       TEXT DEFAULT '',
    agreed_rate REAL,
    notes       TEXT DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    spent_on       TEXT NOT NULL,
    amount         REAL NOT NULL,
    category       TEXT DEFAULT 'general',
    description    TEXT DEFAULT '',
    vendor         TEXT DEFAULT '',
    payment_status TEXT NOT NULL DEFAULT 'paid',
    milestone_id   INTEGER REFERENCES milestones(id) ON DELETE SET NULL,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    artisan_id  INTEGER REFERENCES artisans(id) ON DELETE SET NULL,
    artisan_name TEXT DEFAULT '',
    amount      REAL NOT NULL,
    paid_on     TEXT NOT NULL,
    description TEXT DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'paid',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS issues (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    description   TEXT DEFAULT '',
    severity      TEXT NOT NULL DEFAULT 'medium',
    status        TEXT NOT NULL DEFAULT 'open',
    raised_on     TEXT NOT NULL,
    resolved_on   TEXT,
    resolution    TEXT DEFAULT '',
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category    TEXT NOT NULL DEFAULT 'general',
    title       TEXT NOT NULL,
    content     TEXT DEFAULT '',
    created_at  TEXT NOT NULL
);
"""


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _row(r: Optional[sqlite3.Row]) -> Optional[dict]:
    return dict(r) if r is not None else None


def _rows(rs) -> list[dict]:
    return [dict(r) for r in rs]


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
def create_project(
    name: str,
    budget: float = 0,
    currency: str = "$",
    location: str = "",
    description: str = "",
    start_date: Optional[str] = None,
    target_end_date: Optional[str] = None,
) -> dict:
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO projects
               (name, description, location, budget, currency, start_date, target_end_date, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (name, description, location, budget, currency,
             start_date or _today(), target_end_date, _now()),
        )
        conn.commit()
        return get_project(cur.lastrowid)  # type: ignore[arg-type]
    finally:
        conn.close()


def list_projects() -> list[dict]:
    conn = get_conn()
    try:
        return _rows(conn.execute("SELECT * FROM projects ORDER BY created_at DESC"))
    finally:
        conn.close()


def get_project(project_id: int) -> Optional[dict]:
    conn = get_conn()
    try:
        return _row(conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone())
    finally:
        conn.close()


def update_project(project_id: int, **fields: Any) -> Optional[dict]:
    allowed = {"name", "description", "location", "budget", "currency",
               "start_date", "target_end_date"}
    sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not sets:
        return get_project(project_id)
    conn = get_conn()
    try:
        cols = ", ".join(f"{k}=?" for k in sets)
        conn.execute(f"UPDATE projects SET {cols} WHERE id=?",
                     (*sets.values(), project_id))
        conn.commit()
        return get_project(project_id)
    finally:
        conn.close()


def delete_project(project_id: int) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Milestones
# --------------------------------------------------------------------------- #
def add_milestone(project_id: int, name: str, description: str = "",
                  status: str = "not_started", target_date: Optional[str] = None) -> dict:
    if status not in MILESTONE_STATUSES:
        status = "not_started"
    conn = get_conn()
    try:
        completed = _today() if status == "done" else None
        cur = conn.execute(
            """INSERT INTO milestones
               (project_id, name, description, status, target_date, completed_date, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (project_id, name, description, status, target_date, completed, _now()),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM milestones WHERE id=?", (cur.lastrowid,)).fetchone())  # type: ignore
    finally:
        conn.close()


def find_milestone(project_id: int, name: str) -> Optional[dict]:
    conn = get_conn()
    try:
        return _row(conn.execute(
            "SELECT * FROM milestones WHERE project_id=? AND name LIKE ? ORDER BY created_at DESC LIMIT 1",
            (project_id, f"%{name}%"),
        ).fetchone())
    finally:
        conn.close()


def update_milestone(milestone_id: int, status: Optional[str] = None,
                     description: Optional[str] = None,
                     target_date: Optional[str] = None,
                     completed_date: Optional[str] = None) -> Optional[dict]:
    conn = get_conn()
    try:
        sets: dict[str, Any] = {}
        if status and status in MILESTONE_STATUSES:
            sets["status"] = status
            if status == "done" and not completed_date:
                sets["completed_date"] = _today()
        if description is not None:
            sets["description"] = description
        if target_date is not None:
            sets["target_date"] = target_date
        if completed_date is not None:
            sets["completed_date"] = completed_date
        if sets:
            cols = ", ".join(f"{k}=?" for k in sets)
            conn.execute(f"UPDATE milestones SET {cols} WHERE id=?",
                         (*sets.values(), milestone_id))
            conn.commit()
        return _row(conn.execute("SELECT * FROM milestones WHERE id=?", (milestone_id,)).fetchone())
    finally:
        conn.close()


def list_milestones(project_id: int) -> list[dict]:
    conn = get_conn()
    try:
        return _rows(conn.execute(
            "SELECT * FROM milestones WHERE project_id=? ORDER BY COALESCE(target_date,'9999'), created_at",
            (project_id,),
        ))
    finally:
        conn.close()


def get_milestone(milestone_id: int) -> Optional[dict]:
    conn = get_conn()
    try:
        return _row(conn.execute(
            "SELECT * FROM milestones WHERE id=?", (milestone_id,)).fetchone())
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Artisans
# --------------------------------------------------------------------------- #
def add_artisan(project_id: int, name: str, trade: str = "", phone: str = "",
                agreed_rate: Optional[float] = None, notes: str = "") -> dict:
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO artisans (project_id, name, trade, phone, agreed_rate, notes, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (project_id, name, trade, phone, agreed_rate, notes, _now()),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM artisans WHERE id=?", (cur.lastrowid,)).fetchone())  # type: ignore
    finally:
        conn.close()


def find_artisan(project_id: int, name: str) -> Optional[dict]:
    conn = get_conn()
    try:
        return _row(conn.execute(
            "SELECT * FROM artisans WHERE project_id=? AND name LIKE ? ORDER BY created_at DESC LIMIT 1",
            (project_id, f"%{name}%"),
        ).fetchone())
    finally:
        conn.close()


def list_artisans(project_id: int) -> list[dict]:
    conn = get_conn()
    try:
        rows = _rows(conn.execute(
            "SELECT * FROM artisans WHERE project_id=? ORDER BY name", (project_id,)))
        # attach total paid for convenience
        for a in rows:
            total = conn.execute(
                "SELECT COALESCE(SUM(amount),0) t FROM payments WHERE artisan_id=? AND status!='pending'",
                (a["id"],),
            ).fetchone()["t"]
            a["total_paid"] = total
        return rows
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Expenses
# --------------------------------------------------------------------------- #
def add_expense(project_id: int, amount: float, category: str = "general",
                description: str = "", vendor: str = "", spent_on: Optional[str] = None,
                payment_status: str = "paid", milestone_id: Optional[int] = None) -> dict:
    if payment_status not in EXPENSE_STATUSES:
        payment_status = "paid"
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO expenses
               (project_id, spent_on, amount, category, description, vendor, payment_status, milestone_id, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (project_id, spent_on or _today(), amount, category, description,
             vendor, payment_status, milestone_id, _now()),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM expenses WHERE id=?", (cur.lastrowid,)).fetchone())  # type: ignore
    finally:
        conn.close()


def list_expenses(project_id: int) -> list[dict]:
    conn = get_conn()
    try:
        return _rows(conn.execute(
            "SELECT * FROM expenses WHERE project_id=? ORDER BY spent_on DESC, created_at DESC",
            (project_id,),
        ))
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Payments (to artisans / labour)
# --------------------------------------------------------------------------- #
def record_payment(project_id: int, amount: float, artisan_name: str = "",
                   artisan_id: Optional[int] = None, paid_on: Optional[str] = None,
                   description: str = "", status: str = "paid") -> dict:
    if status not in PAYMENT_STATUSES:
        status = "paid"
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO payments
               (project_id, artisan_id, artisan_name, amount, paid_on, description, status, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (project_id, artisan_id, artisan_name, amount, paid_on or _today(),
             description, status, _now()),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM payments WHERE id=?", (cur.lastrowid,)).fetchone())  # type: ignore
    finally:
        conn.close()


def list_payments(project_id: int) -> list[dict]:
    conn = get_conn()
    try:
        return _rows(conn.execute(
            "SELECT * FROM payments WHERE project_id=? ORDER BY paid_on DESC, created_at DESC",
            (project_id,),
        ))
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Issues
# --------------------------------------------------------------------------- #
def add_issue(project_id: int, title: str, description: str = "",
              severity: str = "medium", status: str = "open",
              raised_on: Optional[str] = None) -> dict:
    if severity not in ISSUE_SEVERITIES:
        severity = "medium"
    if status not in ISSUE_STATUSES:
        status = "open"
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO issues
               (project_id, title, description, severity, status, raised_on, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (project_id, title, description, severity, status, raised_on or _today(), _now()),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM issues WHERE id=?", (cur.lastrowid,)).fetchone())  # type: ignore
    finally:
        conn.close()


def find_issue(project_id: int, title: str) -> Optional[dict]:
    conn = get_conn()
    try:
        return _row(conn.execute(
            "SELECT * FROM issues WHERE project_id=? AND title LIKE ? AND status='open' ORDER BY created_at DESC LIMIT 1",
            (project_id, f"%{title}%"),
        ).fetchone())
    finally:
        conn.close()


def get_issue(issue_id: int) -> Optional[dict]:
    conn = get_conn()
    try:
        return _row(conn.execute(
            "SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone())
    finally:
        conn.close()


def resolve_issue(issue_id: int, resolution: str = "") -> Optional[dict]:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE issues SET status='resolved', resolved_on=?, resolution=? WHERE id=?",
            (_today(), resolution, issue_id),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone())
    finally:
        conn.close()


def reopen_issue(issue_id: int) -> Optional[dict]:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE issues SET status='open', resolved_on=NULL, resolution='' WHERE id=?",
            (issue_id,),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM issues WHERE id=?", (issue_id,)).fetchone())
    finally:
        conn.close()


def list_issues(project_id: int) -> list[dict]:
    conn = get_conn()
    try:
        return _rows(conn.execute(
            """SELECT * FROM issues WHERE project_id=?
               ORDER BY CASE status WHEN 'open' THEN 0 ELSE 1 END,
                        CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1
                                      WHEN 'medium' THEN 2 ELSE 3 END,
                        created_at DESC""",
            (project_id,),
        ))
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Notes (design & construction details)
# --------------------------------------------------------------------------- #
def add_note(project_id: int, title: str, content: str = "",
             category: str = "general") -> dict:
    if category not in NOTE_CATEGORIES:
        category = "general"
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO notes (project_id, category, title, content, created_at) VALUES (?,?,?,?,?)",
            (project_id, category, title, content, _now()),
        )
        conn.commit()
        return _row(conn.execute("SELECT * FROM notes WHERE id=?", (cur.lastrowid,)).fetchone())  # type: ignore
    finally:
        conn.close()


def list_notes(project_id: int) -> list[dict]:
    conn = get_conn()
    try:
        return _rows(conn.execute(
            "SELECT * FROM notes WHERE project_id=? ORDER BY created_at DESC", (project_id,)))
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Generic delete (used by dashboard correction buttons)
# --------------------------------------------------------------------------- #
_DELETABLE = {"milestones", "artisans", "expenses", "payments", "issues", "notes"}


def delete_record(table: str, record_id: int, project_id: int) -> bool:
    if table not in _DELETABLE:
        return False
    conn = get_conn()
    try:
        cur = conn.execute(
            f"DELETE FROM {table} WHERE id=? AND project_id=?", (record_id, project_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Summary / roll-up used by the dashboard and by Claude
# --------------------------------------------------------------------------- #
def get_summary(project_id: int) -> dict:
    project = get_project(project_id)
    if not project:
        return {}
    conn = get_conn()
    try:
        spent_expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE project_id=? AND payment_status='paid'",
            (project_id,)).fetchone()["t"]
        committed_expenses = conn.execute(
            "SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE project_id=? AND payment_status='pending'",
            (project_id,)).fetchone()["t"]
        labour_paid = conn.execute(
            "SELECT COALESCE(SUM(amount),0) t FROM payments WHERE project_id=? AND status!='pending'",
            (project_id,)).fetchone()["t"]
        labour_pending = conn.execute(
            "SELECT COALESCE(SUM(amount),0) t FROM payments WHERE project_id=? AND status='pending'",
            (project_id,)).fetchone()["t"]

        total_spent = (spent_expenses or 0) + (labour_paid or 0)
        outstanding = (committed_expenses or 0) + (labour_pending or 0)

        m_total = conn.execute(
            "SELECT COUNT(*) c FROM milestones WHERE project_id=?", (project_id,)).fetchone()["c"]
        m_done = conn.execute(
            "SELECT COUNT(*) c FROM milestones WHERE project_id=? AND status='done'", (project_id,)).fetchone()["c"]
        issues_open = conn.execute(
            "SELECT COUNT(*) c FROM issues WHERE project_id=? AND status='open'", (project_id,)).fetchone()["c"]
        artisan_count = conn.execute(
            "SELECT COUNT(*) c FROM artisans WHERE project_id=?", (project_id,)).fetchone()["c"]

        budget = project["budget"] or 0
        return {
            "project": project,
            "budget": budget,
            "spent": round(total_spent, 2),
            "spent_materials": round(spent_expenses or 0, 2),
            "spent_labour": round(labour_paid or 0, 2),
            "outstanding": round(outstanding, 2),
            "remaining": round(budget - total_spent, 2),
            "over_budget": total_spent > budget if budget else False,
            "percent_spent": round((total_spent / budget) * 100, 1) if budget else 0,
            "milestones_total": m_total,
            "milestones_done": m_done,
            "milestone_progress": round((m_done / m_total) * 100, 1) if m_total else 0,
            "issues_open": issues_open,
            "artisan_count": artisan_count,
        }
    finally:
        conn.close()
