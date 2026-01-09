#!/bin/sh

alias uv="/root/.local/bin/uv"

# apply database migrations
echo "Applying database migrations..."
uv run alembic upgrade head

# run server
echo "Starting FastAPI server..."
uv run fastapi dev main.py --port 8000 --host 0.0.0.0