from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import Settings
from app.models import AdCopy, AdTask, AutomationRun, TaskStatus
from app.services.automation_service import (
    AutomationSubmissionError,
    AutomationSubmissionPayload,
    submit_task_to_mock_platform,
)


class SuccessfulClient:
    def submit(
        self,
        payload: AutomationSubmissionPayload,
        *,
        screenshot_path: Path,
    ) -> str:
        assert payload.brand_name == "NovaFit"
        screenshot_path.write_bytes(b"fake png")
        return "MOCK-123"


class FailingClient:
    def submit(
        self,
        payload: AutomationSubmissionPayload,
        *,
        screenshot_path: Path,
    ) -> str:
        del payload, screenshot_path
        raise RuntimeError("mock platform is unavailable")


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def app_settings():
    return Settings(
        log_dir=Path("artifacts") / "logs" / "pytest",
        screenshot_dir=Path("artifacts") / "screenshots" / "pytest",
    )


def make_generated_task(session: Session) -> AdTask:
    task = AdTask(
        video_path="sample.mp4",
        brand_name="NovaFit",
        product_type="Smart watch",
        selling_points="long battery",
        target_audience="office workers",
        platform="TikTok",
        copy_style="energetic",
        template_id="TEMPLATE_FAST_01",
        status=TaskStatus.COPY_GENERATED.value,
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    ad_copy = AdCopy(
        task_id=task.id,
        title="NovaFit for busy mornings",
        marketing_copy="Start the day with stronger fitness habits.",
        selling_point_list='["long battery"]',
        voiceover_script="NovaFit keeps pace with your workday.",
        raw_llm_response="{}",
    )
    session.add(ad_copy)
    session.commit()
    session.refresh(task)
    return task


def test_submit_task_to_mock_platform_records_success(session, app_settings):
    task = make_generated_task(session)

    run = submit_task_to_mock_platform(
        session,
        task.id,
        client=SuccessfulClient(),
        app_settings=app_settings,
    )
    session.refresh(task)

    assert task.status == TaskStatus.SUBMITTED.value
    assert task.platform_job_id == "MOCK-123"
    assert run.status == TaskStatus.SUBMITTED.value
    assert run.finished_at is not None
    assert run.error_message is None
    assert run.log_path is not None
    assert run.screenshot_path is not None
    assert Path(run.log_path).exists()
    assert Path(run.screenshot_path).exists()


def test_submit_task_to_mock_platform_records_failure_artifacts(session, app_settings):
    task = make_generated_task(session)

    with pytest.raises(AutomationSubmissionError, match="mock platform is unavailable"):
        submit_task_to_mock_platform(
            session,
            task.id,
            client=FailingClient(),
            app_settings=app_settings,
        )
    session.refresh(task)

    run = session.exec(select(AutomationRun)).one()
    assert task.status == TaskStatus.FAILED.value
    assert task.error_message == "mock platform is unavailable"
    assert run.status == TaskStatus.FAILED.value
    assert run.finished_at is not None
    assert run.error_message == "mock platform is unavailable"
    assert run.log_path is not None
    assert run.screenshot_path is not None
    assert Path(run.log_path).exists()
    assert Path(run.screenshot_path).exists()


def test_retry_automation_increments_retry_count(session, app_settings):
    task = make_generated_task(session)
    task.status = TaskStatus.FAILED.value
    session.add(task)
    session.commit()
    session.refresh(task)

    submit_task_to_mock_platform(
        session,
        task.id,
        retry=True,
        client=SuccessfulClient(),
        app_settings=app_settings,
    )
    session.refresh(task)

    assert task.retry_count == 1
    assert task.status == TaskStatus.SUBMITTED.value
