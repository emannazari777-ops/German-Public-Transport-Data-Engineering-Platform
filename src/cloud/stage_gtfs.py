
from pathlib import Path

from src.cloud.storage import LocalStorage


def stage_gtfs_file() -> Path:
    """Copy the downloaded GTFS feed into local object storage."""

    source_path = Path("data/raw/gtfs.zip")

    if not source_path.is_file():
        raise FileNotFoundError(
            f"GTFS source file not found: {source_path}"
        )

    storage = LocalStorage(base_dir="data/cloud_storage")

    destination = storage.upload_file(
        source_path=str(source_path),
        object_key="german-transport/bronze/gtfs.zip",
    )

    print("GTFS file staged successfully.")
    print(f"Source: {source_path}")
    print(f"Destination: {destination}")
    print(f"File size: {destination.stat().st_size:,} bytes")

    return destination


if __name__ == "__main__":
    stage_gtfs_file()
