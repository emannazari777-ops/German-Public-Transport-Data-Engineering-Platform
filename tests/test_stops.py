from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STOPS_FILE = PROJECT_ROOT / "data" / "silver" / "stops.parquet"


def test_stops_file_exists():
    assert STOPS_FILE.exists(), "Silver stops file is missing"


def test_stops_not_empty():
    stops = pd.read_parquet(STOPS_FILE)
    assert not stops.empty, "Stops dataset is empty"


def test_stop_ids_are_unique():
    stops = pd.read_parquet(STOPS_FILE)
    assert stops["stop_id"].is_unique, "Duplicate stop IDs found"


def test_stop_ids_not_null():
    stops = pd.read_parquet(STOPS_FILE)
    assert stops["stop_id"].notna().all(), "Missing stop IDs found"
    assert stops["stop_id"].str.strip().ne("").all(), "Empty stop IDs found"


def test_coordinates_within_valid_range():
    stops = pd.read_parquet(STOPS_FILE)

    latitude = stops["stop_lat"].dropna()
    longitude = stops["stop_lon"].dropna()

    assert latitude.between(-90, 90).all(), "Invalid latitude found"
    assert longitude.between(-180, 180).all(), "Invalid longitude found"