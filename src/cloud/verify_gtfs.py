
import hashlib
from pathlib import Path


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA-256 checksum of a file."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def verify_gtfs() -> bool:
    """Verify that the staged GTFS file matches the original."""

    original = Path("data/raw/gtfs.zip")

    staged = Path(
        "data/cloud_storage/german-transport/bronze/gtfs.zip"
    )

    if not original.is_file():
        raise FileNotFoundError(f"Original file missing: {original}")

    if not staged.is_file():
        raise FileNotFoundError(f"Staged file missing: {staged}")

    original_hash = calculate_sha256(original)
    staged_hash = calculate_sha256(staged)

    print(f"Original SHA-256: {original_hash}")
    print(f"Staged SHA-256:   {staged_hash}")

    if original_hash == staged_hash:
        print("SUCCESS: GTFS file integrity verified.")
        return True

    print("ERROR: GTFS file integrity check failed.")
    return False


if __name__ == "__main__":
    if not verify_gtfs():
        raise SystemExit(1)
