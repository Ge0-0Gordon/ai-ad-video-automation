from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
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
