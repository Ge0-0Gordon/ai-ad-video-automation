# AI Ad Video Automation

This project implements the backend foundation and copy-generation layer for a
batch AI ad-video automation MVP.

Current scope:
- CSV task import only.
- FastAPI task listing and detail endpoints.
- SQLite persistence through SQLModel.
- Centralized task status transition rules.
- Mock and OpenAI-compatible copy generation flow.
- Mock editing platform for Playwright submission.
- FastAPI automation submission and retry endpoints.
- Streamlit dashboard that drives the workflow through FastAPI only.
- Pytest coverage for CSV import, copy schema, copy service, task state, automation state records, and dashboard read APIs.

Not implemented yet:
- Excel import.
- Playwright e2e pytest.

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

## Phase 3 Mock Platform and Automation

Install Python dependencies after pulling Phase 3:

```powershell
conda run -n learn-a pip install -e ".[dev]"
```

Install the Playwright browser used by the automation service:

```powershell
conda run -n learn-a python -m playwright install chromium
```

Start the backend in one terminal:

```powershell
conda run -n learn-a uvicorn app.main:app --reload --port 8000
```

Start the mock editing platform in a second terminal:

```powershell
conda run -n learn-a uvicorn mock_platform.main:app --reload --port 8001
```

Manual Phase 1 -> Phase 2 -> Phase 3 test:

1. Open `http://localhost:8000/docs`.
2. Use `POST /tasks/import-csv` to upload `sample_data/sample_tasks.csv`.
3. Use `POST /copywriting/1/generate` to generate structured copy for task `1`.
4. Open `http://localhost:8001/login` and manually verify the mock platform can log in and submit a task.
5. Use `POST /automation/1/submit` to run Playwright against the mock platform.
6. Confirm `GET /tasks/1` shows `status=SUBMITTED` and a non-empty `platform_job_id`.
7. Confirm the returned automation run includes `screenshot_path` and `log_path`.

Automation retry for a failed task:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/automation/1/retry
```

Phase 3 acceptance criteria:
- The mock platform exposes login, task creation, success, and status pages.
- Mock page selectors use `data-testid`.
- Playwright submits a `COPY_GENERATED` task to the mock platform.
- Successful submission moves the task to `SUBMITTED` and saves `platform_job_id`.
- Failed submission moves the task to `FAILED` and saves error, screenshot path, and log path.

## Phase 4 Dashboard and Demo

Install dependencies:

```powershell
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Start the mock editing platform:

```powershell
python -m uvicorn mock_platform.main:app --reload --port 8001
```

Start the dashboard:

```powershell
python -m streamlit run dashboard/Home.py
```

Manual Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 test:

1. Open the Streamlit URL printed by the dashboard command.
2. Confirm the sidebar FastAPI URL is `http://localhost:8000`.
3. Upload `sample_data/sample_tasks.csv` in the Import CSV panel.
4. Select the first imported task and click `Generate copy`.
5. Confirm the generated title, marketing copy, selling points, and voiceover script appear in the dashboard.
6. Click `Submit automation`.
7. Confirm task status changes to `SUBMITTED` and a `platform_job_id` appears.
8. Confirm automation run details show `screenshot_path` and `log_path`.
9. For failure demo, stop the mock platform, submit a `COPY_GENERATED` task, and confirm the dashboard shows `FAILED`, error text, and artifact paths.
10. Restart the mock platform and use `Submit automation` on the failed task to retry.

Interview demo script:

1. Explain the business problem: ad teams need to batch create copy, fill platform forms, submit jobs, and track failures.
2. Show the architecture: CSV import, mock/real LLM provider, Pydantic validation, Playwright automation, SQLite state, Streamlit dashboard.
3. Import the sample CSV and point out `PENDING` tasks.
4. Generate copy and show structured fields instead of free-form text.
5. Submit automation and show Playwright returning `platform_job_id`.
6. Show failure visibility: status, `error_message`, screenshot path, log path, and retry count.
7. Summarize the project as an AI workflow integration MVP, not a video model.

Playwright e2e pytest remains optional and is not required for the MVP. The repeatable manual dashboard flow above is the Phase 4 verification path.

## Suggested Git Safety Net

This folder was created in a directory that is not currently a git repository.
Before larger edits, initialize git and make a baseline commit:

```powershell
git init
git add .
git commit -m "Initial phase 1 scaffold"
```
