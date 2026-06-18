#!/usr/bin/env bash
# Convenience launcher for SiteLedger.
set -e

cd "$(dirname "$0")"

# Create a virtual environment on first run
if [ ! -d ".venv" ]; then
  echo "Setting up virtual environment…"
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip >/dev/null
  ./.venv/bin/pip install -r requirements.txt
fi

if [ ! -f ".env" ]; then
  echo "⚠  No .env file found. Copy .env.example to .env and add your ANTHROPIC_API_KEY"
  echo "   (the dashboard still works without it; the assistant will be offline)."
fi

echo "Starting SiteLedger on http://localhost:8000"
exec ./.venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000 "$@"
