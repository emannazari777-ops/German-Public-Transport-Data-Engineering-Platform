
import pytest

from src.cloud.gtfs_event import publish_gtfs_event
from src.cloud.message_queue import LocalMessageQueue
from src.cloud.storage import LocalStorage


def test_publish_gtfs_event_success(tmp_path):
    """Publish an event for an existing GTFS file."""

    storage = LocalStorage(base_dir=str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    source = tmp_path / "gtfs.zip"
    source.write_bytes(b"Sample GTFS data")

    object_key = "german-transport/bronze/gtfs.zip"

    storage.upload_file(
        source_path=str(source),
        object_key=object_key,
    )

    message_id = publish_gtfs_event(
        storage=storage,
        queue=queue,
        object_key=object_key,
    )

    assert queue.message_count() == 1

    received = queue.receive_message()

    assert received is not None
    assert received["message_id"] == message_id
    assert received["body"]["event_type"] == "gtfs_staged"
    assert received["body"]["object_key"] == object_key
    assert received["body"]["file_size"] == len(b"Sample GTFS data")


def test_publish_gtfs_event_missing_file(tmp_path):
    """Do not publish an event if the GTFS file is missing."""

    storage = LocalStorage(base_dir=str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    with pytest.raises(FileNotFoundError):
        publish_gtfs_event(
            storage=storage,
            queue=queue,
            object_key="german-transport/bronze/missing.zip",
        )

    assert queue.message_count() == 0


def test_publish_gtfs_event_invalid_key(tmp_path):
    """Reject unsafe object keys without publishing a message."""

    storage = LocalStorage(base_dir=str(tmp_path / "storage"))
    queue = LocalMessageQueue()

    with pytest.raises(ValueError):
        publish_gtfs_event(
            storage=storage,
            queue=queue,
            object_key="../outside.zip",
        )

    assert queue.message_count() == 0
