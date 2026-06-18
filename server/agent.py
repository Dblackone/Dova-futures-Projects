"""Claude integration: turns plain-English messages into structured records.

A user types something like "Paid James the mason $400 for the foundation
today" and Claude calls the right tool to log it. Questions like "how much
over budget am I?" are answered from the project data via read tools.

Uses the Messages API with a manual tool-use loop so every tool call runs
against the SQLite database scoped to the current project.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import anthropic

from . import db

MODEL = "claude-opus-4-8"
MAX_TOOL_ITERATIONS = 12

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Lazily build the client so the app still imports without a key set."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


# --------------------------------------------------------------------------- #
# Tool definitions exposed to Claude
# --------------------------------------------------------------------------- #
TOOLS: list[dict] = [
    {
        "name": "add_expense",
        "description": (
            "Record a material/general project expense (cement, blocks, rentals, "
            "transport, permits, etc.). Use this for money spent on things, not on "
            "labour paid directly to a named worker (use record_payment for that)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Amount of the expense."},
                "description": {"type": "string", "description": "What was bought / paid for."},
                "category": {
                    "type": "string",
                    "description": "Short category, e.g. materials, transport, rentals, permits, utilities, general.",
                },
                "vendor": {"type": "string", "description": "Supplier or shop name, if known."},
                "spent_on": {"type": "string", "description": "Date in YYYY-MM-DD. Omit to use today."},
                "payment_status": {
                    "type": "string",
                    "enum": list(db.EXPENSE_STATUSES),
                    "description": "'paid' if already paid, 'pending' if owed/on credit.",
                },
            },
            "required": ["amount", "description"],
        },
    },
    {
        "name": "add_artisan",
        "description": "Add a worker/artisan/contractor to the project (mason, carpenter, electrician, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "trade": {"type": "string", "description": "e.g. mason, carpenter, electrician, plumber, painter."},
                "phone": {"type": "string"},
                "agreed_rate": {"type": "number", "description": "Agreed rate or contract amount, if any."},
                "notes": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "record_payment",
        "description": (
            "Record a payment made to a worker/artisan for labour. If the artisan is "
            "not already on the project they will be created automatically."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "artisan_name": {"type": "string", "description": "Who was paid."},
                "amount": {"type": "number"},
                "description": {"type": "string", "description": "What the payment was for, e.g. 'foundation work'."},
                "paid_on": {"type": "string", "description": "Date in YYYY-MM-DD. Omit to use today."},
                "status": {
                    "type": "string",
                    "enum": list(db.PAYMENT_STATUSES),
                    "description": "'paid', 'partial', or 'pending' (still owed).",
                },
                "trade": {"type": "string", "description": "The artisan's trade, if creating them now."},
            },
            "required": ["artisan_name", "amount"],
        },
    },
    {
        "name": "add_milestone",
        "description": "Create a project milestone / phase (e.g. Foundation, Roofing, Plastering, Handover).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": list(db.MILESTONE_STATUSES)},
                "target_date": {"type": "string", "description": "Planned completion date YYYY-MM-DD."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_milestone",
        "description": "Update an existing milestone's status or details. Match it by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name (or part of it) of the milestone to update."},
                "status": {"type": "string", "enum": list(db.MILESTONE_STATUSES)},
                "description": {"type": "string"},
                "target_date": {"type": "string", "description": "New planned date YYYY-MM-DD."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "add_issue",
        "description": "Log a problem, snag, defect, or blocker on the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short summary of the issue."},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": list(db.ISSUE_SEVERITIES)},
            },
            "required": ["title"],
        },
    },
    {
        "name": "resolve_issue",
        "description": "Mark an open issue as resolved. Match it by title.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title (or part of it) of the issue to resolve."},
                "resolution": {"type": "string", "description": "How it was resolved."},
            },
            "required": ["title"],
        },
    },
    {
        "name": "add_note",
        "description": "Save a design or construction detail / note (specs, dimensions, decisions, materials chosen).",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "category": {"type": "string", "enum": list(db.NOTE_CATEGORIES)},
            },
            "required": ["title"],
        },
    },
    {
        "name": "get_summary",
        "description": "Get the project's financial and progress summary (budget, spent, remaining, milestone progress, open issues).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_records",
        "description": "List recent records of a given type to answer questions or check details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["expenses", "payments", "milestones", "artisans", "issues", "notes"],
                },
            },
            "required": ["type"],
        },
    },
]


# --------------------------------------------------------------------------- #
# Tool execution against the database
# --------------------------------------------------------------------------- #
def _execute_tool(name: str, args: dict[str, Any], project_id: int) -> dict:
    if name == "add_expense":
        rec = db.add_expense(
            project_id,
            amount=float(args["amount"]),
            description=args.get("description", ""),
            category=args.get("category", "general") or "general",
            vendor=args.get("vendor", "") or "",
            spent_on=args.get("spent_on"),
            payment_status=args.get("payment_status", "paid") or "paid",
        )
        return {"ok": True, "saved": "expense", "record": rec}

    if name == "add_artisan":
        rec = db.add_artisan(
            project_id,
            name=args["name"],
            trade=args.get("trade", "") or "",
            phone=args.get("phone", "") or "",
            agreed_rate=args.get("agreed_rate"),
            notes=args.get("notes", "") or "",
        )
        return {"ok": True, "saved": "artisan", "record": rec}

    if name == "record_payment":
        artisan = db.find_artisan(project_id, args["artisan_name"])
        if artisan is None:
            artisan = db.add_artisan(
                project_id, name=args["artisan_name"], trade=args.get("trade", "") or "")
        rec = db.record_payment(
            project_id,
            amount=float(args["amount"]),
            artisan_name=artisan["name"],
            artisan_id=artisan["id"],
            description=args.get("description", "") or "",
            paid_on=args.get("paid_on"),
            status=args.get("status", "paid") or "paid",
        )
        return {"ok": True, "saved": "payment", "record": rec}

    if name == "add_milestone":
        rec = db.add_milestone(
            project_id,
            name=args["name"],
            description=args.get("description", "") or "",
            status=args.get("status", "not_started") or "not_started",
            target_date=args.get("target_date"),
        )
        return {"ok": True, "saved": "milestone", "record": rec}

    if name == "update_milestone":
        m = db.find_milestone(project_id, args["name"])
        if m is None:
            return {"ok": False, "error": f"No milestone matching '{args['name']}' was found."}
        rec = db.update_milestone(
            m["id"],
            status=args.get("status"),
            description=args.get("description"),
            target_date=args.get("target_date"),
        )
        return {"ok": True, "saved": "milestone", "record": rec}

    if name == "add_issue":
        rec = db.add_issue(
            project_id,
            title=args["title"],
            description=args.get("description", "") or "",
            severity=args.get("severity", "medium") or "medium",
        )
        return {"ok": True, "saved": "issue", "record": rec}

    if name == "resolve_issue":
        issue = db.find_issue(project_id, args["title"])
        if issue is None:
            return {"ok": False, "error": f"No open issue matching '{args['title']}' was found."}
        rec = db.resolve_issue(issue["id"], args.get("resolution", "") or "")
        return {"ok": True, "saved": "issue", "record": rec}

    if name == "add_note":
        rec = db.add_note(
            project_id,
            title=args["title"],
            content=args.get("content", "") or "",
            category=args.get("category", "general") or "general",
        )
        return {"ok": True, "saved": "note", "record": rec}

    if name == "get_summary":
        return {"ok": True, "summary": db.get_summary(project_id)}

    if name == "list_records":
        t = args.get("type")
        fns = {
            "expenses": db.list_expenses,
            "payments": db.list_payments,
            "milestones": db.list_milestones,
            "artisans": db.list_artisans,
            "issues": db.list_issues,
            "notes": db.list_notes,
        }
        if t not in fns:
            return {"ok": False, "error": f"Unknown record type '{t}'."}
        return {"ok": True, "type": t, "records": fns[t](project_id)}

    return {"ok": False, "error": f"Unknown tool '{name}'."}


def _system_prompt(project: dict) -> str:
    summary = db.get_summary(project["id"])
    cur = project.get("currency") or "$"
    return (
        "You are the assistant for a construction project tracker. You help the user "
        "keep a running record of expenses, payments to artisans, milestones, issues, "
        "and design/construction notes — and you answer questions about the project "
        "using its data.\n\n"
        f"Today's date is {date.today().isoformat()}.\n\n"
        "CURRENT PROJECT\n"
        f"- Name: {project['name']}\n"
        f"- Location: {project.get('location') or 'n/a'}\n"
        f"- Currency: {cur}\n"
        f"- Budget: {cur}{project.get('budget') or 0:,.0f}\n"
        f"- Spent so far: {cur}{summary.get('spent', 0):,.0f}"
        f" (remaining {cur}{summary.get('remaining', 0):,.0f})\n"
        f"- Outstanding/owed: {cur}{summary.get('outstanding', 0):,.0f}\n"
        f"- Milestones: {summary.get('milestones_done', 0)}/{summary.get('milestones_total', 0)} done\n"
        f"- Open issues: {summary.get('issues_open', 0)}\n\n"
        "HOW TO BEHAVE\n"
        "- When the user reports something that happened (a purchase, a payment, a "
        "completed phase, a problem, a decision), record it with the matching tool. "
        "You may call several tools in one turn if the user mentions several things.\n"
        "- Money paid to a named worker for labour -> record_payment. Money spent on "
        "materials/rentals/transport/permits -> add_expense.\n"
        f"- All amounts are in {cur}. If the user doesn't give a date, use today.\n"
        "- For questions, use get_summary or list_records to get real numbers — never "
        "guess. The figures above are a snapshot; re-check with a tool if precision matters.\n"
        "- After recording something, confirm briefly what you saved (one or two lines). "
        "Lead with the outcome. Don't narrate the tools you're about to call.\n"
        "- Be concise, friendly, and practical. Format money with the project's currency symbol."
    )


def _content_to_text(content: Any) -> str:
    """Collapse a stored assistant/user content value to plain text for history."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def chat(project_id: int, message: str, history: list[dict] | None = None) -> dict:
    """Run one chat turn. Returns {reply, actions} where actions lists what changed."""
    project = db.get_project(project_id)
    if not project:
        return {"reply": "That project could not be found.", "actions": []}

    client = get_client()

    messages: list[dict] = []
    for turn in (history or [])[-12:]:
        role = turn.get("role")
        text = _content_to_text(turn.get("content"))
        if role in ("user", "assistant") and text:
            messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": message})

    actions: list[dict] = []
    system = _system_prompt(project)

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            thinking={"type": "adaptive"},
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            reply = "".join(b.text for b in response.content if b.type == "text").strip()
            return {"reply": reply or "Done.", "actions": actions}

        # Echo the assistant turn (thinking + tool_use blocks) back verbatim.
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = _execute_tool(block.name, dict(block.input), project_id)
            if result.get("ok") and result.get("saved"):
                actions.append({"saved": result["saved"], "record": result.get("record")})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
                "is_error": not result.get("ok", True),
            })
        messages.append({"role": "user", "content": tool_results})

    return {
        "reply": "I logged what I could, but stopped after several steps. "
                 "Please check the dashboard and let me know if anything is missing.",
        "actions": actions,
    }
