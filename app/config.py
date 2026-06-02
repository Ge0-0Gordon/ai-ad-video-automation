from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Ad Video Automation"
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{PROJECT_ROOT / 'app.db'}",
    )
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_model: str = os.getenv("LLM_MODEL", "moonshot-v1-8k")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    llm_base_url: str | None = os.getenv("LLM_BASE_URL")
    log_dir: Path = Path(os.getenv("LOG_DIR", PROJECT_ROOT / "artifacts" / "logs"))
    screenshot_dir: Path = Path(
        os.getenv("SCREENSHOT_DIR", PROJECT_ROOT / "artifacts" / "screenshots")
    )


settings = Settings()
