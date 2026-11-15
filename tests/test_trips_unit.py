
import pandas as pd
import pytest

import src.clean_trips as trips_module


def prepare_trips(tmp_path, monkeypatch, data):
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"

    bronze.mkdir()
    silver.mkdir()

    pd.DataFrame(data).to_csv(
        bronze / "trips.txt",
        index=False,
    )

    pd.DataFrame({
        "route_id": ["001", "002"]
    }).to_parquet(
        silver / "routes.parquet",
        index=False,
    )

    monkeypatch.setattr(trips_module, "BRONZE_DIR", bronze)
    monkeypatch.setattr(trips_module, "SILVER_DIR", silver)

    return silver


def test_clean_trips_with_valid_data(tmp_path, monkeypatch):
    silver = prepare_trips(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001", "T002"],
            "route_id": ["001", "002"],
            "service_id": ["S1", "S2"],
        },
    )

    trips_module.clean_trips()

    result = pd.read_parquet(silver / "trips.parquet")

    assert len(result) == 2
    assert result["trip_id"].tolist() == ["T001", "T002"]
    assert result["route_id"].tolist() == ["001", "002"]


def test_clean_trips_rejects_duplicate_ids(tmp_path, monkeypatch):
    prepare_trips(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001", "T001"],
            "route_id": ["001", "002"],
            "service_id": ["S1", "S2"],
        },
    )

    with pytest.raises(ValueError, match="duplicate trip IDs"):
        trips_module.clean_trips()


def test_clean_trips_rejects_unknown_routes(tmp_path, monkeypatch):
    prepare_trips(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001"],
            "route_id": ["999"],
            "service_id": ["S1"],
        },
    )

    with pytest.raises(ValueError, match="unknown route IDs"):
        trips_module.clean_trips()


def test_clean_trips_rejects_missing_service(tmp_path, monkeypatch):
    prepare_trips(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001"],
            "route_id": ["001"],
            "service_id": [""],
        },
    )

    with pytest.raises(ValueError, match="missing values in service_id"):
        trips_module.clean_trips()
