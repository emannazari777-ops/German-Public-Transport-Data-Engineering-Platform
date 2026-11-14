from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def download_gtfs(url: str, filename: str = "gtfs.zip") -> Path:
    """Download a GTFS ZIP archive to the raw data directory."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    destination = RAW_DATA_DIR / filename

    with requests.get(url, stream=True, timeout=(15, 120)) as response:
        response.raise_for_status()

        with destination.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    return destination


if __name__ == "__main__":
    print("GTFS downloader is ready.")
    print(f"Download directory: {RAW_DATA_DIR}")