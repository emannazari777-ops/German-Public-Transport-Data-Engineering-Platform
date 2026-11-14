from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def clean_stop_times():
    source = BRONZE_DIR / "stop_times.txt"
    destination = SILVER_DIR / "stop_times.parquet"

    if not source.is_file():
        raise FileNotFoundError(
            f"Source file not found: {source}"
        )

    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    # Safely quote file paths for SQL statements.
    source_path = "'" + str(source).replace("'", "''") + "'"
    output_path = "'" + str(destination).replace("'", "''") + "'"

    with duckdb.connect() as connection:

        # Create a view without loading the full CSV into memory.
        connection.execute(
            f"""
            CREATE TEMP VIEW stop_times AS
            SELECT
                TRIM(trip_id) AS trip_id,
                TRIM(stop_id) AS stop_id,
                TRY_CAST(stop_sequence AS INTEGER) AS stop_sequence,
                NULLIF(TRIM(arrival_time), '') AS arrival_time,
                NULLIF(TRIM(departure_time), '') AS departure_time,
                pickup_type,
                drop_off_type,
                stop_headsign
            FROM read_csv(
                {source_path},
                all_varchar = true,
                header = true
            )
            """
        )

        # Count source records.
        total_rows = connection.execute(
            "SELECT COUNT(*) FROM stop_times"
        ).fetchone()[0]

        print(f"Input records: {total_rows:,}")

        # Validate required identifiers and stop sequence.
        invalid_ids = connection.execute(
            """
            SELECT COUNT(*)
            FROM stop_times
            WHERE trip_id IS NULL
               OR trip_id = ''
               OR stop_id IS NULL
               OR stop_id = ''
               OR stop_sequence IS NULL
               OR stop_sequence < 0
            """
        ).fetchone()[0]

        if invalid_ids:
            raise ValueError(
                f"Found {invalid_ids:,} invalid stop-time identifiers"
            )

        # GTFS times can exceed 24:00:00.
        # Validate the time format without restricting hours to 0-23.
        invalid_times = connection.execute(
            """
            SELECT COUNT(*)
            FROM stop_times
            WHERE
                (
                    arrival_time IS NOT NULL
                    AND NOT regexp_full_match(
                        arrival_time,
                        '[0-9]+:[0-5][0-9]:[0-5][0-9]'
                    )
                )
                OR
                (
                    departure_time IS NOT NULL
                    AND NOT regexp_full_match(
                        departure_time,
                        '[0-9]+:[0-5][0-9]:[0-5][0-9]'
                    )
                )
            """
        ).fetchone()[0]

        if invalid_times:
            raise ValueError(
                f"Found {invalid_times:,} invalid time values"
            )

        # Ensure a trip does not have duplicate stop sequences.
        duplicate_sequences = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT trip_id, stop_sequence
                FROM stop_times
                GROUP BY trip_id, stop_sequence
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        if duplicate_sequences:
            raise ValueError(
                f"Found {duplicate_sequences:,} duplicate trip sequences"
            )

        # Write to a temporary file first to avoid incomplete output.
        temporary_destination = destination.with_suffix(".tmp.parquet")
        temporary_path = (
            "'" + str(temporary_destination).replace("'", "''") + "'"
        )

        try:
            connection.execute(
                f"""
                COPY (
                    SELECT *
                    FROM stop_times
                )
                TO {temporary_path}
                (FORMAT PARQUET, COMPRESSION ZSTD)
                """
            )

            # Replace the final output only after successful export.
            temporary_destination.replace(destination)

        finally:
            if temporary_destination.exists():
                temporary_destination.unlink()

    print("-" * 45)
    print("Silver layer: stop_times")
    print(f"Input records: {total_rows:,}")
    print(f"Output records: {total_rows:,}")
    print(f"Saved to: {destination}")
    print("Stop times processing completed successfully.")


if __name__ == "__main__":
    clean_stop_times()