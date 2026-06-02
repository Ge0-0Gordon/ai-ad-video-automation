from fastapi import FastAPI

from app.api.tasks import router as tasks_router
from app.config import settings
from app.db import init_db
from app.utils.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    def on_startup() -> None:
        init_db()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(tasks_router)
    return app


app = create_app()
