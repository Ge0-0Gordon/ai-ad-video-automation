from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from app.config import Settings, settings
from app.models import AdCopy, AdTask, AutomationRun, TaskStatus
from app.services.task_state import retry_task, transition_task


class AutomationSubmissionError(RuntimeError):
    """Raised when mock-platform submission fails after task state is recorded."""


@dataclass(frozen=True)
class AutomationSubmissionPayload:
    video_path: str
    brand_name: str
    platform: str
    template_id: str
    title: str
    marketing_copy: str
    voiceover_script: str


class PlaywrightAutomationClient:
    def __init__(self, base_url: str = "http://localhost:8001") -> None:
        self.base_url = base_url.rstrip("/")

    def submit(
        self,
        payload: AutomationSubmissionPayload,
        *,
        screenshot_path: Path,
    ) -> str:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(f"{self.base_url}/login", wait_until="networkidle")
                page.get_by_test_id("username-input").fill("demo")
                page.get_by_test_id("password-input").fill("demo")
                page.get_by_test_id("login-submit").click()

                page.get_by_test_id("video-path-input").fill(payload.video_path)
                page.get_by_test_id("brand-name-input").fill(payload.brand_name)
                page.get_by_test_id("platform-input").fill(payload.platform)
                page.get_by_test_id("template-id-input").fill(payload.template_id)
                page.get_by_test_id("title-input").fill(payload.title)
                page.get_by_test_id("marketing-copy-input").fill(payload.marketing_copy)
                page.get_by_test_id("voiceover-script-input").fill(payload.voiceover_script)
                page.get_by_test_id("create-task-submit").click()

                job_id = page.get_by_test_id("platform-job-id").inner_text().strip()
                page.screenshot(path=str(screenshot_path), full_page=True)
                if not job_id:
                    raise AutomationSubmissionError("Mock platform did not return a platform_job_id.")
                return job_id
            except Exception:
                page.screenshot(path=str(screenshot_path), full_page=True)
                raise
            finally:
                browser.close()


def submit_task_to_mock_platform(
    session: Session,
    task_id: int,
    *,
    retry: bool = False,
    client: PlaywrightAutomationClient | None = None,
    app_settings: Settings = settings,
) -> AutomationRun:
    task = session.get(AdTask, task_id)
    if task is None:
        raise LookupError(f"Task {task_id} not found.")

    if retry:
        retry_task(task, TaskStatus.AUTOMATION_RUNNING)
    else:
        transition_task(task, TaskStatus.AUTOMATION_RUNNING)
    session.add(task)
    session.commit()
    session.refresh(task)

    run = AutomationRun(task_id=task.id, status=TaskStatus.AUTOMATION_RUNNING.value)
    session.add(run)
    session.commit()
    session.refresh(run)

    log_path = _run_artifact_path(app_settings.log_dir, run.id, "log")
    screenshot_path = _run_artifact_path(app_settings.screenshot_dir, run.id, "png")
    log_path.write_text(_format_log_line("started", task), encoding="utf-8")
    run.log_path = str(log_path)
    run.screenshot_path = str(screenshot_path)
    session.add(run)
    session.commit()

    try:
        ad_copy = _latest_copy_for_task(session, task.id)
        payload = _build_payload(task, ad_copy)
        active_client = client or PlaywrightAutomationClient()
        platform_job_id = active_client.submit(payload, screenshot_path=screenshot_path)

        transition_task(task, TaskStatus.SUBMITTED, platform_job_id=platform_job_id)
        run.status = TaskStatus.SUBMITTED.value
        run.finished_at = datetime.utcnow()
        session.add(task)
        session.add(run)
        session.commit()
        session.refresh(run)
        _append_log(log_path, _format_log_line("submitted", task, platform_job_id=platform_job_id))
        return run
    except Exception as exc:
        session.rollback()
        task = session.get(AdTask, task_id)
        run = session.get(AutomationRun, run.id)
        message = str(exc)
        if task is not None and task.status == TaskStatus.AUTOMATION_RUNNING.value:
            transition_task(task, TaskStatus.FAILED, error_message=message)
            session.add(task)
        if run is not None:
            run.status = TaskStatus.FAILED.value
            run.finished_at = datetime.utcnow()
            run.error_message = message
            run.log_path = str(log_path)
            if not screenshot_path.exists():
                _write_placeholder_png(screenshot_path)
            run.screenshot_path = str(screenshot_path)
            session.add(run)
        session.commit()
        _append_log(log_path, _format_log_line("failed", task, error_message=message))
        if isinstance(exc, AutomationSubmissionError):
            raise exc
        raise AutomationSubmissionError(message) from exc


def _latest_copy_for_task(session: Session, task_id: int | None) -> AdCopy:
    statement = (
        select(AdCopy)
        .where(AdCopy.task_id == task_id)
        .order_by(AdCopy.created_at.desc(), AdCopy.id.desc())
    )
    ad_copy = session.exec(statement).first()
    if ad_copy is None:
        raise AutomationSubmissionError(f"Task {task_id} has no generated ad copy.")
    return ad_copy


def _build_payload(task: AdTask, ad_copy: AdCopy) -> AutomationSubmissionPayload:
    return AutomationSubmissionPayload(
        video_path=task.video_path,
        brand_name=task.brand_name,
        platform=task.platform,
        template_id=task.template_id,
        title=ad_copy.title,
        marketing_copy=ad_copy.marketing_copy,
        voiceover_script=ad_copy.voiceover_script,
    )


def _run_artifact_path(directory: Path, run_id: int | None, suffix: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"automation_run_{run_id}.{suffix}"


def _format_log_line(
    event: str,
    task: AdTask | None,
    *,
    platform_job_id: str | None = None,
    error_message: str | None = None,
) -> str:
    parts = [f"event={event}"]
    if task is not None:
        parts.append(f"task_id={task.id}")
        parts.append(f"status={task.status}")
    if platform_job_id:
        parts.append(f"platform_job_id={platform_job_id}")
    if error_message:
        parts.append(f"error={error_message}")
    return " ".join(parts) + "\n"


def _append_log(path: Path, line: str) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(line)


def _write_placeholder_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
