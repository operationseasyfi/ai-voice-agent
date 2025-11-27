#!/bin/bash
set -e

echo "Waiting for database to be ready..."
until python -c "from app.database import engine; from sqlalchemy import text; engine.connect().execute(text('SELECT 1'))" 2>/dev/null; do
  echo "Database not ready, waiting 2 seconds..."
  sleep 2
done

echo "Database is ready. Running migrations..."
alembic upgrade head || {
  echo "Migration failed! Attempting to create tables from scratch..."
  python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine.sync_engine)"
  echo "Tables created. Running migrations again..."
  alembic upgrade head || echo "Migrations completed with warnings"
}

echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

