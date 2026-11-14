from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SILVER_DIR = PROJECT_ROOT / "data" / "silver"


def load_trips():
    return pd.read_parquet(SILVER_DIR / "trips.parquet")


def test_trips_not_empty():
    trips = load_trips()
    assert not trips.empty


def test_trip_ids_are_unique():
    trips = load_trips()
    assert trips["trip_id"].is_unique


def test_required_identifiers_are_present():
    trips = load_trips()

    for column in ["trip_id", "route_id", "service_id"]:
        assert trips[column].notna().all()
        assert trips[column].str.strip().ne("").all()


def test_all_trips_reference_existing_routes():
    trips = load_trips()
    routes = pd.read_parquet(
        SILVER_DIR / "routes.parquet",
        columns=["route_id"],
    )

    assert trips["route_id"].isin(routes["route_id"]).all()


def test_direction_values():
    trips = load_trips()

    if "direction_id" in trips.columns:
        values = trips["direction_id"].dropna()
        assert values.isin(["0", "1"]).all()