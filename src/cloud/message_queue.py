
from collections import deque
from typing import Any
from uuid import uuid4


class LocalMessageQueue:
    """An in-memory queue with acknowledgement, retries and a DLQ."""

    def __init__(self, max_attempts: int = 3):
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        self.max_attempts = max_attempts
        self._messages = deque()
        self._in_flight = {}
        self._dead_letters = deque()

    def send_message(self, body: dict[str, Any]) -> str:
        """Add a new message to the queue."""

        message_id = str(uuid4())

        message = {
            "message_id": message_id,
            "body": body.copy(),
            "attempts": 0,
        }

        self._messages.append(message)
        return message_id

    def receive_message(self) -> dict[str, Any] | None:
        """Receive the next message and record a processing attempt."""

        if not self._messages:
            return None

        message = self._messages.popleft()
        message["attempts"] += 1

        self._in_flight[message["message_id"]] = message

        return message

    def acknowledge_message(self, message_id: str) -> bool:
        """Remove a successfully processed message."""

        return self._in_flight.pop(message_id, None) is not None

    def retry_message(self, message_id: str) -> bool:
        """Retry a failed message or move it to the dead-letter queue."""

        message = self._in_flight.pop(message_id, None)

        if message is None:
            return False

        if message["attempts"] >= self.max_attempts:
            self._dead_letters.append(message)
        else:
            self._messages.appendleft(message)

        return True

    def message_count(self) -> int:
        """Count messages waiting for processing."""

        return len(self._messages)

    def in_flight_count(self) -> int:
        """Count messages currently being processed."""

        return len(self._in_flight)

    def dead_letter_count(self) -> int:
        """Count messages that exceeded the retry limit."""

        return len(self._dead_letters)

    def receive_dead_letter(self) -> dict[str, Any] | None:
        """Retrieve the oldest dead-letter message for inspection."""

        if not self._dead_letters:
            return None

        return self._dead_letters.popleft()
