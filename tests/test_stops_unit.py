
from pathlib import Path

import pandas as pd
import pytest

import src.clean_stops as stops_module


def test_clean_stops_with_sample_data(tmp_path, monkeypatch):
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"
    bronze.mkdir()

    sample = pd.DataFrame(
        {
            "stop_id": ["001", "002", "003"],
            "stop_name": ["Berlin A", "Berlin B", "Berlin C"],
            "stop_lat": [52.52, 52.50, 52.48],
            "stop_lon": [13.40, 13.35, 13.45],
        }
    )
    sample.to_csv(bronze / "stops.txt", index=False)

    monkeypatch.setattr(stops_module, "BRONZE_DIR", bronze)
    monkeypatch.setattr(stops_module, "SILVER_DIR", silver)

    stops_module.clean_stops()

    result = pd.read_parquet(silver / "stops.parquet")

    assert len(result) == 3
    assert result["stop_id"].tolist() == ["001", "002", "003"]
    assert result["stop_lat"].between(-90, 90).all()
    assert result["stop_lon"].between(-180, 180).all()


def test_clean_stops_rejects_duplicate_ids(tmp_path, monkeypatch):
    bronze = tmp_path / "bronze"
    bronze.mkdir()

    sample = pd.DataFrame(
        {
            "stop_id": ["001", "001"],
            "stop_name": ["Berlin A", "Berlin B"],
            "stop_lat": [52.52, 52.50],
            "stop_lon": [13.40, 13.35],
        }
    )
    sample.to_csv(bronze / "stops.txt", index=False)

    monkeypatch.setattr(stops_module, "BRONZE_DIR", bronze)
    monkeypatch.setattr(stops_module, "SILVER_DIR", tmp_path / "silver")

    with pytest.raises(ValueError, match="duplicate stop IDs"):
        stops_module.clean_stops()


def test_clean_stops_rejects_invalid_coordinates(tmp_path, monkeypatch):
    bronze = tmp_path / "bronze"
    bronze.mkdir()

    sample = pd.DataFrame(
        {
            "stop_id": ["001"],
            "stop_name": ["Berlin A"],
            "stop_lat": [95.0],
            "stop_lon": [13.40],
        }
    )
    sample.to_csv(bronze / "stops.txt", index=False)

    monkeypatch.setattr(stops_module, "BRONZE_DIR", bronze)
    monkeypatch.setattr(stops_module, "SILVER_DIR", tmp_path / "silver")

    with pytest.raises(ValueError, match="invalid coordinates"):
        stops_module.clean_stops()
