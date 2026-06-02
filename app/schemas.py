from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    video_path: str = Field(min_length=1)
    brand_name: str = Field(min_length=1)
    product_type: str = Field(min_length=1)
    selling_points: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    copy_style: str = Field(min_length=1)
    template_id: str = Field(min_length=1)


class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    retry_count: int
    error_message: str | None
    platform_job_id: str | None
    created_at: datetime
    updated_at: datetime


class CSVImportResponse(BaseModel):
    imported_count: int
    task_ids: list[int]


class AdCopyStructuredOutput(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    marketing_copy: str = Field(min_length=1, max_length=500)
    selling_point_list: list[str] = Field(min_length=1, max_length=5)
    voiceover_script: str = Field(min_length=1, max_length=1000)


class AdCopyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    title: str
    marketing_copy: str
    selling_point_list: str
    voiceover_script: str
    raw_llm_response: str
    created_at: datetime
