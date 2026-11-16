
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def validate_identifiers(data, filename):
    data["service_id"] = data["service_id"].str.strip()

    invalid = data["service_id"].isna() | data["service_id"].eq("")

    if invalid.any():
        raise ValueError(
            f"{filename}: found {invalid.sum()} invalid service IDs"
        )


def validate_dates(data, columns, filename):
    for column in columns:
        parsed = pd.to_datetime(
            data[column],
            format="%Y%m%d",
            errors="coerce",
        )

        if parsed.isna().any():
            raise ValueError(
                f"{filename}: invalid dates in {column}"
            )


def clean_calendar():
    calendar_source = BRONZE_DIR / "calendar.txt"
    exceptions_source = BRONZE_DIR / "calendar_dates.txt"

    for source in [calendar_source, exceptions_source]:
        if not source.is_file():
            raise FileNotFoundError(f"GTFS calendar file not found: {source}")

    calendar = pd.read_csv(
        calendar_source,
        dtype="string",
        low_memory=False,
    )

    exceptions = pd.read_csv(
        exceptions_source,
        dtype="string",
        low_memory=False,
    )

    calendar_columns = {
        "service_id",
        "start_date",
        "end_date",
        *WEEKDAYS,
    }

    exception_columns = {
        "service_id",
        "date",
        "exception_type",
    }

    missing_calendar = calendar_columns - set(calendar.columns)
    missing_exceptions = exception_columns - set(exceptions.columns)

    if missing_calendar:
        raise ValueError(
            f"calendar.txt missing columns: {sorted(missing_calendar)}"
        )

    if missing_exceptions:
        raise ValueError(
            "calendar_dates.txt missing columns: "
            f"{sorted(missing_exceptions)}"
        )

    validate_identifiers(calendar, "calendar.txt")
    validate_identifiers(exceptions, "calendar_dates.txt")

    if calendar["service_id"].duplicated().any():
        raise ValueError("Duplicate service IDs in calendar.txt")

    validate_dates(
        calendar,
        ["start_date", "end_date"],
        "calendar.txt",
    )

    validate_dates(
        exceptions,
        ["date"],
        "calendar_dates.txt",
    )

    start_dates = pd.to_datetime(
        calendar["start_date"],
        format="%Y%m%d",
    )

    end_dates = pd.to_datetime(
        calendar["end_date"],
        format="%Y%m%d",
    )

    if (start_dates > end_dates).any():
        raise ValueError(
            "calendar.txt contains start dates after end dates"
        )

    for weekday in WEEKDAYS:
        if not calendar[weekday].isin(["0", "1"]).all():
            raise ValueError(
                f"Invalid weekday values in {weekday}"
            )

        calendar[weekday] = calendar[weekday].astype("int8")

    if not exceptions["exception_type"].isin(["1", "2"]).all():
        raise ValueError(
            "Invalid exception types in calendar_dates.txt"
        )

    exceptions["exception_type"] = (
        exceptions["exception_type"].astype("int8")
    )

    duplicate_exceptions = exceptions.duplicated(
        subset=["service_id", "date"]
    )

    if duplicate_exceptions.any():
        raise ValueError(
            "Duplicate service/date combinations in calendar_dates.txt"
        )

    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    calendar_destination = SILVER_DIR / "calendar.parquet"
    exceptions_destination = SILVER_DIR / "calendar_dates.parquet"

    calendar.to_parquet(
        calendar_destination,
        index=False,
        compression="zstd",
    )

    exceptions.to_parquet(
        exceptions_destination,
        index=False,
        compression="zstd",
    )

    print("Silver layer: GTFS calendar")
    print(f"Calendar records: {len(calendar):,}")
    print(f"Exception records: {len(exceptions):,}")
    print(f"Unique calendar services: {calendar['service_id'].nunique():,}")
    print(
        "Unique exception services: "
        f"{exceptions['service_id'].nunique():,}"
    )
    print(f"Saved to: {calendar_destination}")
    print(f"Saved to: {exceptions_destination}")


if __name__ == "__main__":
    clean_calendar()
