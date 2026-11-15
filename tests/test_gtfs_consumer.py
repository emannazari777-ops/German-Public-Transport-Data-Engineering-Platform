
from src.cloud.gtfs_consumer import process_next_gtfs_event
from src.cloud.message_queue import LocalMessageQueue
from src.cloud.storage import LocalStorage


def test_consumer_success(tmp_path):
    """A valid GTFS event should be acknowledged."""

    storage = LocalStorage(str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    source = tmp_path / "gtfs.zip"
    source.write_bytes(b"Sample GTFS data")

    object_key = "german-transport/bronze/gtfs.zip"
    storage.upload_file(str(source), object_key)

    queue.send_message({
        "event_type": "gtfs_staged",
        "object_key": object_key,
        "file_size": source.stat().st_size,
    })

    result = process_next_gtfs_event(storage, queue)

    assert result is True
    assert queue.message_count() == 0
    assert queue.in_flight_count() == 0


def test_consumer_retries_missing_file(tmp_path):
    """A missing GTFS file should cause a retry."""

    storage = LocalStorage(str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    queue.send_message({
        "event_type": "gtfs_staged",
        "object_key": "bronze/missing.zip",
        "file_size": 100,
    })

    result = process_next_gtfs_event(storage, queue)

    assert result is False
    assert queue.message_count() == 1
    assert queue.in_flight_count() == 0


def test_consumer_retries_wrong_file_size(tmp_path):
    """A file size mismatch should cause a retry."""

    storage = LocalStorage(str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    source = tmp_path / "gtfs.zip"
    source.write_bytes(b"Sample data")

    storage.upload_file(str(source), "bronze/gtfs.zip")

    queue.send_message({
        "event_type": "gtfs_staged",
        "object_key": "bronze/gtfs.zip",
        "file_size": 999,
    })

    result = process_next_gtfs_event(storage, queue)

    assert result is False
    assert queue.message_count() == 1
    assert queue.in_flight_count() == 0


def test_consumer_empty_queue(tmp_path):
    """An empty queue should not cause an error."""

    storage = LocalStorage(str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    result = process_next_gtfs_event(storage, queue)

    assert result is False
    assert queue.message_count() == 0


def test_consumer_retries_unsupported_event(tmp_path):
    """An unsupported event should not be acknowledged."""

    storage = LocalStorage(str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    queue.send_message({
        "event_type": "unknown_event",
        "object_key": "bronze/gtfs.zip",
        "file_size": 100,
    })

    result = process_next_gtfs_event(storage, queue)

    assert result is False
    assert queue.message_count() == 1
    assert queue.in_flight_count() == 0
