#!/bin/sh
set -e
export PYTHONPATH=/app

echo "Waiting for database..."
sleep 2

echo "Initializing database..."
python scripts/init_db.py
python scripts/seed.py

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload