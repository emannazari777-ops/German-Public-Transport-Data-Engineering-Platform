
from pathlib import Path
import shutil


class LocalStorage:
    """Store and retrieve files within a local storage directory."""

    def __init__(self, base_dir: str = "data/cloud_storage"):
        self.base_dir = Path(base_dir).resolve()

    def _get_object_path(self, object_key: str) -> Path:
        """Validate an object key and resolve its storage path."""

        if not isinstance(object_key, str) or not object_key:
            raise ValueError("Object key must be a non-empty string.")

        # Use forward slashes for S3-compatible object keys.
        if "\\" in object_key:
            raise ValueError("Backslashes are not allowed in object keys.")

        if object_key.startswith("/"):
            raise ValueError("Absolute paths are not allowed.")

        # Reject Windows drive paths and unsafe path components.
        if ":" in object_key:
            raise ValueError("Colons are not allowed in object keys.")

        parts = object_key.split("/")

        if any(part in ("", ".", "..") for part in parts):
            raise ValueError("Invalid object key path.")

        destination = (self.base_dir / Path(*parts)).resolve()

        # Ensure the destination remains inside the storage directory.
        if not destination.is_relative_to(self.base_dir):
            raise ValueError(
                "Object key points outside the storage directory."
            )

        return destination

    def upload_file(self, source_path: str, object_key: str) -> Path:
        """Copy a file into local object storage."""

        source = Path(source_path)

        if not source.is_file():
            raise FileNotFoundError(
                f"Source file not found: {source}"
            )

        destination = self._get_object_path(object_key)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(source, destination)

        return destination

    def download_file(self, object_key: str, destination_path: str) -> Path:
        """Retrieve a file from local object storage."""

        source = self._get_object_path(object_key)

        if not source.is_file():
            raise FileNotFoundError(
                f"Stored file not found: {object_key}"
            )

        destination = Path(destination_path)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(source, destination)

        return destination
