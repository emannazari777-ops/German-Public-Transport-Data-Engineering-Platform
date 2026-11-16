
"""Load the Gold top_stops dataset into PostgreSQL."""

import os
from pathlib import Path

import pandas as pd
import psycopg


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_PATH = PROJECT_ROOT / "data" / "gold" / "top_stops.parquet"
ENV_PATH = PROJECT_ROOT / "docker" / "postgres" / ".env"

EXPECTED_COLUMNS = [
    "stop_id",
    "stop_name",
    "scheduled_stop_count",
    "unique_trips",
]


def load_database_password() -> str:
    """Read the password from an environment variable or local .env."""

    password = os.environ.get("POSTGRES_PASSWORD")

    if password:
        return password

    if not ENV_PATH.is_file():
        raise FileNotFoundError(
            "PostgreSQL password not found. Set POSTGRES_PASSWORD "
            "or create the local docker/postgres/.env file."
        )

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if separator and key.strip() == "POSTGRES_PASSWORD":
            password = value.strip().strip('"').strip("'")

            if password:
                return password

    raise ValueError("POSTGRES_PASSWORD is missing or empty.")


def get_connection_settings() -> dict:
    """Build PostgreSQL settings for local or Docker execution."""

    return {
        "host": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "dbname": os.environ.get(
            "POSTGRES_DB", "transport_analytics"
        ),
        "user": os.environ.get(
            "POSTGRES_USER", "transport_user"
        ),
        "password": load_database_password(),
        "connect_timeout": 10,
    }


def load_gold_data() -> pd.DataFrame:
    """Read and validate the Gold-layer Parquet dataset."""

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
        raise ValueError("The Gold dataset is empty.")

    if dataframe["stop_id"].isna().any():
        raise ValueError("The dataset contains null stop IDs.")

    if dataframe["stop_id"].duplicated().any():
        raise ValueError("The dataset contains duplicate stop IDs.")

    count_columns = [
        "scheduled_stop_count",
        "unique_trips",
    ]

    if dataframe[count_columns].isna().any().any():
        raise ValueError("The dataset contains null count values.")

    for column in count_columns:
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


def load_into_postgres(dataframe: pd.DataFrame) -> int:
    """Insert or update Gold records in PostgreSQL."""

    records = [
        (
            str(row.stop_id),
            None if pd.isna(row.stop_name) else str(row.stop_name),
            int(row.scheduled_stop_count),
            int(row.unique_trips),
        )
        for row in dataframe.itertuples(index=False)
    ]

    with psycopg.connect(**get_connection_settings()) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO top_stops (
                    stop_id,
                    stop_name,
                    scheduled_stop_count,
                    unique_trips
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (stop_id)
                DO UPDATE SET
                    stop_name = EXCLUDED.stop_name,
                    scheduled_stop_count = EXCLUDED.scheduled_stop_count,
                    unique_trips = EXCLUDED.unique_trips
                """,
                records,
            )

            cursor.execute("SELECT COUNT(*) FROM top_stops")
            total_rows = cursor.fetchone()[0]

    return total_rows


def main() -> None:
    """Run the Gold-to-PostgreSQL loading process."""

    print("Starting Gold to PostgreSQL load...")

    dataframe = load_gold_data()

    print(f"Gold records found: {len(dataframe):,}")

    total_rows = load_into_postgres(dataframe)

    print(f"PostgreSQL top_stops records: {total_rows:,}")
    print("Gold to PostgreSQL load completed successfully.")


if __name__ == "__main__":
    main()
