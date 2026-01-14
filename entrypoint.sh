#!/usr/bin/env sh
set -e

echo "Starting ClubConnect container..."

wait_for_db() {
  if [ -z "${DATABASE_URL:-}" ]; then
    echo "DATABASE_URL is not set"
    exit 1
  fi

  echo "Waiting for database to be reachable..."
  python - <<'PY'
import os, time
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
for i in range(30):
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("DB is ready.")
        raise SystemExit(0)
    except Exception as e:
        print(f"DB not ready yet ({i+1}/30): {e}")
        time.sleep(1)
raise SystemExit("DB did not become ready in time")
PY
}

ROLE="${ROLE:-api}"

case "$ROLE" in
  migrate)
    echo "ROLE=migrate → running migrations only"
    wait_for_db
    alembic upgrade head
    echo "Migrations finished."
    exit 0
    ;;
  api)
    echo "ROLE=api → starting API only"
    exec "$@"
    ;;
  *)
    echo "Unknown ROLE: $ROLE (use 'api' or 'migrate')"
    exit 1
    ;;
esac
