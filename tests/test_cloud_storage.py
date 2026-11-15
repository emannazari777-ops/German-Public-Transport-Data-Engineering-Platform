
import pytest

from src.cloud.storage import LocalStorage


def test_local_storage_upload_and_download(tmp_path):
    """Check that files can be stored and retrieved."""

    source = tmp_path / "sample.txt"
    source.write_text("German Public Transport", encoding="utf-8")

    storage = LocalStorage(base_dir=str(tmp_path / "storage"))

    stored_path = storage.upload_file(
        source_path=str(source),
        object_key="bronze/sample.txt",
    )

    assert stored_path.is_file()

    destination = tmp_path / "downloaded.txt"

    storage.download_file(
        object_key="bronze/sample.txt",
        destination_path=str(destination),
    )

    assert destination.read_text(encoding="utf-8") == (
        "German Public Transport"
    )


def test_local_storage_rejects_unsafe_paths(tmp_path):
    """Reject directory traversal in upload and download operations."""

    storage = LocalStorage(base_dir=str(tmp_path / "storage"))

    source = tmp_path / "sample.txt"
    source.write_text("Test data", encoding="utf-8")

    with pytest.raises(ValueError):
        storage.upload_file(
            source_path=str(source),
            object_key="../outside.txt",
        )

    with pytest.raises(ValueError):
        storage.download_file(
            object_key="../outside.txt",
            destination_path=str(tmp_path / "downloaded.txt"),
        )


@pytest.mark.parametrize(
    "object_key",
    [
        "../secret.txt",
        "bronze/../../secret.txt",
        "/absolute/path.txt",
        "C:/Windows/secret.txt",
        "bronze\\secret.txt",
        "bronze//sample.txt",
        "./sample.txt",
        "",
    ],
)
def test_local_storage_rejects_invalid_keys(tmp_path, object_key):
    """Reject unsafe or malformed object keys."""

    storage = LocalStorage(base_dir=str(tmp_path / "storage"))

    source = tmp_path / "sample.txt"
    source.write_text("Test data", encoding="utf-8")

    with pytest.raises(ValueError):
        storage.upload_file(
            source_path=str(source),
            object_key=object_key,
        )


def test_local_storage_missing_file(tmp_path):
    """Report a missing stored object."""

    storage = LocalStorage(base_dir=str(tmp_path / "storage"))

    with pytest.raises(FileNotFoundError):
        storage.download_file(
            object_key="bronze/missing.txt",
            destination_path=str(tmp_path / "downloaded.txt"),
        )
