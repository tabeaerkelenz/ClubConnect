# ClubConnect

ClubConnect is a FastAPI backend for sports clubs. It helps trainers, coaches, and athletes manage clubs, memberships, training plans, exercise sessions, attendance, and AI-assisted workout plan drafts.

This project was built as the final backend project of my Masterschool software engineering journey and is designed to demonstrate production-oriented backend skills: authentication, database modeling, layered architecture, automated tests, Docker-based deployment, and API documentation.

## Live demo

Deployment: https://clubconnect-0r4z.onrender.com

API documentation:
https://clubconnect-0r4z.onrender.com/docs

Health check:
https://clubconnect-0r4z.onrender.com/healthz

Note: Render free-tier services may need a short warm-up after inactivity.

## Features

- User registration and JWT-based authentication
- Global user roles: athlete, trainer, admin
- Club creation and membership management
- Per-club membership roles: member, coach, owner
- Training plans, workout plans, exercises, and sessions
- Plan assignments for athletes and groups
- Attendance tracking with statuses such as present, absent, excused, and late
- AI workout plan draft endpoint using the OpenAI API
- Daily AI quota tracking
- Domain-specific exception handling with consistent HTTP responses
- PostgreSQL support for deployment and SQLite-based tests
- Alembic database migrations
- Docker Compose startup flow with database, migrations, and API service
- Unit and integration test coverage with pytest

## Tech stack

| Layer | Technology |
| --- | --- |
| Language | Python |
| API framework | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL, SQLite for tests |
| Migrations | Alembic |
| Authentication | JWT, OAuth2 password flow |
| Validation | Pydantic |
| Testing | pytest, pytest-cov |
| Containerization | Docker, Docker Compose |
| Deployment | Render |
| AI integration | OpenAI API |

## Architecture

ClubConnect follows a layered backend architecture:

```text
HTTP request
  -> app/api/endpoints/      FastAPI route handlers and dependencies
  -> app/services/           Business logic and permission checks
  -> app/repositories/       Database access and queries
  -> app/models/models.py    SQLAlchemy ORM models
```

The goal is to keep route handlers thin and place business rules in the service layer. Repository modules isolate database queries, which makes the service layer easier to unit test with mocks.

Key directories:

```text
.
├── app/
│   ├── api/endpoints/       API route modules
│   ├── auth/                JWT utilities, auth routes, auth dependencies
│   ├── core/                App configuration and shared dependencies
│   ├── db/                  Database engine/session setup
│   ├── exceptions/          Domain exceptions and error handling
│   ├── models/              SQLAlchemy models and enums
│   ├── repositories/        Database query layer
│   ├── schemas/             Pydantic request/response schemas
│   ├── services/            Business logic layer
│   └── main.py              FastAPI app setup and router registration
├── alembic/                 Database migrations
├── tests/                   Unit and integration tests
├── docker-compose.yml       Local container orchestration
├── Dockerfile               API image definition
└── requirements.txt         Python dependencies
```

## API overview

Main resource areas include:

- Auth and users
- Clubs and memberships
- Groups and group memberships
- Plans, workout plans, exercises, and sessions
- Plan assignments
- Attendance records
- AI workout plan drafts

For the full interactive API reference, open `/docs` on the live deployment or local server.

## Getting started with Docker

Docker is the recommended local setup because it starts PostgreSQL, runs migrations, and launches the API in a reproducible way.

```bash
git clone https://github.com/tabeaerkelenz/ClubConnect.git
cd ClubConnect
cp .env.example .env
docker compose up --build
```

Then open:

```text
http://localhost:8000/docs
```

Useful Docker commands:

```bash
docker compose down              # stop services
docker compose down -v           # stop services and delete database volume
docker compose logs -f api       # follow API logs
docker compose logs -f db        # follow database logs
docker compose run --rm migrate  # run migrations manually
```

## Local development without Docker

```bash
git clone https://github.com/tabeaerkelenz/ClubConnect.git
cd ClubConnect
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The local API will be available at:

```text
http://localhost:8000
```

## Environment variables

Create a `.env` file from `.env.example` and adjust the values for your environment.

| Variable | Purpose |
| --- | --- |
| POSTGRES_DB | PostgreSQL database name for Docker Compose |
| POSTGRES_USER | PostgreSQL user for Docker Compose |
| POSTGRES_PASSWORD | PostgreSQL password for Docker Compose |
| DATABASE_URL | SQLAlchemy database connection string |
| DEBUG | Enables debug behavior during development |
| SECRET_KEY | JWT signing secret |
| ALGORITHM | JWT signing algorithm, usually HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token lifetime |
| OPENAI_API_KEY | Required for AI workout plan generation |
| OPENAI_MODEL | OpenAI model used for workout plan drafts |

## Running tests

```bash
pytest -q tests/unit
pytest tests/
pytest --cov=app tests/
```

Current local baseline:

```text
146 passed, 1 skipped
```

## Design decisions

- Service-layer permission checks: authorization rules live close to business logic instead of being scattered across route handlers.
- Domain exceptions: services raise custom errors such as not-found or permission errors, and FastAPI exception handlers convert them into consistent JSON responses.
- Repository abstraction: database access is separated from business logic, which keeps service tests focused and easy to mock.
- Docker startup order: Docker Compose waits for the database, runs migrations, then starts the API service.
- AI quota tracking: AI workout plan generation is rate-limited through database-backed usage tracking.

## Roadmap

- Improve API documentation examples
- Add more integration tests for edge cases and permissions
- Add a small frontend or API demo client
- Expand dashboards and notifications
- Improve CI/CD visibility and deployment documentation

## Author

Built by Tabea Erkelenz as part of her software engineering portfolio.

GitHub: https://github.com/tabeaerkelenz
