from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db import get_session
from app.models import AdTask
from app.schemas import CSVImportResponse, TaskRead
from app.services.import_service import CSVImportError, import_tasks_from_csv_text

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/import-csv", response_model=CSVImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> CSVImportResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported in MVP phase 1.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
        return import_tasks_from_csv_text(session, text)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded.") from exc
    except CSVImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[TaskRead])
def list_tasks(session: Session = Depends(get_session)) -> list[AdTask]:
    statement = select(AdTask).order_by(AdTask.created_at.desc())
    return list(session.exec(statement))


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, session: Session = Depends(get_session)) -> AdTask:
    task = session.get(AdTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task
