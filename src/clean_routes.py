from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def clean_routes():
    source = BRONZE_DIR / "routes.txt"
    destination = SILVER_DIR / "routes.parquet"

    if not source.exists():
        raise FileNotFoundError(f"Routes file not found: {source}")

    routes = pd.read_csv(
        source,
        dtype={
            "route_id": "string",
            "agency_id": "string",
            "route_short_name": "string",
            "route_long_name": "string",
            "route_type": "string",
        },
        low_memory=False,
    )

    required_columns = {
        "route_id",
        "route_type",
    }

    missing_columns = required_columns - set(routes.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    original_count = len(routes)

    # Normalize route identifiers.
    routes["route_id"] = routes["route_id"].str.strip()
    routes["route_type"] = routes["route_type"].str.strip()

    # Reject missing identifiers and route types.
    invalid_required = (
        routes["route_id"].isna()
        | routes["route_id"].eq("")
        | routes["route_type"].isna()
        | routes["route_type"].eq("")
    )

    if invalid_required.any():
        raise ValueError(
            f"Found {invalid_required.sum()} routes with missing required values"
        )

    # Every route must have a unique identifier.
    duplicate_count = routes["route_id"].duplicated().sum()

    if duplicate_count:
        raise ValueError(
            f"Found {duplicate_count} duplicate route IDs"
        )

    # GTFS route types must be non-negative integer codes.
    invalid_types = ~routes["route_type"].str.fullmatch(r"\d+").fillna(False)

    if invalid_types.any():
        raise ValueError(
            f"Found {invalid_types.sum()} invalid route types"
        )

    # Keep optional fields unchanged to preserve source information.
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    routes.to_parquet(destination, index=False)

    print("Silver layer: routes")
    print(f"Input records: {original_count:,}")
    print(f"Output records: {len(routes):,}")
    print(f"Saved to: {destination}")


if __name__ == "__main__":
    clean_routes()