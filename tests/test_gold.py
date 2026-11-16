
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


def test_stop_connectivity_not_empty():
    df = load_gold("stop_connectivity.parquet")
    assert not df.empty


def test_stop_connectivity_unique_ids():
    df = load_gold("stop_connectivity.parquet")
    assert df["stop_id"].is_unique


def test_stop_connectivity_valid_counts():
    df = load_gold("stop_connectivity.parquet")

    assert (df["distinct_route_count"] > 0).all()
    assert (df["scheduled_trip_count"] > 0).all()
    assert (df["scheduled_stop_events"] > 0).all()

    assert (
        df["distinct_route_count"]
        <= df["scheduled_trip_count"]
    ).all()

    assert (
        df["scheduled_trip_count"]
        <= df["scheduled_stop_events"]
    ).all()


def test_service_by_weekday_has_seven_days():
    df = load_gold("service_by_weekday.parquet")

    assert len(df) == 7
    assert set(df["weekday_number"]) == set(range(7))


def test_service_by_weekday_unique_days():
    df = load_gold("service_by_weekday.parquet")
    assert df["weekday_number"].is_unique


def test_service_by_weekday_positive_counts():
    df = load_gold("service_by_weekday.parquet")

    assert (df["dates_with_service"] > 0).all()
    assert (df["total_scheduled_trips"] > 0).all()
    assert (df["average_trips_per_active_date"] > 0).all()
