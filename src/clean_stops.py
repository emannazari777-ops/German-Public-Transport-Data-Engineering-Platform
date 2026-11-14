from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def clean_stops():
    source = BRONZE_DIR / "stops.txt"
    destination = SILVER_DIR / "stops.parquet"

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    # Read identifiers as strings to preserve leading zeros.
    stops = pd.read_csv(
        source,
        dtype={
            "stop_id": "string",
            "stop_code": "string",
            "parent_station": "string",
        },
        low_memory=False,
    )

    required_columns = {
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon",
    }

    missing_columns = required_columns - set(stops.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    original_count = len(stops)

    # Remove records without a valid stop identifier.
    stops["stop_id"] = stops["stop_id"].str.strip()
    stops = stops.dropna(subset=["stop_id"])
    stops = stops[stops["stop_id"] != ""]

    # Stop identifiers must be unique.
    duplicate_count = stops["stop_id"].duplicated().sum()

    if duplicate_count:
        raise ValueError(
            f"Found {duplicate_count} duplicate stop IDs"
        )

    # Convert coordinates to numeric values.
    for column in ["stop_lat", "stop_lon"]:
        stops[column] = pd.to_numeric(
            stops[column],
            errors="coerce",
        )

    # Coordinates are validated only when provided.
    # GTFS parent stations may not always have coordinates.
    has_lat = stops["stop_lat"].notna()
    has_lon = stops["stop_lon"].notna()

    invalid_coordinates = (
        (has_lat & ~stops["stop_lat"].between(-90, 90))
        | (has_lon & ~stops["stop_lon"].between(-180, 180))
    )

    if invalid_coordinates.any():
        raise ValueError(
            f"Found {invalid_coordinates.sum()} invalid coordinates"
        )

    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    stops.to_parquet(destination, index=False)

    print("Silver layer: stops")
    print(f"Input records: {original_count:,}")
    print(f"Output records: {len(stops):,}")
    print(f"Saved to: {destination}")


if __name__ == "__main__":
    clean_stops()