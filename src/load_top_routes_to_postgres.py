
"""Load the Gold top_routes dataset into local PostgreSQL."""

from pathlib import Path

import pandas as pd
import psycopg

from load_gold_to_postgres import load_database_password


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = PROJECT_ROOT / "data" / "gold" / "top_routes.parquet"

EXPECTED_COLUMNS = [
    "route_id",
    "route_short_name",
    "route_long_name",
    "route_type",
    "scheduled_trip_count",
]


def load_gold_data() -> pd.DataFrame:
    """Read and validate the Top Routes dataset."""

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
        raise ValueError("The Top Routes dataset is empty.")

    if dataframe["route_id"].isna().any():
        raise ValueError("The dataset contains null route IDs.")

    if dataframe["route_id"].duplicated().any():
        raise ValueError("The dataset contains duplicate route IDs.")

    if dataframe["scheduled_trip_count"].isna().any():
        raise ValueError("Scheduled trip counts contain null values.")

    dataframe["scheduled_trip_count"] = pd.to_numeric(
        dataframe["scheduled_trip_count"],
        errors="raise",
    )

    if (dataframe["scheduled_trip_count"] < 0).any():
        raise ValueError("Scheduled trip counts cannot be negative.")

    if (dataframe["scheduled_trip_count"] % 1 != 0).any():
        raise ValueError("Scheduled trip counts must be integers.")

    dataframe["scheduled_trip_count"] = dataframe[
        "scheduled_trip_count"
    ].astype("int64")

    return dataframe


def optional_text(value):
    """Convert a value to text while preserving missing values."""

    if pd.isna(value):
        return None

    return str(value)


def load_into_postgres(dataframe: pd.DataFrame) -> int:
    """Insert or update Top Routes records."""

    records = [
        (
            str(row.route_id),
            optional_text(row.route_short_name),
            optional_text(row.route_long_name),
            optional_text(row.route_type),
            int(row.scheduled_trip_count),
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
                INSERT INTO top_routes (
                    route_id,
                    route_short_name,
                    route_long_name,
                    route_type,
                    scheduled_trip_count
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (route_id)
                DO UPDATE SET
                    route_short_name = EXCLUDED.route_short_name,
                    route_long_name = EXCLUDED.route_long_name,
                    route_type = EXCLUDED.route_type,
                    scheduled_trip_count = EXCLUDED.scheduled_trip_count
                """,
                records,
            )

            cursor.execute("SELECT COUNT(*) FROM top_routes")
            total_rows = cursor.fetchone()[0]

    return total_rows


def main() -> None:
    """Run the Top Routes loading process."""

    print("Starting Top Routes to PostgreSQL load...")

    dataframe = load_gold_data()
    print(f"Gold records found: {len(dataframe):,}")

    total_rows = load_into_postgres(dataframe)
    print(f"PostgreSQL top_routes records: {total_rows:,}")

    print("Top Routes load completed successfully.")


if __name__ == "__main__":
    main()
