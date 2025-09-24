# 🏋️‍️ ClubConnect
_The final backend Project of my Masterschool journey_


**ClubTrack** is a backend application for sports clubs.  
It helps **trainers** and **athletes** to organize training, track goals, and manage attendance.

---

## Features (MVP)

- Trainer and athlete management
- Create and manage training plans
- Track milestones and goals for athletes
- Record athlete attendance

---

## 🛠 Tech Stack

|  **Layer**   | **Tool/Library**         |
|----------|----------------------|
| Language | Python               |
| Framework | FastAPI              |
| ORM      | SQLAlchemy           |
| Database | PostgreSQL           |
| Migrations | Alembic              |
| Deployment | Render.com           |
| Auth     | JWT, OAuth2 Password Flow |
| Validation | Pydantic             |


---
## 🔗 Live Deployment

🔹 [https://clubconnect-0r4z.onrender.com](https://clubconnect-0r4z.onrender.com)  
_(Swagger UI available at `/docs`)_

---

## 📂 Project Structure 

```
.
└── ClubConnect
    ├── README.md
    ├── alembic/
    ├── alembic.ini
    ├── app/                     # see “Inside app/” below
    ├── env.example                   
    └── requirements.txt   
```
in `app/`:
```
# app/
├── __init__.py
├── main.py
├── auth/
│   ├── deps.py
│   ├── jwt_utils.py
│   └── routes.py
├── core/
│   ├── config.py
│   └── security.py
├── crud/
│   ├── user.py
│   └── plan.py                 # (more in repo)
├── db/
│   ├── database.py
│   └── models.py
├── routers/
│   ├── users.py
│   └── plans.py                # (more in repo)
├── schemas/
│   ├── user.py
│   └── plan.py                 # (more in repo)
└── services/
    ├── user.py
    └── plan.py                 # (more in repo)
```

## 🔧 Setup (local development)

1. Clone the repo  
   ```bash
   git clone https://github.com/<your-username>/clubtrack.git
   cd clubtrack
   ```
2. Set up a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment (copy and edit `.env` file)
   ```
   cp .env.example .env
   ```
5. Run database migrations
   ```bash
   alembic upgrade head
   ```

6. Launch API 
   ```bash
   uvicorn app.main:app --reload
   ```


## 🗺 Roadmap

- [x] Define a project idea
- [x] Database schema design
- [x] Database models for Trainer, Athlete, TrainingPlan, Goals, Attendance
- [x] CRUD operations for all entities
- [x] Authentication (JWT-based)
- [x] Role management (trainer vs. athlete)
- [x] Deployment on a cloud service (Heroku, Render, or Railway)
- [ ] Minimal frontend (planned for v2)
- [ ] Group plan assignments (v2)
- [ ] Notifications & dashboards (v2)

---
### 📬 Feedback?

If you have suggestions or questions, feel free to open an issue or reach out!

[More about me](https://github.com/tabeaerkelenz)
