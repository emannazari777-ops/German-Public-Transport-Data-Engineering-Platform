
"""Load the Gold service_by_weekday dataset into PostgreSQL."""

from pathlib import Path

import pandas as pd
import psycopg

from load_gold_to_postgres import load_database_password


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = (
    PROJECT_ROOT / "data" / "gold" / "service_by_weekday.parquet"
)

EXPECTED_COLUMNS = [
    "weekday_number",
    "weekday_name",
    "dates_with_service",
    "total_scheduled_trips",
    "average_trips_per_active_date",
]


def load_gold_data() -> pd.DataFrame:
    """Read and validate the weekly service dataset."""

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
        raise ValueError("The weekly service dataset is empty.")

    if dataframe["weekday_number"].isna().any():
        raise ValueError("Weekday numbers contain null values.")

    if dataframe["weekday_number"].duplicated().any():
        raise ValueError("Duplicate weekday numbers found.")

    if dataframe["weekday_name"].isna().any():
        raise ValueError("Weekday names contain null values.")

    numeric_columns = [
        "dates_with_service",
        "total_scheduled_trips",
        "average_trips_per_active_date",
    ]

    if dataframe[numeric_columns].isna().any().any():
        raise ValueError("Numeric columns contain null values.")

    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="raise",
        )

        if (dataframe[column] < 0).any():
            raise ValueError(
                f"Negative values found in {column}."
            )

    integer_columns = [
        "weekday_number",
        "dates_with_service",
    ]

    for column in integer_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="raise",
        )

        if (dataframe[column] % 1 != 0).any():
            raise ValueError(
                f"Non-integer values found in {column}."
            )

        dataframe[column] = dataframe[column].astype("int64")

    return dataframe


def load_into_postgres(dataframe: pd.DataFrame) -> int:
    """Insert or update weekly service records."""

    records = [
        (
            int(row.weekday_number),
            str(row.weekday_name),
            int(row.dates_with_service),
            float(row.total_scheduled_trips),
            float(row.average_trips_per_active_date),
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
                INSERT INTO service_by_weekday (
                    weekday_number,
                    weekday_name,
                    dates_with_service,
                    total_scheduled_trips,
                    average_trips_per_active_date
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (weekday_number)
                DO UPDATE SET
                    weekday_name = EXCLUDED.weekday_name,
                    dates_with_service = EXCLUDED.dates_with_service,
                    total_scheduled_trips = EXCLUDED.total_scheduled_trips,
                    average_trips_per_active_date =
                        EXCLUDED.average_trips_per_active_date
                """,
                records,
            )

            cursor.execute(
                "SELECT COUNT(*) FROM service_by_weekday"
            )

            total_rows = cursor.fetchone()[0]

    return total_rows


def main() -> None:
    """Run the weekly service loading process."""

    print("Starting Weekly Service to PostgreSQL load...")

    dataframe = load_gold_data()

    print(f"Gold records found: {len(dataframe):,}")

    total_rows = load_into_postgres(dataframe)

    print(f"PostgreSQL service_by_weekday records: {total_rows:,}")

    print("Weekly Service load completed successfully.")


if __name__ == "__main__":
    main()
