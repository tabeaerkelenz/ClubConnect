#!/usr/bin/env sh
set -e

echo "Starting ClubConnect API..."

# Optional: wait for DB to be ready (recommended)
if [ -n "${DATABASE_URL:-}" ]; then
  echo "Waiting for database to be reachable..."
  python - <<'PY'
import os, time
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
# Retry loop
for i in range(30):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("DB is ready.")
        break
    except Exception as e:
        print(f"DB not ready yet ({i+1}/30): {e}")
        time.sleep(1)
else:
    raise SystemExit("DB did not become ready in time")
PY
fi

echo "Running Alembic migrations..."
alembic upgrade head

echo "Launching API..."
exec "$@"
