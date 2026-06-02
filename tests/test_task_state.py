import pytest

from app.models import AdTask, TaskStatus
from app.services.task_state import retry_task, transition_task


def make_task(status: TaskStatus = TaskStatus.PENDING) -> AdTask:
    return AdTask(
        video_path="sample.mp4",
        brand_name="NovaFit",
        product_type="Smart watch",
        selling_points="long battery",
        target_audience="office workers",
        platform="TikTok",
        copy_style="energetic",
        template_id="T1",
        status=status.value,
    )


def test_transition_task_allows_phase_one_copy_flow():
    task = make_task()

    transition_task(task, TaskStatus.COPY_GENERATING)
    transition_task(task, TaskStatus.COPY_GENERATED)

    assert task.status == TaskStatus.COPY_GENERATED.value
    assert task.error_message is None


def test_transition_task_rejects_illegal_direct_submission():
    task = make_task()

    with pytest.raises(ValueError, match="PENDING -> SUBMITTED"):
        transition_task(task, TaskStatus.SUBMITTED)


def test_transition_task_records_failure_message():
    task = make_task()
    transition_task(task, TaskStatus.COPY_GENERATING)

    transition_task(task, TaskStatus.COPY_FAILED, error_message="LLM returned invalid JSON")

    assert task.status == TaskStatus.COPY_FAILED.value
    assert task.error_message == "LLM returned invalid JSON"


def test_retry_copy_increments_count_and_enters_copy_generating():
    task = make_task(TaskStatus.COPY_FAILED)

    retry_task(task, TaskStatus.COPY_GENERATING)

    assert task.retry_count == 1
    assert task.status == TaskStatus.COPY_GENERATING.value


def test_retry_automation_increments_count_and_enters_automation_running():
    task = make_task(TaskStatus.FAILED)

    retry_task(task, TaskStatus.AUTOMATION_RUNNING)

    assert task.retry_count == 1
    assert task.status == TaskStatus.AUTOMATION_RUNNING.value


def test_retry_rejects_submitted_as_long_term_retry_state():
    task = make_task(TaskStatus.FAILED)

    with pytest.raises(ValueError, match="COPY_GENERATING or AUTOMATION_RUNNING"):
        retry_task(task, TaskStatus.SUBMITTED)
