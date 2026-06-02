import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import Settings
from app.models import AdCopy, AdTask, TaskStatus
from app.services.copy_service import (
    CopyGenerationError,
    CopyProvider,
    generate_copy_for_task,
)


class InvalidJSONProvider(CopyProvider):
    def generate(self, task: AdTask, prompt: str) -> str:
        del task, prompt
        return "this is not json"


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
        selling_points="long battery; sleep insights; heart-rate tracking",
        target_audience="office workers",
        platform="TikTok",
        copy_style="energetic",
        template_id="T1",
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def test_generate_copy_for_task_uses_mock_provider_and_marks_generated(session):
    task = make_task(session)

    ad_copy = generate_copy_for_task(
        session,
        task.id,
        app_settings=Settings(llm_provider="mock"),
    )
    session.refresh(task)

    assert task.status == TaskStatus.COPY_GENERATED.value
    assert ad_copy.task_id == task.id
    assert ad_copy.title
    assert "NovaFit" in ad_copy.marketing_copy


def test_generate_copy_for_task_marks_copy_failed_on_invalid_provider_output(session):
    task = make_task(session)

    with pytest.raises(CopyGenerationError, match="not valid JSON"):
        generate_copy_for_task(session, task.id, provider=InvalidJSONProvider())
    session.refresh(task)

    copies = list(session.exec(select(AdCopy)))
    assert task.status == TaskStatus.COPY_FAILED.value
    assert "not valid JSON" in task.error_message
    assert copies == []


def test_kimi_mode_requires_api_key_and_does_not_fallback_to_mock(session):
    task = make_task(session)

    with pytest.raises(CopyGenerationError, match="LLM_API_KEY is required"):
        generate_copy_for_task(
            session,
            task.id,
            app_settings=Settings(llm_provider="kimi", llm_api_key=None),
        )
    session.refresh(task)

    assert task.status == TaskStatus.COPY_FAILED.value
    assert "LLM_API_KEY is required" in task.error_message
