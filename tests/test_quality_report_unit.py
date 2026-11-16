
import json

import duckdb
import pandas as pd
import pytest

from src import generate_quality_report as quality


def test_inspect_dataset(tmp_path):
    """Check row counts and missing key values."""

    file_path = tmp_path / "stops.parquet"

    data = pd.DataFrame(
        {
            "stop_id": ["S1", "S2", None],
            "stop_name": ["Central", "West", "Unknown"],
        }
    )
    data.to_parquet(file_path, index=False)

    with duckdb.connect() as connection:
        result = quality.inspect_dataset(
            connection,
            "stops",
            file_path,
        )

    assert result["row_count"] == 3
    assert result["column_count"] == 2
    assert result["null_key_counts"]["stop_id"] == 1


def test_inspect_dataset_missing_column(tmp_path):
    """Missing required columns must be detected."""

    file_path = tmp_path / "stops.parquet"

    pd.DataFrame(
        {"stop_name": ["Central"]}
    ).to_parquet(file_path, index=False)

    with duckdb.connect() as connection:
        with pytest.raises(
            ValueError,
            match="Missing required column",
        ):
            quality.inspect_dataset(
                connection,
                "stops",
                file_path,
            )


def test_quality_report_pass(tmp_path, monkeypatch):
    """A valid sample dataset should produce PASS."""

    sample_file = tmp_path / "sample.parquet"
    report_file = tmp_path / "quality_report.json"

    pd.DataFrame(
        {"stop_id": ["S1", "S2"]}
    ).to_parquet(sample_file, index=False)

    monkeypatch.setattr(
        quality,
        "DATASETS",
        {"stops": sample_file},
    )
    monkeypatch.setattr(
        quality,
        "METADATA_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        quality,
        "REPORT_FILE",
        report_file,
    )
    monkeypatch.setattr(
        quality,
        "check_duplicate_ids",
        lambda connection: {"stops": 0},
    )
    monkeypatch.setattr(
        quality,
        "check_referential_integrity",
        lambda connection: {
            "unknown_trip_ids": 0,
            "unknown_stop_ids": 0,
        },
    )

    result = quality.generate_quality_report()

    assert result == report_file
    assert report_file.exists()

    report = json.loads(
        report_file.read_text(encoding="utf-8")
    )

    assert report["overall_status"] == "PASS"
    assert report["issues"] == []
    assert report["dataset_metrics"]["stops"]["row_count"] == 2


def test_quality_report_fail(tmp_path, monkeypatch):
    """Invalid data should produce FAIL and raise an error."""

    sample_file = tmp_path / "sample.parquet"
    report_file = tmp_path / "quality_report.json"

    pd.DataFrame(
        {"stop_id": ["S1", None]}
    ).to_parquet(sample_file, index=False)

    monkeypatch.setattr(
        quality,
        "DATASETS",
        {"stops": sample_file},
    )
    monkeypatch.setattr(
        quality,
        "METADATA_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        quality,
        "REPORT_FILE",
        report_file,
    )
    monkeypatch.setattr(
        quality,
        "check_duplicate_ids",
        lambda connection: {"stops": 0},
    )
    monkeypatch.setattr(
        quality,
        "check_referential_integrity",
        lambda connection: {
            "unknown_trip_ids": 0,
            "unknown_stop_ids": 0,
        },
    )

    with pytest.raises(
        ValueError,
        match="Data quality checks failed",
    ):
        quality.generate_quality_report()

    report = json.loads(
        report_file.read_text(encoding="utf-8")
    )

    assert report["overall_status"] == "FAIL"
    assert len(report["issues"]) == 1
    assert "null values" in report["issues"][0]
