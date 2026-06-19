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
  seed.py      pre-loads the Ibafo pool project on a fresh database
  main.py      REST API + serves the frontend
web/           index.html, styles.css, app.js  (the dashboard + chat)
data/          your tracker.db lives here (created on first run, git-ignored)
Dockerfile     container image for hosting
render.yaml    one-click Render deploy (shared, online)
```

> **Pre-loaded project:** on a fresh database the app automatically creates the
> **Swimming Pool — Ibafo** project, with its 13 build stages, the cost breakdown
> and payment schedule, and the client-supply materials list — all from the Dova
> Futures quote. Set `SEED_POOL=0` to start empty instead.

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

## Put it online (shared & live)

Host it once and both you and your partner open the **same URL** on your phones —
whatever one of you logs, the other sees on refresh. The pool project is already
seeded, so the dashboard is populated the moment it's live.

### Option A — Render (easiest)
1. Push this repo to GitHub (already done if you're reading this there).
2. In [Render](https://render.com): **New + → Blueprint**, pick this repo. It reads
   `render.yaml` and sets everything up.
3. Open the service's **Environment** tab and add `ANTHROPIC_API_KEY` (from
   <https://console.anthropic.com/settings/keys>) to enable the assistant.
4. Visit the `*.onrender.com` URL Render gives you — share it with your partner.

The blueprint mounts a **persistent disk** at `/data` so your data survives
restarts and redeploys. That needs a paid instance (~$7/mo). To trial for free,
edit `render.yaml`: set `plan: free` and remove the `disk:` block — but free
instances reset their storage when they sleep, so don't keep months of data there.

### Option B — any Docker host (Railway, Fly.io, a VPS)
```bash
docker build -t siteledger .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v $(pwd)/data:/data \
  siteledger
```
The `-v …:/data` mount keeps the SQLite database on the host so it persists.
On Fly.io use a [volume](https://fly.io/docs/volumes/) mounted at `/data` for
free, durable storage — a good fit for SQLite.

### Option C — same Wi-Fi only
If you both just need access at home/site, run it on one machine and bind to the
network, then open `http://<that-machine-ip>:8000` from the other phone:
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

> **Keep the URL private** unless you add a password — anyone with the link can
> view and edit the project. Ask me if you'd like simple login protection added.

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
