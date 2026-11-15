
import pytest

from src.cloud.message_queue import LocalMessageQueue


def test_message_moves_to_dlq_after_three_failures():
    """Move a message to the DLQ after three failed attempts."""

    queue = LocalMessageQueue(max_attempts=3)

    message_id = queue.send_message({
        "event_type": "gtfs_staged",
        "object_key": "bronze/missing.zip",
    })

    for attempt in range(1, 4):
        message = queue.receive_message()

        assert message is not None
        assert message["message_id"] == message_id
        assert message["attempts"] == attempt

        assert queue.retry_message(message_id) is True

    assert queue.message_count() == 0
    assert queue.in_flight_count() == 0
    assert queue.dead_letter_count() == 1

    failed_message = queue.receive_dead_letter()

    assert failed_message["message_id"] == message_id
    assert failed_message["attempts"] == 3
    assert queue.dead_letter_count() == 0


def test_successful_message_does_not_enter_dlq():
    """A successfully acknowledged message must not enter the DLQ."""

    queue = LocalMessageQueue(max_attempts=3)

    queue.send_message({"event_type": "gtfs_staged"})

    message = queue.receive_message()

    assert message is not None
    assert queue.acknowledge_message(message["message_id"]) is True

    assert queue.message_count() == 0
    assert queue.in_flight_count() == 0
    assert queue.dead_letter_count() == 0


def test_message_can_succeed_after_retry():
    """A retried message can still be processed successfully."""

    queue = LocalMessageQueue(max_attempts=3)

    message_id = queue.send_message({"event_type": "gtfs_staged"})

    first_attempt = queue.receive_message()
    assert first_attempt is not None

    assert queue.retry_message(message_id) is True

    second_attempt = queue.receive_message()

    assert second_attempt is not None
    assert second_attempt["attempts"] == 2

    assert queue.acknowledge_message(message_id) is True

    assert queue.message_count() == 0
    assert queue.dead_letter_count() == 0


def test_empty_dead_letter_queue():
    """An empty DLQ should return None."""

    queue = LocalMessageQueue()

    assert queue.receive_dead_letter() is None
    assert queue.dead_letter_count() == 0


def test_invalid_max_attempts():
    """The retry limit must be at least one."""

    with pytest.raises(ValueError):
        LocalMessageQueue(max_attempts=0)
