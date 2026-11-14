from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "data" / "gold"


def load_gold(filename):
    path = GOLD_DIR / filename
    assert path.is_file(), f"Missing Gold file: {path}"

    with duckdb.connect() as connection:
        return connection.execute(
            "SELECT * FROM read_parquet(?)", [str(path)]
        ).df()


def test_top_stops_not_empty():
    df = load_gold("top_stops.parquet")
    assert not df.empty


def test_top_stops_unique_ids():
    df = load_gold("top_stops.parquet")
    assert df["stop_id"].is_unique


def test_top_stops_positive_counts():
    df = load_gold("top_stops.parquet")
    assert (df["scheduled_stop_count"] > 0).all()


def test_top_routes_not_empty():
    df = load_gold("top_routes.parquet")
    assert not df.empty


def test_top_routes_unique_ids():
    df = load_gold("top_routes.parquet")
    assert df["route_id"].is_unique


def test_top_routes_positive_counts():
    df = load_gold("top_routes.parquet")
    assert (df["scheduled_trip_count"] > 0).all()