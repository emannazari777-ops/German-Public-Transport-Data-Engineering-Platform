
import duckdb
import pandas as pd
import pytest

import src.clean_stop_times as stop_times_module


def prepare_stop_times(tmp_path, monkeypatch, data):
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"

    bronze.mkdir()
    silver.mkdir()

    pd.DataFrame(data).to_csv(
        bronze / "stop_times.txt",
        index=False,
    )

    monkeypatch.setattr(
        stop_times_module, "BRONZE_DIR", bronze
    )
    monkeypatch.setattr(
        stop_times_module, "SILVER_DIR", silver
    )

    return silver


def test_clean_stop_times_with_valid_data(tmp_path, monkeypatch):
    silver = prepare_stop_times(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001", "T001"],
            "stop_id": ["S001", "S002"],
            "stop_sequence": [1, 2],
            "arrival_time": ["23:30:00", "25:15:00"],
            "departure_time": ["23:31:00", "25:16:00"],
            "pickup_type": [0, 0],
            "drop_off_type": [0, 0],
            "stop_headsign": ["Central", "Airport"],
        },
    )

    stop_times_module.clean_stop_times()

    result = duckdb.sql(
        f"SELECT * FROM read_parquet('{silver / 'stop_times.parquet'}')"
    ).df()

    assert len(result) == 2
    assert result["trip_id"].tolist() == ["T001", "T001"]
    assert result["arrival_time"].tolist() == [
        "23:30:00",
        "25:15:00",
    ]


def test_clean_stop_times_rejects_invalid_time(
    tmp_path, monkeypatch
):
    prepare_stop_times(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001"],
            "stop_id": ["S001"],
            "stop_sequence": [1],
            "arrival_time": ["12:99:00"],
            "departure_time": ["13:00:00"],
            "pickup_type": [0],
            "drop_off_type": [0],
            "stop_headsign": ["Central"],
        },
    )

    with pytest.raises(ValueError, match="invalid time values"):
        stop_times_module.clean_stop_times()


def test_clean_stop_times_rejects_duplicate_sequence(
    tmp_path, monkeypatch
):
    prepare_stop_times(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001", "T001"],
            "stop_id": ["S001", "S002"],
            "stop_sequence": [1, 1],
            "arrival_time": ["10:00:00", "10:10:00"],
            "departure_time": ["10:01:00", "10:11:00"],
            "pickup_type": [0, 0],
            "drop_off_type": [0, 0],
            "stop_headsign": ["Central", "Airport"],
        },
    )

    with pytest.raises(ValueError, match="duplicate trip sequences"):
        stop_times_module.clean_stop_times()


def test_clean_stop_times_rejects_missing_stop_id(
    tmp_path, monkeypatch
):
    prepare_stop_times(
        tmp_path,
        monkeypatch,
        {
            "trip_id": ["T001"],
            "stop_id": [""],
            "stop_sequence": [1],
            "arrival_time": ["10:00:00"],
            "departure_time": ["10:01:00"],
            "pickup_type": [0],
            "drop_off_type": [0],
            "stop_headsign": ["Central"],
        },
    )

    with pytest.raises(
        ValueError, match="invalid stop-time identifiers"
    ):
        stop_times_module.clean_stop_times()
