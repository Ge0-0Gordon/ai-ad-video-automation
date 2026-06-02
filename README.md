# AI Ad Video Automation

Phase 1 implements the backend foundation for a batch AI ad-video automation MVP.

Current scope:
- CSV task import only.
- FastAPI task listing and detail endpoints.
- SQLite persistence through SQLModel.
- Centralized task status transition rules.
- Pytest coverage for CSV import, copy schema, and task state.

Not implemented in Phase 1:
- LLM copy generation.
- Playwright automation.
- Mock editing platform.
- Streamlit dashboard.
- Excel import.

## Status Values

The MVP uses only:

```text
PENDING
COPY_GENERATING
COPY_GENERATED
COPY_FAILED
AUTOMATION_RUNNING
SUBMITTED
FAILED
```

`SUBMITTED` means the mock platform accepted the task and returned a `platform_job_id`.
There is no `SUCCESS` state in the first MVP.

Retries do not use a long-lived `RETRYING` state:
- Copy retry increments `retry_count` and re-enters `COPY_GENERATING`.
- Automation retry increments `retry_count` and re-enters `AUTOMATION_RUNNING`.

## Run Phase 1

Use the `learn-a` conda environment:

```powershell
conda run -n learn-a pytest
conda run -n learn-a uvicorn app.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Import sample CSV from an API client or Swagger UI:

```text
http://localhost:8000/docs
```

Upload:

```text
sample_data/sample_tasks.csv
```

## Suggested Git Safety Net

This folder was created in a directory that is not currently a git repository.
Before larger edits, initialize git and make a baseline commit:

```powershell
git init
git add .
git commit -m "Initial phase 1 scaffold"
```
