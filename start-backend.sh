#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"

cd "$BACKEND_DIR"

# Check uv is installed
if ! command -v uv &> /dev/null; then
  echo "uv not found. Install it with:"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

# Sync dependencies (creates .venv automatically if missing)
echo "Syncing dependencies with uv..."
uv sync

# Copy .env if missing
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "Created .env from .env.example — please add your API keys."
fi

echo ""
echo "Starting AI Presentation Coach backend on http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
