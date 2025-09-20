from fastapi import FastAPI

from ClubConnect.app.auth.routes import router as auth_router
from ClubConnect.app.routers import clubs, users, memberships, plans, sessions, exercises, plan_assignments

app = FastAPI(title="ClubTrack API")

@app.get("/healthz")
def healthz():
    return {"ok": True}

app.include_router(clubs.router)
app.include_router(auth_router)
app.include_router(users.router)
app.include_router(memberships.clubs_memberships_router)    # specify the router name
app.include_router(memberships.memberships_router)
app.include_router(plans.router)
app.include_router(sessions.router)
app.include_router(exercises.exercises_router)
app.include_router(plan_assignments.router)

# to run from project root: python -m uvicorn ClubConnect.app.main:app --reload
# to run from git root: python -m uvicorn app.main:app --reload
