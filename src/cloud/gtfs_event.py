
from pathlib import Path

from src.cloud.message_queue import LocalMessageQueue
from src.cloud.storage import LocalStorage


def publish_gtfs_event(
    storage: LocalStorage,
    queue: LocalMessageQueue,
    object_key: str,
) -> str:
    """Publish an event after confirming the GTFS file exists."""

    stored_file = storage._get_object_path(object_key)

    if not stored_file.is_file():
        raise FileNotFoundError(
            f"GTFS file not found in storage: {object_key}"
        )

    message = {
        "event_type": "gtfs_staged",
        "object_key": object_key,
        "file_size": stored_file.stat().st_size,
    }

    return queue.send_message(message)


def main() -> None:
    """Demonstrate a local GTFS storage event."""

    object_key = "german-transport/bronze/gtfs.zip"

    storage = LocalStorage(base_dir="data/cloud_storage")
    queue = LocalMessageQueue()

    message_id = publish_gtfs_event(
        storage=storage,
        queue=queue,
        object_key=object_key,
    )

    print(f"Event published: {message_id}")
    print(f"Messages waiting: {queue.message_count()}")

    received = queue.receive_message()

    if received is None:
        raise RuntimeError("Expected a GTFS event in the queue.")

    print(f"Event received: {received['body']['event_type']}")
    print(f"Object key: {received['body']['object_key']}")
    print(f"File size: {received['body']['file_size']:,} bytes")


if __name__ == "__main__":
    main()
