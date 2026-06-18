# SiteLedger — AI Construction Project Tracker

Keep track of a building project's **expenses, progress, milestones, artisan
payments, issues, and design/construction notes** — by typing in plain English.

You type things like:

> "Paid James the mason $400 for the foundation today"
> "Bought 50 bags of cement for 600 from BuildMart, on credit"
> "Roofing milestone is done"
> "There's a crack in the east wall — high priority"

…and Claude logs each one into the right place. Then you can ask:

> "How much have I spent so far?"
> "Am I over budget?"
> "What issues are still open?"

…and it answers from your actual data. Everything also shows up on a live
dashboard you can open on your phone or computer.

---

## What it tracks

| Area | What you can log |
|------|------------------|
| 💸 **Expenses** | Materials, transport, rentals, permits — paid or on credit |
| 👷 **Artisan payments** | Payments to named workers (mason, carpenter, electrician…) |
| 🏗️ **Milestones** | Phases like Foundation, Roofing, Plastering — with status & dates |
| 🧱 **Artisans** | Your workers, their trades, rates, and how much they've been paid |
| ⚠️ **Issues** | Snags, defects, blockers — with severity and resolution |
| 📐 **Notes** | Design decisions, specs, dimensions, materials chosen |
| 📊 **Budget & progress** | Auto roll-up of spend vs budget and milestone completion |

---

## How it's built

- **Backend:** Python + [FastAPI](https://fastapi.tiangolo.com/) with a single-file
  SQLite database — no database server to install.
- **AI:** the [Claude API](https://platform.claude.com/) (`claude-opus-4-8`) using a
  tool-use loop, so plain-English messages turn into structured records and
  questions are answered from your data.
- **Frontend:** a responsive single-page dashboard (plain HTML/CSS/JS) that works
  on mobile and desktop.

```
server/        FastAPI app, database layer, and Claude integration
  db.py        SQLite schema + all data access
  agent.py     Claude tool definitions + the chat loop
  main.py      REST API + serves the frontend
web/           index.html, styles.css, app.js  (the dashboard + chat)
data/          your tracker.db lives here (created on first run, git-ignored)
```

---

## Run it

### 1. Add your API key
```bash
cp .env.example .env
# edit .env and paste your key from https://console.anthropic.com/settings/keys
```

### 2. Start it
Easiest (sets up a virtualenv, installs deps, launches):
```bash
./run.sh
```

Or manually:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server.main:app --reload
```

### 3. Open it
Go to **http://localhost:8000**, create a project, and start typing in the
assistant panel.

> The dashboard works even without an API key — you just won't be able to use the
> natural-language assistant until `ANTHROPIC_API_KEY` is set.

---

## Notes

- **Multiple projects** are supported — switch between them with the selector in
  the top bar.
- **Corrections:** every record on the dashboard has a 🗑 button if the assistant
  logs something wrong.
- **Your data stays local** in `data/tracker.db`. Back it up by copying that file.
  It's git-ignored by default so you don't accidentally commit project finances.
- **Currency** is set per project; the assistant formats amounts with your symbol.

---

## Costs

The assistant calls the Claude API, which is billed per token by Anthropic. Each
logged item or question is a small request. See
[Claude API pricing](https://platform.claude.com/) for current rates. The
dashboard and database themselves are free and run locally.
