# German Public Transport Data Engineering Platform

## Project Overview

An end-to-end Data Engineering project that processes public transportation timetable data from Germany using GTFS (General Transit Feed Specification).

The platform demonstrates data ingestion, transformation, validation, analytical modeling, automated testing, and workflow orchestration.

The project currently uses public transport data from the Berlin-Brandenburg region (VBB).

## Project Objectives

- Build a reproducible data processing pipeline.
- Implement a Bronze, Silver, and Gold data architecture.
- Process large-scale GTFS timetable datasets.
- Validate data quality and referential integrity.
- Generate analytical datasets using SQL.
- Automate the pipeline with Apache Airflow.
- Run automated quality tests using Pytest.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data ingestion and transformation |
| Pandas | Data cleaning and validation |
| DuckDB | Large-scale processing and SQL analytics |
| Apache Parquet | Columnar data storage |
| Apache Airflow | Pipeline orchestration |
| Docker | Containerized execution environment |
| Pytest | Automated data quality testing |
| Git and GitHub | Version control and project sharing |

## Data Source

The project uses publicly available GTFS timetable data from Verkehrsverbund Berlin-Brandenburg (VBB).

Source: https://unternehmen.vbb.de/digitale-services/datensaetze/

GTFS files used:

- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`

## Data Architecture

**Bronze Layer**

Raw GTFS files are extracted from the downloaded archive and stored without analytical transformations.

**Silver Layer**

GTFS data is cleaned, validated, and converted into Parquet datasets.

The processing includes validation of identifiers, coordinates, timetable fields, and relationships between datasets.

**Gold Layer**

DuckDB and SQL are used to create analytical outputs:

- `top_stops.parquet`: Top 20 stop IDs by scheduled stop events.
- `top_routes.parquet`: Top 20 route IDs by scheduled trips.

These metrics describe scheduled transportation services, not actual passenger demand or ridership.

## Pipeline Orchestration

Apache Airflow orchestrates eight tasks:

1. `ingest_gtfs`
2. `clean_stops`
3. `clean_routes`
4. `clean_trips`
5. `clean_stop_times`
6. `check_relationships`
7. `build_gold`
8. `run_quality_tests`

The pipeline uses manual triggering (`schedule=None`) and processes the stages in sequence.

## Processing Results

Results from the tested VBB GTFS dataset:

| Dataset | Records |
|---|---:|
| Stops | 42,421 |
| Routes | 1,287 |
| Trips | 261,282 |
| Stop Times | 5,785,831 |

Both Gold analytical outputs contain 20 rows.

Referential integrity validation reported:

- Unknown trip IDs: 0
- Unknown stop IDs: 0

## Testing and Validation

The project includes 26 automated Pytest tests covering the Silver and Gold datasets.

**Verified results:**

- 26 tests passed on Windows.
- 26 tests passed inside the Docker container.
- All eight Airflow tasks completed successfully in the first full DAG run.

## Running the Project

### Prerequisites

- Python
- Docker Desktop with Docker Compose
- Access to the public VBB GTFS dataset

### Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

### Prepare the Data

Run the GTFS download script from the project root:

```bash
python src/download_gtfs.py
```

The source dataset is stored locally and excluded from Git.

### Start Airflow

```bash
docker compose -f airflow/docker-compose.yml up -d
```

Open:

http://localhost:8080

Find the `german_transport_pipeline` DAG, enable it, and trigger a manual run.

### Run Automated Tests

After generating the processed datasets:

```bash
python -m pytest tests/ -v
```

## Project Structure

```text
German-Public-Transport-Data-Engineering-Platform/
├── airflow/
│   ├── dags/
│   │   └── transport_pipeline.py
│   └── docker-compose.yml
├── data/                  # Local data (not committed)
├── docs/
├── docker/
├── sql/
│   ├── top_stops.sql
│   └── top_routes.sql
├── src/
├── tests/
├── .gitignore
├── requirements.txt
└── README.md
```

## Current Scope and Limitations

- The current implementation uses local files mounted into Docker, rather than AWS cloud storage.
- The dataset represents scheduled GTFS services, not real-time vehicle locations.
- The DAG requires a locally downloaded GTFS archive and is triggered manually.
- The analytical outputs are grouped by GTFS stop and route identifiers, which may represent separate platforms or services with similar names.
- Automated GitHub CI and cloud deployment have not yet been implemented.

## Future Improvements

Potential enhancements include AWS S3 integration, continuous integration, monitoring, and a visualization dashboard.

## Conclusion

This project demonstrates practical Data Engineering skills through a working, containerized ETL pipeline with layered data storage, SQL analytics, data validation, automated tests, and Apache Airflow orchestration.