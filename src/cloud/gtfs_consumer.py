
from src.cloud.message_queue import LocalMessageQueue
from src.cloud.storage import LocalStorage


def process_next_gtfs_event(
    storage: LocalStorage,
    queue: LocalMessageQueue,
) -> bool:
    """Process one GTFS event and acknowledge or retry it."""

    message = queue.receive_message()

    if message is None:
        print("No messages available.")
        return False

    message_id = message["message_id"]

    try:
        body = message["body"]

        if body.get("event_type") != "gtfs_staged":
            raise ValueError("Unsupported event type.")

        object_key = body["object_key"]
        stored_file = storage._get_object_path(object_key)

        if not stored_file.is_file():
            raise FileNotFoundError(
                f"GTFS file not found: {object_key}"
            )

        expected_size = body["file_size"]
        actual_size = stored_file.stat().st_size

        if actual_size != expected_size:
            raise ValueError("GTFS file size does not match the event.")

        queue.acknowledge_message(message_id)

        print(f"GTFS event processed: {object_key}")
        return True

    except (KeyError, ValueError, FileNotFoundError) as error:
        queue.retry_message(message_id)

        print(f"GTFS event processing failed: {error}")
        return False
