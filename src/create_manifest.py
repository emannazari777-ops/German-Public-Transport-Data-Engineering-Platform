
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

GTFS_FILE = PROJECT_ROOT / "data" / "raw" / "gtfs.zip"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
MANIFEST_FILE = METADATA_DIR / "gtfs_manifest.json"


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 checksum without loading the whole file."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def create_manifest() -> Path:
    """Create a manifest describing the local GTFS archive."""

    if not GTFS_FILE.is_file():
        raise FileNotFoundError(
            f"GTFS archive not found: {GTFS_FILE}"
        )

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    file_info = GTFS_FILE.stat()

    manifest = {
        "dataset_name": "VBB Berlin-Brandenburg GTFS",
        "filename": GTFS_FILE.name,
        "file_format": "ZIP",
        "file_size_bytes": file_info.st_size,
        "sha256": calculate_sha256(GTFS_FILE),
        "file_modified_at_utc": datetime.fromtimestamp(
            file_info.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
        "manifest_created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "source_url": None,
        "downloaded_at_utc": None,
        "metadata_notes": (
            "Source URL and original download timestamp "
            "have not been verified."
        ),
    }

    with MANIFEST_FILE.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4, ensure_ascii=False)
        file.write("\n")

    return MANIFEST_FILE


if __name__ == "__main__":
    output_path = create_manifest()

    print("GTFS manifest created successfully.")
    print(f"Manifest: {output_path}")
    print(f"Source archive: {GTFS_FILE.name}")
