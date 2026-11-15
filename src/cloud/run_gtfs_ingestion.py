
from pathlib import Path
import hashlib
import shutil
import tempfile

from src.cloud.message_queue import LocalMessageQueue
from src.cloud.storage import LocalStorage


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_ARCHIVE = PROJECT_ROOT / "data" / "raw" / "gtfs.zip"
STORAGE_DIR = PROJECT_ROOT / "data" / "cloud_storage"

OBJECT_KEY = "german-transport/bronze/gtfs.zip"


def calculate_sha256(file_path: Path) -> str:
    """Calculate a file checksum without loading it into memory."""

    digest = hashlib.sha256()

    with file_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def run_gtfs_ingestion():
    """Stage, publish, consume and retrieve the GTFS archive."""

    if not RAW_ARCHIVE.is_file():
        raise FileNotFoundError(
            f"GTFS archive not found: {RAW_ARCHIVE}"
        )

    storage = LocalStorage(str(STORAGE_DIR))
    queue = LocalMessageQueue(max_attempts=3)

    # Stage the original archive in local object storage.
    stored_file = storage.upload_file(
        str(RAW_ARCHIVE),
        OBJECT_KEY,
    )

    expected_size = stored_file.stat().st_size
    expected_checksum = calculate_sha256(stored_file)

    print(f"GTFS staged: {OBJECT_KEY}")

    # Publish an event describing the staged archive.
    queue.send_message(
        {
            "event_type": "gtfs_staged",
            "object_key": OBJECT_KEY,
            "file_size": expected_size,
            "sha256": expected_checksum,
        }
    )

    print("GTFS event published.")

    # The queue is in-memory, so consume within this process.
    message = queue.receive_message()

    if message is None:
        raise RuntimeError("No GTFS event available.")

    message_id = message["message_id"]

    try:
        event = message["body"]

        if event.get("event_type") != "gtfs_staged":
            raise ValueError("Unsupported GTFS event type.")

        object_key = event["object_key"]

        # Download to a temporary location before replacing
        # the pipeline's input archive.
        with tempfile.TemporaryDirectory() as temporary_dir:
            downloaded_file = Path(temporary_dir) / "gtfs.zip"

            storage.download_file(
                object_key,
                str(downloaded_file),
            )

            actual_size = downloaded_file.stat().st_size
            actual_checksum = calculate_sha256(downloaded_file)

            if actual_size != event["file_size"]:
                raise ValueError("GTFS archive size mismatch.")

            if actual_checksum != event["sha256"]:
                raise ValueError("GTFS archive checksum mismatch.")

            # Replace the raw input only after verification.
            replacement = RAW_ARCHIVE.with_name("gtfs.pending.zip")

            try:
                shutil.copy2(downloaded_file, replacement)
                replacement.replace(RAW_ARCHIVE)
            finally:
                replacement.unlink(missing_ok=True)

        queue.acknowledge_message(message_id)

        print("GTFS event acknowledged.")
        print("GTFS archive downloaded and verified.")
        print(f"Pipeline input ready: {RAW_ARCHIVE}")

    except Exception:
        queue.retry_message(message_id)
        raise


if __name__ == "__main__":
    run_gtfs_ingestion()
