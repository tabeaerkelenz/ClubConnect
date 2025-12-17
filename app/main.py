from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse

from app.auth.routes import router as auth_router
from app.exceptions.base import DomainError
from app.api.endpoints import (
    clubs,
    plans,
    plan_assignments,
    attendances,
)
from app.api.endpoints import users, exercises, group_memberships, groups, memberships, sessions
def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_req: Request, exc: DomainError):
        return JSONResponse(
            status_code=getattr(exc, "status_code", 500),
            content={"detail": str(exc)},
        )


app = FastAPI(title="ClubTrack API")

register_exception_handlers(app)

@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def welcome():
    return """
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClubTrack API</title>
<style>
  :root { --bg:#0b132b; --card:#1c2541; --accent:#3a86ff; --text:#e9ecef; }
  html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto;}
  .wrap{min-height:100%;display:grid;place-items:center;padding:2rem}
  .card{background:var(--card);padding:2rem 2.25rem;border-radius:18px;box-shadow:0 10px 30px rgba(0,0,0,.25);max-width:680px}
  h1{margin:0 0 .25rem;font-size:1.6rem}
  p{margin:.25rem 0 1.25rem;opacity:.9}
  .links{display:flex;gap:.75rem;flex-wrap:wrap}
  a{display:inline-block;padding:.6rem .9rem;border-radius:12px;text-decoration:none;background:var(--accent);color:white}
  a.secondary{background:transparent;border:1px solid rgba(255,255,255,.2)}
</style>
<div class="wrap">
  <div class="card">
    <h1>✅ ClubTrack API is running</h1>
    <p>Your backend is deployed and healthy.</p>
    <div class="links">
      <a href="/docs">Open Swagger Docs</a>
      <a class="secondary" href="/healthz">Health Check</a>
      <a class="secondary" href="/demo">Demo</a>
    </div>
  </div>
</div>
</html>
"""


app.include_router(clubs.router)
app.include_router(auth_router)
app.include_router(users.router)
app.include_router(memberships.clubs_memberships_router)
app.include_router(memberships.memberships_router)
app.include_router(plans.router)
app.include_router(sessions.router)
app.include_router(exercises.exercises_router)
app.include_router(plan_assignments.router)
app.include_router(groups.router)
app.include_router(group_memberships.router)
app.include_router(attendances.router)


# to run from project root: python -m uvicorn ClubConnect.app.main:app --reload
# to run from git root: python -m uvicorn app.main:app --reload
# to run render demo: TS=$(date +%s) BASE_URL="https://clubconnect-0r4z.onrender.com" ./demo.sh
