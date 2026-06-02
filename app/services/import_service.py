import csv
from io import StringIO

from pydantic import ValidationError
from sqlmodel import Session

from app.models import AdTask
from app.schemas import CSVImportResponse, TaskCreate


REQUIRED_COLUMNS = [
    "video_path",
    "brand_name",
    "product_type",
    "selling_points",
    "target_audience",
    "platform",
    "copy_style",
    "template_id",
]


class CSVImportError(ValueError):
    """Raised when a CSV cannot be imported as ad tasks."""


def import_tasks_from_csv_text(session: Session, csv_text: str) -> CSVImportResponse:
    reader = csv.DictReader(StringIO(csv_text))
    if reader.fieldnames is None:
        raise CSVImportError("CSV file is empty.")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
    if missing_columns:
        raise CSVImportError(f"Missing required columns: {', '.join(missing_columns)}")

    task_ids: list[int] = []
    for row_number, row in enumerate(reader, start=2):
        try:
            task_data = _parse_row(row)
        except ValidationError as exc:
            raise CSVImportError(f"Invalid data at row {row_number}: {exc.errors()}") from exc

        task = AdTask(**task_data.model_dump())
        session.add(task)
        session.flush()
        if task.id is not None:
            task_ids.append(task.id)

    if not task_ids:
        raise CSVImportError("CSV file does not contain any task rows.")

    session.commit()
    return CSVImportResponse(imported_count=len(task_ids), task_ids=task_ids)


def _parse_row(row: dict[str, str | None]) -> TaskCreate:
    normalized = {
        column: (row.get(column) or "").strip()
        for column in REQUIRED_COLUMNS
    }
    return TaskCreate.model_validate(normalized)
