
from pathlib import Path
from zipfile import ZipFile
import shutil


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze"

REQUIRED_FILES = [
    "agency.txt",
    "stops.txt",
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "calendar.txt",
    "calendar_dates.txt",
]


def ingest_gtfs():
    archive_path = RAW_DIR / "gtfs.zip"
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    if not archive_path.exists():
        raise FileNotFoundError(f"GTFS archive not found: {archive_path}")

    with ZipFile(archive_path) as archive:
        available_files = set(archive.namelist())

        for filename in REQUIRED_FILES:
            if filename not in available_files:
                raise ValueError(f"Missing GTFS file: {filename}")

        for filename in REQUIRED_FILES:
            destination = BRONZE_DIR / filename

            with archive.open(filename) as source:
                with destination.open("wb") as target:
                    shutil.copyfileobj(source, target)

            print(f"Ingested: {filename}")

    print("Bronze ingestion completed successfully.")


if __name__ == "__main__":
    ingest_gtfs()
