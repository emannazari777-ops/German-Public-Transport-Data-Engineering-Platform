
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = PROJECT_ROOT / "sql" / "service_by_weekday.sql"


def test_calendar_exceptions_are_applied(tmp_path, monkeypatch):
    # Create a small, isolated project dataset.
    silver_dir = tmp_path / "data" / "silver"
    silver_dir.mkdir(parents=True)

    calendar = pd.DataFrame(
        [
            {
                "service_id": "S1",
                "monday": 1,
                "tuesday": 0,
                "wednesday": 0,
                "thursday": 0,
                "friday": 0,
                "saturday": 0,
                "sunday": 0,
                "start_date": "20261116",
                "end_date": "20261117",
            }
        ]
    )

    exceptions = pd.DataFrame(
        [
            {
                "service_id": "S1",
                "date": "20261116",
                "exception_type": 2,
            },
            {
                "service_id": "S1",
                "date": "20261117",
                "exception_type": 1,
            },
        ]
    )

    trips = pd.DataFrame(
        [
            {"trip_id": "T1", "service_id": "S1"},
            {"trip_id": "T2", "service_id": "S1"},
        ]
    )

    calendar.to_parquet(silver_dir / "calendar.parquet", index=False)
    exceptions.to_parquet(
        silver_dir / "calendar_dates.parquet",
        index=False,
    )
    trips.to_parquet(silver_dir / "trips.parquet", index=False)

    monkeypatch.chdir(tmp_path)

    query = SQL_FILE.read_text(encoding="utf-8")

    with duckdb.connect() as connection:
        result = connection.execute(query).df()

    # Monday's regular service was removed.
    assert "Monday" not in result["weekday_name"].tolist()

    # Tuesday's service was added through an exception.
    assert len(result) == 1
    assert result.iloc[0]["weekday_name"] == "Tuesday"
    assert result.iloc[0]["dates_with_service"] == 1
    assert result.iloc[0]["total_scheduled_trips"] == 2
    assert result.iloc[0]["average_trips_per_active_date"] == 2
