from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTES_FILE = PROJECT_ROOT / "data" / "silver" / "routes.parquet"


def load_routes():
    return pd.read_parquet(ROUTES_FILE)


def test_routes_file_exists():
    assert ROUTES_FILE.is_file(), "Routes Parquet file is missing"


def test_routes_not_empty():
    routes = load_routes()
    assert not routes.empty, "Routes dataset is empty"


def test_route_ids_are_valid():
    routes = load_routes()

    assert routes["route_id"].notna().all()
    assert routes["route_id"].str.strip().ne("").all()
    assert routes["route_id"].is_unique


def test_route_types_are_valid():
    routes = load_routes()

    route_types = routes["route_type"].astype("string")

    assert route_types.notna().all()
    assert route_types.str.fullmatch(r"\d+").fillna(False).all()


def test_required_columns_exist():
    routes = load_routes()

    required = {"route_id", "route_type"}

    assert required.issubset(routes.columns)