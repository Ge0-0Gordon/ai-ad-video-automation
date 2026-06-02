import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import AdTask, TaskStatus
from app.services.import_service import CSVImportError, import_tasks_from_csv_text


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_import_tasks_from_csv_text_creates_pending_tasks(session):
    csv_text = (
        "video_path,brand_name,product_type,selling_points,target_audience,platform,copy_style,template_id\n"
        "sample.mp4,NovaFit,Smart watch,long battery,office workers,TikTok,energetic,T1\n"
        "sample.mp4,GlowTea,Tea,low caffeine,professionals,Instagram,warm,T2\n"
    )

    result = import_tasks_from_csv_text(session, csv_text)

    tasks = list(session.exec(select(AdTask).order_by(AdTask.id)))
    assert result.imported_count == 2
    assert result.task_ids == [task.id for task in tasks]
    assert [task.status for task in tasks] == [TaskStatus.PENDING.value, TaskStatus.PENDING.value]
    assert all(task.retry_count == 0 for task in tasks)


def test_import_tasks_from_csv_text_rejects_missing_required_column(session):
    csv_text = (
        "video_path,brand_name,product_type,selling_points,target_audience,platform,copy_style\n"
        "sample.mp4,NovaFit,Smart watch,long battery,office workers,TikTok,energetic\n"
    )

    with pytest.raises(CSVImportError, match="Missing required columns: template_id"):
        import_tasks_from_csv_text(session, csv_text)


def test_import_tasks_from_csv_text_rejects_blank_required_value(session):
    csv_text = (
        "video_path,brand_name,product_type,selling_points,target_audience,platform,copy_style,template_id\n"
        "sample.mp4,,Smart watch,long battery,office workers,TikTok,energetic,T1\n"
    )

    with pytest.raises(CSVImportError, match="Invalid data at row 2"):
        import_tasks_from_csv_text(session, csv_text)
