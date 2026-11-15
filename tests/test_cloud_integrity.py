
from src.cloud.verify_gtfs import calculate_sha256


def test_sha256_same_content(tmp_path):
    """Files with identical content must have identical hashes."""

    first_file = tmp_path / "first.txt"
    second_file = tmp_path / "second.txt"

    first_file.write_text("German Public Transport", encoding="utf-8")
    second_file.write_text("German Public Transport", encoding="utf-8")

    first_hash = calculate_sha256(first_file)
    second_hash = calculate_sha256(second_file)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_sha256_different_content(tmp_path):
    """Files with different content should produce different hashes."""

    first_file = tmp_path / "first.txt"
    second_file = tmp_path / "second.txt"

    first_file.write_text("Berlin Transport", encoding="utf-8")
    second_file.write_text("Hamburg Transport", encoding="utf-8")

    assert calculate_sha256(first_file) != calculate_sha256(second_file)


def test_sha256_empty_file(tmp_path):
    """Verify the known SHA-256 checksum of an empty file."""

    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")

    expected_hash = (
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855"
    )

    assert calculate_sha256(empty_file) == expected_hash
