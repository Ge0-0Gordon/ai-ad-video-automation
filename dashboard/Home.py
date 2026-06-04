from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st


DEFAULT_API_BASE_URL = "http://localhost:8000"


def main() -> None:
    st.set_page_config(page_title="AI Ad Video Automation", layout="wide")
    st.title("AI Ad Video Automation")

    api_base_url = st.sidebar.text_input("FastAPI URL", DEFAULT_API_BASE_URL).rstrip("/")
    if st.sidebar.button("Refresh"):
        st.rerun()

    render_import_panel(api_base_url)

    tasks = api_get(api_base_url, "/tasks", default=[])
    if not tasks:
        st.info("No tasks yet. Import a CSV to start the workflow.")
        return

    render_task_table(tasks)
    task_id = st.selectbox(
        "Task",
        [task["id"] for task in tasks],
        format_func=lambda value: format_task_option(tasks, value),
    )
    task = api_get(api_base_url, f"/tasks/{task_id}")
    if task:
        render_task_detail(api_base_url, task)


def render_import_panel(api_base_url: str) -> None:
    with st.expander("Import CSV", expanded=True):
        uploaded_file = st.file_uploader("CSV file", type=["csv"])
        if st.button("Import tasks", disabled=uploaded_file is None):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            response = api_post(api_base_url, "/tasks/import-csv", files=files)
            if response:
                st.success(f"Imported {response['imported_count']} task(s): {response['task_ids']}")
                st.rerun()


def render_task_table(tasks: list[dict[str, Any]]) -> None:
    st.subheader("Tasks")
    rows = [
        {
            "id": task["id"],
            "brand": task["brand_name"],
            "platform": task["platform"],
            "template": task["template_id"],
            "status": task["status"],
            "retry_count": task["retry_count"],
            "platform_job_id": task["platform_job_id"] or "",
        }
        for task in tasks
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def render_task_detail(api_base_url: str, task: dict[str, Any]) -> None:
    st.subheader(f"Task {task['id']} · {task['brand_name']}")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Status", task["status"])
    metric_columns[1].metric("Retries", task["retry_count"])
    metric_columns[2].metric("Platform", task["platform"])
    metric_columns[3].metric("Template", task["template_id"])

    if task.get("error_message"):
        st.error(task["error_message"])
    if task.get("platform_job_id"):
        st.success(f"Platform job id: {task['platform_job_id']}")

    render_action_buttons(api_base_url, task)

    left, right = st.columns(2)
    with left:
        render_copy_panel(api_base_url, task["id"])
    with right:
        render_automation_panel(api_base_url, task["id"])

    with st.expander("Task payload"):
        st.json(task)


def render_action_buttons(api_base_url: str, task: dict[str, Any]) -> None:
    status = task["status"]
    col1, col2, col3 = st.columns(3)

    if col1.button("Generate copy", disabled=status not in {"PENDING"}):
        if api_post(api_base_url, f"/copywriting/{task['id']}/generate"):
            st.rerun()

    if col2.button("Retry copy", disabled=status not in {"COPY_FAILED", "FAILED"}):
        if api_post(api_base_url, f"/copywriting/{task['id']}/retry"):
            st.rerun()

    automation_path = f"/automation/{task['id']}/submit"
    if status == "FAILED":
        automation_path = f"/automation/{task['id']}/retry"
    automation_disabled = status not in {"COPY_GENERATED", "FAILED"}
    if col3.button("Submit automation", disabled=automation_disabled):
        if api_post(api_base_url, automation_path):
            st.rerun()


def render_copy_panel(api_base_url: str, task_id: int) -> None:
    st.markdown("#### Generated copy")
    ad_copy = api_get(api_base_url, f"/copywriting/{task_id}/latest", default=None, quiet_404=True)
    if not ad_copy:
        st.caption("No generated copy yet.")
        return

    st.text_input("Title", value=ad_copy["title"], disabled=True)
    st.text_area("Marketing copy", value=ad_copy["marketing_copy"], disabled=True)
    st.text_area("Voiceover script", value=ad_copy["voiceover_script"], disabled=True)
    try:
        selling_points = json.loads(ad_copy["selling_point_list"])
    except json.JSONDecodeError:
        selling_points = [ad_copy["selling_point_list"]]
    st.write("Selling points")
    st.write(selling_points)


def render_automation_panel(api_base_url: str, task_id: int) -> None:
    st.markdown("#### Automation runs")
    runs = api_get(api_base_url, f"/automation/{task_id}/runs", default=[])
    if not runs:
        st.caption("No automation run yet.")
        return

    latest = runs[0]
    if latest.get("error_message"):
        st.error(latest["error_message"])
    st.write(
        {
            "status": latest["status"],
            "started_at": latest["started_at"],
            "finished_at": latest["finished_at"],
            "screenshot_path": latest["screenshot_path"],
            "log_path": latest["log_path"],
        }
    )
    st.dataframe(runs, hide_index=True, use_container_width=True)


def format_task_option(tasks: list[dict[str, Any]], task_id: int) -> str:
    task = next(task for task in tasks if task["id"] == task_id)
    return f"{task['id']} · {task['brand_name']} · {task['status']}"


def api_get(
    api_base_url: str,
    path: str,
    *,
    default: Any | None = None,
    quiet_404: bool = False,
) -> Any:
    try:
        response = requests.get(f"{api_base_url}{path}", timeout=15)
        if quiet_404 and response.status_code == 404:
            return default
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        if not quiet_404:
            st.error(f"GET {path} failed: {exc}")
        return default


def api_post(api_base_url: str, path: str, **kwargs: Any) -> Any | None:
    try:
        response = requests.post(f"{api_base_url}{path}", timeout=120, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        detail = getattr(exc.response, "text", "") if exc.response is not None else ""
        st.error(f"POST {path} failed: {exc} {detail}")
        return None


if __name__ == "__main__":
    main()
