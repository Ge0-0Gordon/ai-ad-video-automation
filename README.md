# AI Ad Video Automation

This project implements the backend foundation and copy-generation layer for a
batch AI ad-video automation MVP.

Current scope:
- CSV task import only.
- FastAPI task listing and detail endpoints.
- SQLite persistence through SQLModel.
- Centralized task status transition rules.
- Mock and OpenAI-compatible copy generation flow.
- Pytest coverage for CSV import, copy schema, copy service, and task state.

Not implemented yet:
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

## Phase 2 Copy Generation

Configure mock provider in `.env` or your shell:

```powershell
$env:LLM_PROVIDER="mock"
```

Mock is the default provider and does not require an API key. It produces
deterministic JSON so demos and tests are stable.

For KIMI / OpenAI-compatible mode:

```powershell
$env:LLM_PROVIDER="kimi"
$env:LLM_MODEL="moonshot-v1-8k"
$env:LLM_API_KEY="your-key"
$env:LLM_BASE_URL="https://api.moonshot.cn/v1"
```

Real API mode fails visibly if the API key, network call, provider response, or
Pydantic validation fails. It does not silently fall back to mock mode.

Start the backend:

```powershell
conda run -n learn-a uvicorn app.main:app --reload --port 8000
```

Import the sample CSV through Swagger UI:

```text
http://localhost:8000/docs
```

Then generate copy for the first imported task:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/copywriting/1/generate
```

Retry copy generation for a failed task:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/copywriting/1/retry
```

Phase 2 acceptance criteria:
- Mock provider can generate valid structured copy.
- Generated copy is saved in `ad_copies`.
- Task status moves `PENDING -> COPY_GENERATING -> COPY_GENERATED`.
- Invalid provider output moves the task to `COPY_FAILED`.
- KIMI / real OpenAI-compatible mode requires `LLM_API_KEY` and does not fallback to mock.
- Core tests pass with `conda run -n learn-a pytest`.

## Suggested Git Safety Net

This folder was created in a directory that is not currently a git repository.
Before larger edits, initialize git and make a baseline commit:

```powershell
git init
git add .
git commit -m "Initial phase 1 scaffold"
```
