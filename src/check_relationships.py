from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def check_relationships():
    stop_times = SILVER_DIR / "stop_times.parquet"
    trips = SILVER_DIR / "trips.parquet"
    stops = SILVER_DIR / "stops.parquet"

    for file in [stop_times, trips, stops]:
        if not file.is_file():
            raise FileNotFoundError(f"Missing file: {file}")

    with duckdb.connect() as connection:
        connection.execute(
            """
            CREATE VIEW stop_times AS
            SELECT * FROM read_parquet(?)
            """.replace("read_parquet(?)", f"read_parquet('{stop_times.as_posix()}')")
        )

        connection.execute(
            """
            CREATE VIEW trips AS
            SELECT trip_id FROM read_parquet(?)
            """.replace("read_parquet(?)", f"read_parquet('{trips.as_posix()}')")
        )

        connection.execute(
            """
            CREATE VIEW stops AS
            SELECT stop_id FROM read_parquet(?)
            """.replace("read_parquet(?)", f"read_parquet('{stops.as_posix()}')")
        )

        unknown_trips = connection.execute(
            """
            SELECT COUNT(*)
            FROM stop_times st
            WHERE NOT EXISTS (
                SELECT 1
                FROM trips t
                WHERE t.trip_id = st.trip_id
            )
            """
        ).fetchone()[0]

        unknown_stops = connection.execute(
            """
            SELECT COUNT(*)
            FROM stop_times st
            WHERE NOT EXISTS (
                SELECT 1
                FROM stops s
                WHERE s.stop_id = st.stop_id
            )
            """
        ).fetchone()[0]

    print("GTFS Referential Integrity Check")
    print("-" * 40)
    print(f"Unknown trip IDs: {unknown_trips:,}")
    print(f"Unknown stop IDs: {unknown_stops:,}")

    if unknown_trips == 0 and unknown_stops == 0:
        print("All relationships are valid.")
    else:
        raise ValueError("Referential integrity check failed.")


if __name__ == "__main__":
    check_relationships()