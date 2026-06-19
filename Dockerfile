# SiteLedger — construction project tracker
# Builds a self-contained image that runs the FastAPI app + static dashboard.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (.dockerignore keeps .venv, data and secrets out).
COPY . .

# Store the SQLite database on a mounted volume so data survives restarts.
ENV TRACKER_DB=/data/tracker.db

EXPOSE 8000

# Honour the platform-provided $PORT (Render/Railway/Fly) and fall back to 8000.
CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
