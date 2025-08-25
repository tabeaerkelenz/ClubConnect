from fastapi import FastAPI

app = FastAPI(title="ClubTrack API")

# restore routes later to crud and routes
@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}


# to run: uvicorn app.main:app --reload