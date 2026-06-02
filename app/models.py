from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    COPY_GENERATING = "COPY_GENERATING"
    COPY_GENERATED = "COPY_GENERATED"
    COPY_FAILED = "COPY_FAILED"
    AUTOMATION_RUNNING = "AUTOMATION_RUNNING"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"


class AdTask(SQLModel, table=True):
    __tablename__ = "ad_tasks"

    id: int | None = Field(default=None, primary_key=True)
    video_path: str
    brand_name: str
    product_type: str
    selling_points: str
    target_audience: str
    platform: str
    copy_style: str
    template_id: str
    status: str = Field(default=TaskStatus.PENDING.value, index=True)
    retry_count: int = Field(default=0)
    error_message: str | None = Field(default=None)
    platform_job_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdCopy(SQLModel, table=True):
    __tablename__ = "ad_copies"

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="ad_tasks.id", index=True)
    title: str
    marketing_copy: str
    selling_point_list: str
    voiceover_script: str
    raw_llm_response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AutomationRun(SQLModel, table=True):
    __tablename__ = "automation_runs"

    id: int | None = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="ad_tasks.id", index=True)
    status: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = Field(default=None)
    screenshot_path: str | None = Field(default=None)
    log_path: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
