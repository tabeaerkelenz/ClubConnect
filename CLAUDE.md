# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the App

```bash
# Docker (recommended)
docker compose up --build

# Local
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Testing

```bash
pytest -q tests/unit                  # Unit tests only
pytest tests/                          # All tests
pytest --cov=app tests/               # With coverage

# Single test file
pytest tests/unit/services/test_users_services.py

# Single test function
pytest tests/unit/services/test_users_services.py::test_get_user_happy_path
```

### Linting

```bash
flake8 . --max-complexity=10 --max-line-length=127
```

### Database Migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Architecture

The app follows a strict 4-layer architecture. Every feature spans all four layers:

```
HTTP Request
    → api/endpoints/*.py       (route handlers, auth deps)
    → services/*.py            (business logic, permission checks)
    → repositories/*.py        (database queries)
    → models/models.py         (SQLAlchemy ORM entities)
```

### Key Directories

- `app/auth/` — JWT utilities, OAuth2 password flow, dependency factories for current user
- `app/core/config.py` — Pydantic Settings reading from `.env`
- `app/db/database.py` — Engine setup (PostgreSQL in prod, SQLite in tests)
- `app/exceptions/base.py` — Custom domain exceptions that auto-convert to HTTP responses
- `app/models/models.py` — All ORM models in one file; includes `TimestampMixin`
- `tests/conftest.py` — SQLite in-memory DB, TestClient, auth helper fixtures

### Exception Handling

Custom exceptions in `app/exceptions/base.py` (e.g., `NotFoundError`, `CoachRequiredError`, `RateLimitError`) are registered as handlers in `app/main.py` and automatically converted to JSON HTTP responses with the correct status codes. Raise these from services instead of returning error responses.

### Role-Based Access Control

Two orthogonal role systems:
- `UserRole` (`athlete`, `trainer`, `admin`) — global user type stored on `User`
- `MembershipRole` (`member`, `coach`, `owner`) — per-club role stored on `Membership`

Permission checks happen in the service layer, not in route handlers.

### AI Workout Plans

`POST /clubs/{club_id}/workout-plans/ai-draft` calls the OpenAI API to generate a workout plan. Daily quota is tracked in the database; exceeding it raises `RateLimitError`. Requires `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env`.

### Testing Patterns

- **Unit tests** (`tests/unit/`): Mock repositories via `unittest.mock`, test service logic in isolation
- **Integration tests** (`tests/integration/`): Full HTTP requests through FastAPI `TestClient` with a real SQLite in-memory DB
- Auth helpers in `tests/helpers_auth.py` provide reusable token/header factories

### Docker Startup Order

`docker-compose.yml` enforces: `db` (healthy) → `migrate` (runs `alembic upgrade head`) → `api` (starts uvicorn). The `entrypoint.sh` script routes on the `ROLE` env var (`migrate` or `api`).

## Environment Variables

Copy `.env.example` to `.env`. Required keys:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `OPENAI_API_KEY` | For AI workout plan generation |
| `OPENAI_MODEL` | e.g. `gpt-4` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime (default 30) |
