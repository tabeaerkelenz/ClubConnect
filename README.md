# ClubConnect
_The final backend project of my Masterschool journey_

**ClubConnect** is a backend application for sports clubs.  
It helps **club coaches and members** to organize training, manage club memberships, track attendance, and generate AI-powered workout plans.

---

## Features

- User management with role-based access (JWT authentication)
- Club creation and management
- Club membership management
- Group management within clubs
- Training plan creation and assignment
- Session and exercise tracking
- Attendance recording
- AI-generated workout plans via OpenAI (feat/workoutplan — ready to merge)

---

## Tech Stack

| **Layer**        | **Tool/Library**                                         |
|------------------|----------------------------------------------------------|
| Language         | Python                                                   |
| Framework        | FastAPI                                                  |
| ORM              | SQLAlchemy                                               |
| Database         | PostgreSQL                                               |
| Migrations       | Alembic                                                  |
| Deployment       | Render.com                                               |
| Auth             | JWT, OAuth2 Password Flow                                |
| Validation       | Pydantic                                                 |
| Containerization | Docker                                                   |
| Orchestration    | Docker Compose                                           |
| Architecture     | Layered (Endpoints, Services, Repositories, Schemas, Models) |
| Startup Flow     | Deterministic startup chain (db -> migrate -> api)       |
| Testing          | Pytest (service-layer unit tests, mocked repositories)   |

---

## Live Deployment

[https://clubconnect-0r4z.onrender.com](https://clubconnect-0r4z.onrender.com)  
_(Swagger UI available at `/docs`)_

---

## Project Structure

```
.
└── ClubConnect/
    ├── README.md
    ├── alembic/
    ├── alembic.ini
    ├── app/
    ├── env.example
    └── requirements.txt
```

Inside `app/`:

```
app/
├── __init__.py
├── main.py
├── api/
│   └── endpoints/
│       ├── attendances.py
│       ├── clubs.py
│       ├── exercises.py
│       ├── group_memberships.py
│       ├── groups.py
│       ├── memberships.py
│       ├── plan_assignments.py
│       ├── plans.py
│       ├── sessions.py
│       └── users.py
├── auth/
│   ├── deps.py
│   ├── jwt_utils.py
│   └── routes.py
├── core/
│   ├── config.py
│   └── security.py
├── db/
│   └── database.py
├── exceptions/
│   └── base.py
├── models/
│   └── models.py
├── repositories/
├── schemas/
└── services/
    ├── attendance.py
    ├── club.py
    ├── exercise.py
    ├── group.py
    ├── group_membership.py
    ├── membership.py
    ├── plan.py
    ├── plan_assignment.py
    ├── session.py
    └── user.py
```

---

## Deployment & Setup (Docker)

ClubConnect runs as a fully containerized backend service.  
No local Python or PostgreSQL installation is required.

### Quickstart

```bash
git clone https://github.com/tabeaerkelenz/ClubConnect.git
cd ClubConnect
cp .env.example .env
docker compose up --build
```

### Open API documentation

- [http://localhost:8000/docs](http://localhost:8000/docs)

### Useful commands

```bash
docker compose down               # stop everything
docker compose down -v            # reset (data loss)
docker compose logs -f api        # view API logs
docker compose logs -f db         # view DB logs
docker compose run --rm migrate   # re-run migrations
```

---

## Setup (local development)

1. Clone the repo
   ```bash
   git clone https://github.com/tabeaerkelenz/ClubConnect.git
   cd ClubConnect
   ```

2. Set up a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment
   ```bash
   cp .env.example .env
   ```

5. Run database migrations
   ```bash
   alembic upgrade head
   ```

6. Launch the API
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Roadmap

- [x] Define project idea
- [x] Database schema design
- [x] Database models (User, Club, Membership, Group, Plan, Session, Exercise, Attendance)
- [x] Repository + service layer for all entities
- [x] Authentication (JWT-based)
- [x] Role management
- [x] Deployment on Render.com
- [x] AI-generated workout plans (feat/workoutplan — pending test coverage)
- [ ] Minimal frontend (v2)
- [ ] Group plan assignments (v2)
- [ ] Notifications & dashboards (v2)

---

### Feedback?

If you have suggestions or questions, feel free to open an issue or reach out!

[More to see...](https://github.com/tabeaerkelenz)
