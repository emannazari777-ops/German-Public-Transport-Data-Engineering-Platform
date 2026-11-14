
import pandas as pd
import pytest

import src.clean_routes as routes_module


def prepare_routes(tmp_path, monkeypatch, data):
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"
    bronze.mkdir()

    pd.DataFrame(data).to_csv(
        bronze / "routes.txt",
        index=False,
    )

    monkeypatch.setattr(routes_module, "BRONZE_DIR", bronze)
    monkeypatch.setattr(routes_module, "SILVER_DIR", silver)

    return silver


def test_clean_routes_with_valid_data(tmp_path, monkeypatch):
    silver = prepare_routes(
        tmp_path,
        monkeypatch,
        {
            "route_id": ["001", "002"],
            "route_short_name": ["U6", "M10"],
            "route_type": ["400", "900"],
        },
    )

    routes_module.clean_routes()

    result = pd.read_parquet(silver / "routes.parquet")

    assert len(result) == 2
    assert result["route_id"].tolist() == ["001", "002"]
    assert result["route_type"].tolist() == ["400", "900"]


def test_clean_routes_rejects_duplicate_ids(tmp_path, monkeypatch):
    prepare_routes(
        tmp_path,
        monkeypatch,
        {
            "route_id": ["001", "001"],
            "route_type": ["400", "900"],
        },
    )

    with pytest.raises(ValueError, match="duplicate route IDs"):
        routes_module.clean_routes()


def test_clean_routes_rejects_invalid_type(tmp_path, monkeypatch):
    prepare_routes(
        tmp_path,
        monkeypatch,
        {
            "route_id": ["001"],
            "route_type": ["invalid"],
        },
    )

    with pytest.raises(ValueError, match="invalid route types"):
        routes_module.clean_routes()


def test_clean_routes_rejects_missing_id(tmp_path, monkeypatch):
    prepare_routes(
        tmp_path,
        monkeypatch,
        {
            "route_id": [""],
            "route_type": ["400"],
        },
    )

    with pytest.raises(ValueError, match="missing required values"):
        routes_module.clean_routes()
