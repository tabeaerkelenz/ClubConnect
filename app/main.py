from fastapi import FastAPI

from ClubConnect.app.auth.routes import router as auth_router
from ClubConnect.app.routers import clubs, users

app = FastAPI(title="ClubTrack API")
app.include_router(clubs.router)
app.include_router(auth_router)
app.include_router(users.router)


# to run: python -m uvicorn ClubConnect.app.main:app --reload
