from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import AdCopy
from app.schemas import AdCopyRead
from app.services.copy_service import CopyGenerationError, generate_copy_for_task

router = APIRouter(prefix="/copywriting", tags=["copywriting"])


@router.post("/{task_id}/generate", response_model=AdCopyRead)
def generate_copy(task_id: int, session: Session = Depends(get_session)) -> AdCopyRead:
    try:
        return generate_copy_for_task(session, task_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CopyGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{task_id}/retry", response_model=AdCopyRead)
def retry_copy_generation(task_id: int, session: Session = Depends(get_session)) -> AdCopyRead:
    try:
        return generate_copy_for_task(session, task_id, retry=True)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CopyGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{task_id}/latest", response_model=AdCopyRead)
def get_latest_copy(task_id: int, session: Session = Depends(get_session)) -> AdCopy:
    statement = (
        select(AdCopy)
        .where(AdCopy.task_id == task_id)
        .order_by(AdCopy.created_at.desc(), AdCopy.id.desc())
    )
    ad_copy = session.exec(statement).first()
    if ad_copy is None:
        raise HTTPException(status_code=404, detail="Generated copy not found for this task.")
    return ad_copy
