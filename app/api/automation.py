from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.schemas import AutomationRunRead
from app.services.automation_service import (
    AutomationSubmissionError,
    submit_task_to_mock_platform,
)

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post("/{task_id}/submit", response_model=AutomationRunRead)
def submit_automation(task_id: int, session: Session = Depends(get_session)) -> AutomationRunRead:
    try:
        return submit_task_to_mock_platform(session, task_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AutomationSubmissionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/{task_id}/retry", response_model=AutomationRunRead)
def retry_automation(task_id: int, session: Session = Depends(get_session)) -> AutomationRunRead:
    try:
        return submit_task_to_mock_platform(session, task_id, retry=True)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AutomationSubmissionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
