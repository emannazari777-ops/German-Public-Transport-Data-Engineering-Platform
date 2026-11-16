
import hashlib
import json
from pathlib import Path

import pytest

from src import create_manifest


def test_calculate_sha256(tmp_path):
    """Verify the checksum against Python's hashlib."""

    sample_file = tmp_path / "sample.zip"
    content = b"sample GTFS data"
    sample_file.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    actual = create_manifest.calculate_sha256(sample_file)

    assert actual == expected
    assert len(actual) == 64


def test_manifest_missing_file(tmp_path, monkeypatch):
    """A missing GTFS archive must raise an error."""

    missing_file = tmp_path / "missing.zip"

    monkeypatch.setattr(
        create_manifest,
        "GTFS_FILE",
        missing_file,
    )

    with pytest.raises(FileNotFoundError):
        create_manifest.create_manifest()


def test_create_manifest(tmp_path, monkeypatch):
    """Verify metadata is written for a sample archive."""

    raw_dir = tmp_path / "data" / "raw"
    metadata_dir = tmp_path / "data" / "metadata"

    raw_dir.mkdir(parents=True)

    gtfs_file = raw_dir / "gtfs.zip"
    content = b"test archive content"
    gtfs_file.write_bytes(content)

    manifest_file = metadata_dir / "gtfs_manifest.json"

    monkeypatch.setattr(
        create_manifest,
        "GTFS_FILE",
        gtfs_file,
    )
    monkeypatch.setattr(
        create_manifest,
        "METADATA_DIR",
        metadata_dir,
    )
    monkeypatch.setattr(
        create_manifest,
        "MANIFEST_FILE",
        manifest_file,
    )

    result_path = create_manifest.create_manifest()

    assert result_path == manifest_file
    assert manifest_file.exists()

    manifest = json.loads(
        manifest_file.read_text(encoding="utf-8")
    )

    assert manifest["dataset_name"] == (
        "VBB Berlin-Brandenburg GTFS"
    )
    assert manifest["filename"] == "gtfs.zip"
    assert manifest["file_format"] == "ZIP"
    assert manifest["file_size_bytes"] == len(content)
    assert manifest["sha256"] == hashlib.sha256(
        content
    ).hexdigest()

    assert manifest["file_modified_at_utc"]
    assert manifest["manifest_created_at_utc"]

    assert manifest["source_url"] is None
    assert manifest["downloaded_at_utc"] is None
