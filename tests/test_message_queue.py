
from src.cloud.message_queue import LocalMessageQueue


def test_send_and_receive_message():
    """Verify that a message can be sent and received."""

    queue = LocalMessageQueue()

    message_id = queue.send_message({
        "event": "gtfs_uploaded",
        "file": "german-transport/bronze/gtfs.zip",
    })

    assert queue.message_count() == 1

    message = queue.receive_message()

    assert message is not None
    assert message["message_id"] == message_id
    assert message["body"]["event"] == "gtfs_uploaded"
    assert queue.message_count() == 0
    assert queue.in_flight_count() == 1


def test_messages_are_received_in_order():
    """Verify FIFO ordering for the local queue."""

    queue = LocalMessageQueue()

    queue.send_message({"file": "stops.txt"})
    queue.send_message({"file": "routes.txt"})
    queue.send_message({"file": "trips.txt"})

    first = queue.receive_message()
    second = queue.receive_message()
    third = queue.receive_message()

    assert first["body"]["file"] == "stops.txt"
    assert second["body"]["file"] == "routes.txt"
    assert third["body"]["file"] == "trips.txt"


def test_receive_from_empty_queue():
    """An empty queue should return None."""

    queue = LocalMessageQueue()

    assert queue.receive_message() is None
    assert queue.message_count() == 0


def test_each_message_has_unique_id():
    """Every message should have a unique identifier."""

    queue = LocalMessageQueue()

    first_id = queue.send_message({"event": "first"})
    second_id = queue.send_message({"event": "second"})

    assert first_id != second_id
    assert queue.message_count() == 2


def test_acknowledge_message():
    """Acknowledge a message after successful processing."""

    queue = LocalMessageQueue()

    queue.send_message({"event": "gtfs_staged"})
    message = queue.receive_message()

    assert message is not None
    assert queue.in_flight_count() == 1

    result = queue.acknowledge_message(message["message_id"])

    assert result is True
    assert queue.in_flight_count() == 0
    assert queue.message_count() == 0


def test_retry_failed_message():
    """Return a failed message to the queue."""

    queue = LocalMessageQueue()

    queue.send_message({"event": "gtfs_staged"})
    message = queue.receive_message()

    assert message is not None

    result = queue.retry_message(message["message_id"])

    assert result is True
    assert queue.message_count() == 1
    assert queue.in_flight_count() == 0

    retried_message = queue.receive_message()

    assert retried_message["message_id"] == message["message_id"]
    assert retried_message["body"] == message["body"]


def test_acknowledge_unknown_message():
    """Reject acknowledgement of an unknown message."""

    queue = LocalMessageQueue()

    assert queue.acknowledge_message("unknown-id") is False


def test_retry_unknown_message():
    """Reject retry requests for unknown messages."""

    queue = LocalMessageQueue()

    assert queue.retry_message("unknown-id") is False
