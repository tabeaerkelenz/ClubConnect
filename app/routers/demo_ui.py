from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os

router = APIRouter(tags=["demo-ui"])

@router.get("/demo", response_class=HTMLResponse)
def demo_page():
    demo_key = os.getenv("DEMO_API_KEY", "")
    key_header = f"'X-Demo-Key': '{demo_key}'," if demo_key else ""
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Run ClubConnect Demo</title>
<style>
  :root {{ --bg:#0b132b; --card:#1c2541; --accent:#3a86ff; --text:#e9ecef; }}
  html,body{{margin:0;height:100%;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto}}
  .wrap{{min-height:100%;display:grid;place-items:center;padding:2rem}}
  .card{{background:var(--card);padding:2rem 2.25rem;border-radius:18px;box-shadow:0 10px 30px rgba(0,0,0,.25);max-width:760px}}
  h1{{margin:0 0 .25rem;font-size:1.6rem}}
  p{{margin:.25rem 1px 1rem;opacity:.9}}
  button{{padding:.6rem 1rem;border-radius:12px;border:1px solid rgba(255,255,255,.2);background:var(--accent);color:#fff;cursor:pointer}}
  pre{{background:#0b1020;color:#d9e2ff;padding:12px;border-radius:8px;overflow:auto;max-height:50vh}}
</style>
<div class="wrap">
  <div class="card">
    <h1>Run Demo</h1>
    <p>This will create demo users, a club, a plan, and a session on the server.</p>
    <button id="runBtn">Run Demo</button>
    <a style="margin-left:.75rem" href="/docs">Swagger</a>
    <pre id="out">(results will appear here)</pre>
  </div>
</div>
<script>
  const out = document.getElementById('out');
  document.getElementById('runBtn').onclick = async () => {{
    out.textContent = "Running...";
    try {{
      const res = await fetch('/demo/run', {{
        method: 'POST',
        headers: {{
          {key_header}
          'Content-Type': 'application/json'
        }}
      }});
      const txt = await res.text();
      try {{
        out.textContent = JSON.stringify(JSON.parse(txt), null, 2);
      }} catch (_) {{
        out.textContent = txt;
      }}
    }} catch (err) {{
      out.textContent = "Error: " + err;
    }}
  }};
</script>
</html>"""
