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
    log_dir: Path = Path(os.getenv("LOG_DIR", PROJECT_ROOT / "artifacts" / "logs"))
    screenshot_dir: Path = Path(
        os.getenv("SCREENSHOT_DIR", PROJECT_ROOT / "artifacts" / "screenshots")
    )


settings = Settings()
