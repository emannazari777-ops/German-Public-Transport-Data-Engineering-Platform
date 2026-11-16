
"""Load the Gold stop_connectivity dataset into PostgreSQL."""

from pathlib import Path

import pandas as pd
import psycopg

from load_gold_to_postgres import load_database_password


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = (
    PROJECT_ROOT / "data" / "gold" / "stop_connectivity.parquet"
)

EXPECTED_COLUMNS = [
    "stop_id",
    "stop_name",
    "distinct_route_count",
    "scheduled_trip_count",
    "scheduled_stop_events",
]

COUNT_COLUMNS = [
    "distinct_route_count",
    "scheduled_trip_count",
    "scheduled_stop_events",
]


def load_gold_data() -> pd.DataFrame:
    """Read and validate the Stop Connectivity dataset."""

    if not PARQUET_PATH.is_file():
        raise FileNotFoundError(
            f"Gold dataset not found: {PARQUET_PATH}"
        )

    dataframe = pd.read_parquet(PARQUET_PATH)

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    dataframe = dataframe[EXPECTED_COLUMNS].copy()

    if dataframe.empty:
        raise ValueError("The Stop Connectivity dataset is empty.")

    if dataframe["stop_id"].isna().any():
        raise ValueError("The dataset contains null stop IDs.")

    if dataframe["stop_id"].duplicated().any():
        raise ValueError("The dataset contains duplicate stop IDs.")

    if dataframe[COUNT_COLUMNS].isna().any().any():
        raise ValueError("The dataset contains null count values.")

    for column in COUNT_COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="raise",
        )

        if (dataframe[column] < 0).any():
            raise ValueError(
                f"Negative values found in {column}."
            )

        if (dataframe[column] % 1 != 0).any():
            raise ValueError(
                f"Non-integer values found in {column}."
            )

        dataframe[column] = dataframe[column].astype("int64")

    return dataframe


def optional_text(value):
    """Convert a value to text while preserving missing values."""

    if pd.isna(value):
        return None

    return str(value)


def load_into_postgres(dataframe: pd.DataFrame) -> int:
    """Insert or update Stop Connectivity records."""

    records = [
        (
            str(row.stop_id),
            optional_text(row.stop_name),
            int(row.distinct_route_count),
            int(row.scheduled_trip_count),
            int(row.scheduled_stop_events),
        )
        for row in dataframe.itertuples(index=False)
    ]

    connection_settings = {
        "host": "127.0.0.1",
        "port": 5432,
        "dbname": "transport_analytics",
        "user": "transport_user",
        "password": load_database_password(),
        "connect_timeout": 10,
    }

    with psycopg.connect(**connection_settings) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO stop_connectivity (
                    stop_id,
                    stop_name,
                    distinct_route_count,
                    scheduled_trip_count,
                    scheduled_stop_events
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (stop_id)
                DO UPDATE SET
                    stop_name = EXCLUDED.stop_name,
                    distinct_route_count = EXCLUDED.distinct_route_count,
                    scheduled_trip_count = EXCLUDED.scheduled_trip_count,
                    scheduled_stop_events = EXCLUDED.scheduled_stop_events
                """,
                records,
            )

            cursor.execute(
                "SELECT COUNT(*) FROM stop_connectivity"
            )

            total_rows = cursor.fetchone()[0]

    return total_rows


def main() -> None:
    """Run the Stop Connectivity loading process."""

    print("Starting Stop Connectivity to PostgreSQL load...")

    dataframe = load_gold_data()

    print(f"Gold records found: {len(dataframe):,}")

    total_rows = load_into_postgres(dataframe)

    print(f"PostgreSQL stop_connectivity records: {total_rows:,}")

    print("Stop Connectivity load completed successfully.")


if __name__ == "__main__":
    main()
