from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def test_stop_times_file_exists():
    assert (SILVER_DIR / "stop_times.parquet").is_file()


def test_stop_times_not_empty():
    path = SILVER_DIR / "stop_times.parquet"

    with duckdb.connect() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM read_parquet(?)",
            [str(path)],
        ).fetchone()[0]

    assert count > 0


def test_required_fields_are_valid():
    path = SILVER_DIR / "stop_times.parquet"

    with duckdb.connect() as connection:
        invalid_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM read_parquet(?)
            WHERE trip_id IS NULL OR TRIM(trip_id) = ''
               OR stop_id IS NULL OR TRIM(stop_id) = ''
               OR stop_sequence IS NULL OR stop_sequence < 0
            """,
            [str(path)],
        ).fetchone()[0]

    assert invalid_count == 0


def test_stop_sequences_are_unique_per_trip():
    path = SILVER_DIR / "stop_times.parquet"

    with duckdb.connect() as connection:
        duplicates = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT trip_id, stop_sequence
                FROM read_parquet(?)
                GROUP BY trip_id, stop_sequence
                HAVING COUNT(*) > 1
            )
            """,
            [str(path)],
        ).fetchone()[0]

    assert duplicates == 0


def test_stop_times_have_valid_time_format():
    path = SILVER_DIR / "stop_times.parquet"

    with duckdb.connect() as connection:
        invalid_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM read_parquet(?)
            WHERE (
                arrival_time IS NOT NULL
                AND NOT regexp_full_match(
                    arrival_time,
                    '[0-9]+:[0-5][0-9]:[0-5][0-9]'
                )
            )
            OR (
                departure_time IS NOT NULL
                AND NOT regexp_full_match(
                    departure_time,
                    '[0-9]+:[0-5][0-9]:[0-5][0-9]'
                )
            )
            """,
            [str(path)],
        ).fetchone()[0]

    assert invalid_count == 0