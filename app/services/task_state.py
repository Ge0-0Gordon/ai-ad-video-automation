from datetime import datetime

from app.models import AdTask, TaskStatus


ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.COPY_GENERATING},
    TaskStatus.COPY_GENERATING: {TaskStatus.COPY_GENERATED, TaskStatus.COPY_FAILED},
    TaskStatus.COPY_GENERATED: {TaskStatus.AUTOMATION_RUNNING},
    TaskStatus.COPY_FAILED: {TaskStatus.COPY_GENERATING},
    TaskStatus.AUTOMATION_RUNNING: {TaskStatus.SUBMITTED, TaskStatus.FAILED},
    TaskStatus.FAILED: {TaskStatus.AUTOMATION_RUNNING, TaskStatus.COPY_GENERATING},
    TaskStatus.SUBMITTED: set(),
}


def transition_task(
    task: AdTask,
    target_status: TaskStatus | str,
    *,
    error_message: str | None = None,
    platform_job_id: str | None = None,
) -> AdTask:
    current = _coerce_status(task.status)
    target = _coerce_status(target_status)
    allowed_targets = ALLOWED_TRANSITIONS[current]

    if target not in allowed_targets:
        raise ValueError(f"Illegal task status transition: {current.value} -> {target.value}")

    task.status = target.value
    task.error_message = error_message
    if platform_job_id is not None:
        task.platform_job_id = platform_job_id
    task.updated_at = datetime.utcnow()
    return task


def retry_task(task: AdTask, target_status: TaskStatus | str) -> AdTask:
    target = _coerce_status(target_status)
    if target not in {TaskStatus.COPY_GENERATING, TaskStatus.AUTOMATION_RUNNING}:
        raise ValueError("Retry target must be COPY_GENERATING or AUTOMATION_RUNNING.")

    task.retry_count += 1
    return transition_task(task, target)


def _coerce_status(status: TaskStatus | str) -> TaskStatus:
    if isinstance(status, TaskStatus):
        return status
    try:
        return TaskStatus(status)
    except ValueError as exc:
        raise ValueError(f"Unknown task status: {status}") from exc
