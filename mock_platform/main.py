from datetime import datetime
from pathlib import Path
from string import Template

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

app = FastAPI(title="Mock Editing Platform")


@app.get("/", response_class=HTMLResponse)
def root() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page() -> HTMLResponse:
    return HTMLResponse(_render("login.html"))


@app.post("/login", response_class=HTMLResponse)
def login(username: str = Form(...), password: str = Form(...)) -> RedirectResponse:
    del username, password
    return RedirectResponse(url="/tasks/new", status_code=303)


@app.get("/tasks/new", response_class=HTMLResponse)
def create_task_page() -> HTMLResponse:
    return HTMLResponse(_render("create_task.html"))


@app.post("/tasks", response_class=HTMLResponse)
def create_task(
    video_path: str = Form(...),
    brand_name: str = Form(...),
    platform: str = Form(...),
    template_id: str = Form(...),
    title: str = Form(...),
    marketing_copy: str = Form(...),
    voiceover_script: str = Form(...),
) -> HTMLResponse:
    del video_path, brand_name, platform, template_id, title, marketing_copy, voiceover_script
    platform_job_id = f"MOCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    return HTMLResponse(_render("success.html", platform_job_id=platform_job_id))


@app.get("/status/{platform_job_id}", response_class=HTMLResponse)
def status_page(platform_job_id: str) -> HTMLResponse:
    return HTMLResponse(_render("status.html", platform_job_id=platform_job_id))


def _render(template_name: str, **values: str) -> str:
    template = Template((TEMPLATE_DIR / template_name).read_text(encoding="utf-8"))
    return template.safe_substitute(values)
