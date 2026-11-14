from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def clean_trips():
    source = BRONZE_DIR / "trips.txt"
    routes_file = SILVER_DIR / "routes.parquet"
    destination = SILVER_DIR / "trips.parquet"

    if not source.is_file():
        raise FileNotFoundError(f"Trips file not found: {source}")

    if not routes_file.is_file():
        raise FileNotFoundError(
            f"Cleaned routes file not found: {routes_file}"
        )

    # Keep identifiers as strings to avoid changing their values.
    trips = pd.read_csv(source, dtype="string", low_memory=False)

    required_columns = {"trip_id", "route_id", "service_id"}
    missing = required_columns - set(trips.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    original_count = len(trips)

    # Normalize required identifiers.
    for column in required_columns:
        trips[column] = trips[column].str.strip()

        invalid = trips[column].isna() | trips[column].eq("")

        if invalid.any():
            raise ValueError(
                f"Found {invalid.sum()} missing values in {column}"
            )

    # Each trip must have a unique identifier.
    duplicate_count = trips["trip_id"].duplicated().sum()

    if duplicate_count:
        raise ValueError(
            f"Found {duplicate_count} duplicate trip IDs"
        )

    # Check that every trip references an existing route.
    routes = pd.read_parquet(
        routes_file,
        columns=["route_id"],
    )

    valid_route_ids = set(routes["route_id"])

    unknown_routes = ~trips["route_id"].isin(valid_route_ids)

    if unknown_routes.any():
        raise ValueError(
            f"Found {unknown_routes.sum()} trips with unknown route IDs"
        )

    # Preserve optional GTFS fields for downstream processing.
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    trips.to_parquet(destination, index=False)

    print("Silver layer: trips")
    print(f"Input records: {original_count:,}")
    print(f"Output records: {len(trips):,}")
    print(f"Unique routes referenced: {trips['route_id'].nunique():,}")
    print(f"Saved to: {destination}")


if __name__ == "__main__":
    clean_trips()