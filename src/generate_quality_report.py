
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

REPORT_FILE = METADATA_DIR / "quality_report.json"

DATASETS = {
    "stops": SILVER_DIR / "stops.parquet",
    "routes": SILVER_DIR / "routes.parquet",
    "trips": SILVER_DIR / "trips.parquet",
    "stop_times": SILVER_DIR / "stop_times.parquet",
    "calendar": SILVER_DIR / "calendar.parquet",
    "calendar_dates": SILVER_DIR / "calendar_dates.parquet",
    "top_stops": GOLD_DIR / "top_stops.parquet",
    "top_routes": GOLD_DIR / "top_routes.parquet",
    "stop_connectivity": GOLD_DIR / "stop_connectivity.parquet",
    "service_by_weekday": GOLD_DIR / "service_by_weekday.parquet",
}

KEY_COLUMNS = {
    "stops": ["stop_id"],
    "routes": ["route_id"],
    "trips": ["trip_id", "route_id", "service_id"],
    "stop_times": ["trip_id", "stop_id"],
    "calendar": ["service_id"],
    "calendar_dates": ["service_id", "date"],
}


def inspect_dataset(connection, dataset_name, file_path):
    """Calculate basic quality metrics for one Parquet dataset."""

    parquet_path = file_path.as_posix().replace("'", "''")
    source = f"read_parquet('{parquet_path}')"

    row_count = connection.execute(
        f"SELECT COUNT(*) FROM {source}"
    ).fetchone()[0]

    columns = [
        column[0]
        for column in connection.execute(
            f"DESCRIBE SELECT * FROM {source}"
        ).fetchall()
    ]

    null_counts = {}

    for column in KEY_COLUMNS.get(dataset_name, []):
        if column not in columns:
            raise ValueError(
                f"Missing required column '{column}' "
                f"in dataset '{dataset_name}'"
            )

        null_counts[column] = connection.execute(
            f'SELECT COUNT(*) FROM {source} '
            f'WHERE "{column}" IS NULL'
        ).fetchone()[0]

    return {
        "row_count": row_count,
        "column_count": len(columns),
        "null_key_counts": null_counts,
    }


def check_duplicate_ids(connection):
    """Check duplicate identifiers in core Silver datasets."""

    checks = {
        "stops": ("stops.parquet", "stop_id"),
        "routes": ("routes.parquet", "route_id"),
        "trips": ("trips.parquet", "trip_id"),
    }

    results = {}

    for name, (filename, column) in checks.items():
        path = (SILVER_DIR / filename).as_posix()
        path = path.replace("'", "''")

        duplicate_count = connection.execute(
            f"""
            SELECT COUNT(*) - COUNT(DISTINCT "{column}")
            FROM read_parquet('{path}')
            WHERE "{column}" IS NOT NULL
            """
        ).fetchone()[0]

        results[name] = duplicate_count

    return results


def check_referential_integrity(connection):
    """Count stop_times references missing from parent tables."""

    stop_times_path = (
        SILVER_DIR / "stop_times.parquet"
    ).as_posix().replace("'", "''")

    trips_path = (
        SILVER_DIR / "trips.parquet"
    ).as_posix().replace("'", "''")

    stops_path = (
        SILVER_DIR / "stops.parquet"
    ).as_posix().replace("'", "''")

    unknown_trips = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{stop_times_path}') AS st
        WHERE NOT EXISTS (
            SELECT 1
            FROM read_parquet('{trips_path}') AS t
            WHERE st.trip_id = t.trip_id
        )
        """
    ).fetchone()[0]

    unknown_stops = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{stop_times_path}') AS st
        WHERE NOT EXISTS (
            SELECT 1
            FROM read_parquet('{stops_path}') AS s
            WHERE st.stop_id = s.stop_id
        )
        """
    ).fetchone()[0]

    return {
        "unknown_trip_ids": unknown_trips,
        "unknown_stop_ids": unknown_stops,
    }


def generate_quality_report():
    """Generate a persistent quality report for Silver and Gold."""

    missing_files = [
        str(path)
        for path in DATASETS.values()
        if not path.is_file()
    ]

    if missing_files:
        raise FileNotFoundError(
            "Required datasets are missing:\n"
            + "\n".join(missing_files)
        )

    with duckdb.connect() as connection:
        dataset_metrics = {
            name: inspect_dataset(connection, name, path)
            for name, path in DATASETS.items()
        }

        duplicates = check_duplicate_ids(connection)
        relationships = check_referential_integrity(
            connection
        )

    issues = []

    for name, metrics in dataset_metrics.items():
        if metrics["row_count"] == 0:
            issues.append(f"{name}: dataset is empty")

        for column, count in metrics["null_key_counts"].items():
            if count > 0:
                issues.append(
                    f"{name}: {count} null values in {column}"
                )

    for name, count in duplicates.items():
        if count > 0:
            issues.append(
                f"{name}: {count} duplicate identifiers"
            )

    for name, count in relationships.items():
        if count > 0:
            issues.append(f"{name}: {count} invalid references")

    report = {
        "report_name": "GTFS Data Quality Report",
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset_metrics": dataset_metrics,
        "duplicate_id_counts": duplicates,
        "referential_integrity": relationships,
        "overall_status": "PASS" if not issues else "FAIL",
        "issues": issues,
    }

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)
        file.write("\n")

    print("GTFS Data Quality Report")
    print("-" * 40)
    print(f"Datasets checked: {len(dataset_metrics)}")
    print(f"Overall status: {report['overall_status']}")
    print(f"Issues found: {len(issues)}")
    print(f"Report saved: {REPORT_FILE}")

    if issues:
        for issue in issues:
            print(f"- {issue}")

        raise ValueError("Data quality checks failed.")

    return REPORT_FILE


if __name__ == "__main__":
    generate_quality_report()
