import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from langchain_core.prompts import PromptTemplate
from pydantic import ValidationError
from sqlmodel import Session

from app.config import PROJECT_ROOT, Settings, settings
from app.models import AdCopy, AdTask, TaskStatus
from app.schemas import AdCopyStructuredOutput
from app.services.task_state import retry_task, transition_task


class CopyGenerationError(RuntimeError):
    """Raised when copy generation fails after task state has been recorded."""


class CopyProvider(ABC):
    @abstractmethod
    def generate(self, task: AdTask, prompt: str) -> str:
        """Return raw provider text. It must be JSON matching AdCopyStructuredOutput."""


class MockCopyProvider(CopyProvider):
    def generate(self, task: AdTask, prompt: str) -> str:
        # The mock provider is deterministic so demos and tests do not depend on a networked LLM.
        del prompt
        payload = {
            "title": f"{task.brand_name} for {task.target_audience}",
            "marketing_copy": (
                f"Meet {task.brand_name}, a {task.product_type} built for "
                f"{task.target_audience}. Highlights: {task.selling_points}."
            ),
            "selling_point_list": _split_selling_points(task.selling_points),
            "voiceover_script": (
                f"Looking for a {task.product_type} that fits your day? "
                f"{task.brand_name} brings {task.selling_points} in a {task.copy_style} style "
                f"made for {task.platform}."
            ),
        }
        return json.dumps(payload, ensure_ascii=False)


class OpenAICompatibleCopyProvider(CopyProvider):
    def __init__(self, app_settings: Settings) -> None:
        if not app_settings.llm_api_key:
            raise CopyGenerationError("LLM_API_KEY is required when LLM_PROVIDER is openai or kimi.")

        # Import lazily so Phase 1 and mock-mode tests do not require real API configuration.
        from langchain_openai import ChatOpenAI

        self.chat_model = ChatOpenAI(
            model=app_settings.llm_model,
            api_key=app_settings.llm_api_key,
            base_url=app_settings.llm_base_url,
        )

    def generate(self, task: AdTask, prompt: str) -> str:
        del task
        response = self.chat_model.invoke(prompt)
        return str(response.content)


def generate_copy_for_task(
    session: Session,
    task_id: int,
    *,
    retry: bool = False,
    provider: CopyProvider | None = None,
    app_settings: Settings = settings,
) -> AdCopy:
    task = session.get(AdTask, task_id)
    if task is None:
        raise LookupError(f"Task {task_id} not found.")

    if retry:
        retry_task(task, TaskStatus.COPY_GENERATING)
    else:
        transition_task(task, TaskStatus.COPY_GENERATING)
    session.add(task)
    session.commit()
    session.refresh(task)

    try:
        prompt = build_ad_copy_prompt(task)
        active_provider = provider or build_copy_provider(app_settings)
        raw_response = active_provider.generate(task, prompt)
        structured = parse_structured_copy(raw_response)
        ad_copy = _save_copy(session, task, structured, raw_response)
        transition_task(task, TaskStatus.COPY_GENERATED)
        session.add(task)
        session.commit()
        session.refresh(ad_copy)
        return ad_copy
    except Exception as exc:
        # Fail visibly: the task records the exact provider/parser error and the API returns 502.
        # Real API mode must not fall back to mock, because that would hide production failures.
        session.rollback()
        task = session.get(AdTask, task_id)
        if task is not None and task.status == TaskStatus.COPY_GENERATING.value:
            transition_task(task, TaskStatus.COPY_FAILED, error_message=str(exc))
            session.add(task)
            session.commit()
        if isinstance(exc, CopyGenerationError):
            raise exc
        raise CopyGenerationError(str(exc)) from exc


def build_copy_provider(app_settings: Settings = settings) -> CopyProvider:
    provider_name = app_settings.llm_provider.lower().strip()
    if provider_name == "mock":
        return MockCopyProvider()
    if provider_name in {"openai", "kimi"}:
        return OpenAICompatibleCopyProvider(app_settings)
    raise CopyGenerationError(f"Unsupported LLM_PROVIDER: {app_settings.llm_provider}")


def build_ad_copy_prompt(task: AdTask) -> str:
    prompt_template = PromptTemplate.from_template(_read_prompt_template())
    return prompt_template.format(
        brand_name=task.brand_name,
        product_type=task.product_type,
        selling_points=task.selling_points,
        target_audience=task.target_audience,
        platform=task.platform,
        copy_style=task.copy_style,
        template_id=task.template_id,
    )


def parse_structured_copy(raw_response: str) -> AdCopyStructuredOutput:
    data = _loads_json_object(raw_response)
    try:
        return AdCopyStructuredOutput.model_validate(data)
    except ValidationError as exc:
        raise CopyGenerationError(f"LLM output failed schema validation: {exc}") from exc


def _save_copy(
    session: Session,
    task: AdTask,
    structured: AdCopyStructuredOutput,
    raw_response: str,
) -> AdCopy:
    ad_copy = AdCopy(
        task_id=task.id,
        title=structured.title,
        marketing_copy=structured.marketing_copy,
        selling_point_list=json.dumps(structured.selling_point_list, ensure_ascii=False),
        voiceover_script=structured.voiceover_script,
        raw_llm_response=raw_response,
    )
    session.add(ad_copy)
    session.flush()
    return ad_copy


def _read_prompt_template() -> str:
    path = PROJECT_ROOT / "app" / "prompts" / "ad_copy_prompt.txt"
    return Path(path).read_text(encoding="utf-8")


def _loads_json_object(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CopyGenerationError(f"LLM output is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CopyGenerationError("LLM output must be a JSON object.")
    return data


def _split_selling_points(selling_points: str) -> list[str]:
    parts = [
        part.strip(" ;,")
        for part in selling_points.replace("；", ";").replace("，", ";").split(";")
    ]
    cleaned = [part for part in parts if part]
    return cleaned[:5] or [selling_points.strip()]
