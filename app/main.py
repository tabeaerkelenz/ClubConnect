from fastapi import FastAPI
from ClubConnect.app.routers import club

app = FastAPI(title="ClubTrack API")
app.include_router(club.router)


# to run: python -m uvicorn ClubConnect.app.main:app --reload