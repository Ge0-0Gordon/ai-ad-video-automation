from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.automation import list_automation_runs
from app.api.copywriting import get_latest_copy
from app.models import AdCopy, AdTask, AutomationRun, TaskStatus


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


def make_task(session: Session) -> AdTask:
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
    return task


def test_get_latest_copy_returns_newest_copy(session):
    task = make_task(session)
    old_copy = AdCopy(
        task_id=task.id,
        title="Old title",
        marketing_copy="Old copy",
        selling_point_list="[]",
        voiceover_script="Old voiceover",
        raw_llm_response="{}",
        created_at=datetime(2026, 1, 1),
    )
    new_copy = AdCopy(
        task_id=task.id,
        title="New title",
        marketing_copy="New copy",
        selling_point_list="[]",
        voiceover_script="New voiceover",
        raw_llm_response="{}",
        created_at=datetime(2026, 1, 2),
    )
    session.add(old_copy)
    session.add(new_copy)
    session.commit()

    result = get_latest_copy(task.id, session)

    assert result.title == "New title"


def test_get_latest_copy_raises_404_when_missing(session):
    task = make_task(session)

    with pytest.raises(HTTPException) as exc_info:
        get_latest_copy(task.id, session)

    assert exc_info.value.status_code == 404


def test_list_automation_runs_returns_newest_first(session):
    task = make_task(session)
    old_run = AutomationRun(
        task_id=task.id,
        status=TaskStatus.FAILED.value,
        started_at=datetime(2026, 1, 1),
    )
    new_run = AutomationRun(
        task_id=task.id,
        status=TaskStatus.SUBMITTED.value,
        started_at=datetime(2026, 1, 2),
    )
    session.add(old_run)
    session.add(new_run)
    session.commit()

    runs = list_automation_runs(task.id, session)

    assert [run.status for run in runs] == [TaskStatus.SUBMITTED.value, TaskStatus.FAILED.value]
