# 🏋️‍♀️ ClubConnect
The final backend Project of my Masterschool journey


**ClubTrack** is a backend application for sports clubs.  
It helps **trainers** and **athletes** to organize training, track goals, and manage attendance.

---

## 🚀 Features (MVP)

- Trainer and athlete management
- Create and manage training plans
- Track milestones and goals for athletes
- Record athlete attendance

---

## 🛠 Tech Stack

- **Backend Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic

---

## 📂 Project Structure (planned)

```
clubtrack/
│
├── app/                          
│   ├── __init__.py               # Make app a package
│   ├── main.py                   # FastAPI entry point
│   │
│   ├── core/                     # Core configs
│   │   ├── config.py             # Settings (DB URL, secrets, env vars)
│   │   └── security.py           # Password hashing, auth helpers
│   │
│   ├── db/                       # Database layer
│   │   ├── database.py           # DB connection + session
│   │   └── models.py             # SQLAlchemy models (Trainer, Athlete, etc.)
│   │
│   ├── schemas/                  # Pydantic schemas
│   │   ├── trainer.py
│   │   ├── athlete.py
│   │   ├── workoutplan.py
│   │   ├── goal.py
│   │   └── attendance.py
│   │
│   ├── crud/                     # CRUD operations (one file per entity)
│   │   ├── trainer.py
│   │   ├── athlete.py
│   │   ├── workoutplan.py
│   │   ├── goal.py
│   │   └── attendance.py
│   │
│   ├── routers/                  # API routes
│   │   ├── trainer.py
│   │   ├── athlete.py
│   │   ├── workoutplan.py
│   │   ├── goal.py
│   │   └── attendance.py
│   │
│   └── utils/                    # Utility functions (e.g. email, validation)
│
├── tests/                        # Unit and integration tests
│   ├── test_trainer.py
│   └── test_athlete.py
│
├── alembic/                      # Database migrations (if used)
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Example environment variables
├── .gitignore                    # Ignore venv, pycache, secrets
└── README.md                     # Project documentation
```

## 🔧 Setup (local development)

1. Clone the repo  
   ```bash
   git clone https://github.com/<your-username>/clubtrack.git
   cd clubtrack
   ```
2. create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server
   ```bash
   uvicorn app.main:app --reload
   ```

## 🚀 Roadmap

- [x] Define project idea
- [x] Database schema design
- [ ] Database models for Trainer, Athlete, TrainingPlan, Goals, Attendance
- [ ] CRUD operations for all entities
- [ ] Authentication (JWT-based)
- [ ] Role management (trainer vs. athlete)
- [ ] Deployment on a cloud service (Heroku, Render, or Railway)



