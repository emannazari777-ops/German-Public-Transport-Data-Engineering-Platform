# German Public Transport Data Engineering Platform

**An end-to-end Data Engineering project for processing and analyzing public transport timetable data using Python, DuckDB, Apache Airflow, Docker, and a local cloud simulation.**

**Project Author:** Eman Nazari

## 1. Project Overview

The German Public Transport Data Engineering Platform is a practical data engineering project designed to ingest, validate, transform, and analyze public transportation data using the General Transit Feed Specification (GTFS).

The current implementation processes timetable data from the Berlin-Brandenburg region of Germany, provided by Verkehrsverbund Berlin-Brandenburg (VBB).

The project demonstrates an end-to-end ETL workflow with a Bronze, Silver, and Gold data architecture, event-driven ingestion simulation, automated orchestration, data quality checks, and continuous integration.

The platform is designed to run locally without requiring paid cloud services.

## 2. Project Objectives

- Build a reproducible data engineering pipeline.
- Process large GTFS timetable datasets.
- Organize data using Bronze, Silver, and Gold layers.
- Implement data cleaning and referential integrity checks.
- Generate analytical datasets using SQL and DuckDB.
- Orchestrate processing with Apache Airflow.
- Simulate cloud object storage and event-driven messaging.
- Implement message acknowledgement, retries, and dead-letter handling.
- Validate the pipeline using automated tests.
- Run continuous integration checks through GitHub Actions.
- Provide a foundation for future deployment using AWS services.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data ingestion, transformation, and processing |
| Pandas | Data cleaning and validation |
| DuckDB | SQL processing and analytical transformations |
| Apache Parquet | Efficient columnar data storage |
| Apache Airflow 3.1 | Workflow orchestration |
| Docker / Docker Compose | Containerized execution |
| Pytest | Automated testing |
| GitHub Actions | Continuous integration |
| LocalStorage | Local simulation of S3-style object storage |
| LocalMessageQueue | Local simulation of SQS-style messaging |
| Git and GitHub | Version control and project sharing |

The cloud components are local implementations. The project does not currently provision or use AWS S3, SQS, or EC2 resources for its execution.

## 4. Data Source

The project uses publicly available GTFS timetable data from Verkehrsverbund Berlin-Brandenburg (VBB).

**Data provider:** Verkehrsverbund Berlin-Brandenburg (VBB)

**Source:** https://unternehmen.vbb.de/digitale-services/datensaetze/

The main GTFS files used are:

- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`

The downloaded GTFS archive is stored in:

`data/raw/gtfs.zip`

Raw and processed datasets are excluded from Git because of their size.

**Geographic coverage:** The current dataset covers Berlin-Brandenburg. The project architecture could be extended to other German transport feeds, but nationwide processing has not yet been implemented.

## 5. Data Architecture

The project follows a layered data architecture.

### Bronze Layer

The Bronze layer contains the original GTFS text files extracted from the source archive.

Location: `data/bronze/`

The ingestion process checks that required GTFS files are present before extracting them.

### Silver Layer

The Silver layer contains cleaned and validated Parquet datasets.

Location: `data/silver/`

The processing includes:

- Validation of required columns and identifiers.
- Detection of duplicate identifiers.
- Coordinate validation.
- Validation of route and timetable fields.
- Conversion to Parquet.
- Referential integrity checks between stops, trips, and stop times.

### Gold Layer

The Gold layer contains analytical datasets generated using DuckDB and SQL.

Location: `data/gold/`

**Generated datasets:**

| File | Description |
|---|---|
| `top_stops.parquet` | Top 20 GTFS stop IDs by scheduled stop events |
| `top_routes.parquet` | Top 20 GTFS route IDs by scheduled trips |

These metrics describe scheduled services, not actual passenger counts.

## 6. Local Cloud and Event-Driven Ingestion

The project includes a local cloud simulation to demonstrate object storage and message-based processing without incurring cloud costs.

### Local Object Storage

The `LocalStorage` class provides file upload and download operations.

It stores objects under:

`data/cloud_storage/`

The implementation includes object-key validation and path safety checks.

### Message Queue

The `LocalMessageQueue` class provides:

- Message publishing and receiving.
- Message acknowledgement.
- Processing-attempt tracking.
- Retry handling.
- Dead Letter Queue (DLQ) support.

The queue is implemented in Python memory. It is intended for local demonstrations and does not provide the persistence or distributed messaging capabilities of AWS SQS.

### Integrated Cloud Ingestion

The integrated ingestion workflow:

1. Stages the GTFS archive in local object storage.
2. Publishes a `gtfs_staged` event.
3. Receives the event through the local queue.
4. Downloads the archive from storage.
5. Verifies file size and SHA-256 checksum.
6. Prepares the verified archive for Bronze ingestion.
7. Acknowledges the message after successful processing.

The publisher and consumer run within one Python process because the queue is in-memory.

This workflow is implemented in:

`src/cloud/run_gtfs_ingestion.py`

## 7. Apache Airflow Orchestration

Apache Airflow coordinates the complete processing workflow.

**DAG ID:** `german_transport_pipeline`

**Execution mode:** Manual (`schedule=None`)

The DAG contains nine sequential tasks:

1. `cloud_ingestion`
2. `ingest_gtfs`
3. `clean_stops`
4. `clean_routes`
5. `clean_trips`
6. `clean_stop_times`
7. `check_relationships`
8. `build_gold`
9. `run_quality_tests`

Each task must complete successfully before the next task begins.

The pipeline runs inside a Docker container, with project source code, SQL scripts, tests, and data directories mounted from the local machine.

**Verified execution:** On November 15, 2026, all nine Airflow tasks completed successfully in approximately 70 seconds.

## 8. Processing Results

The tested VBB GTFS dataset produced the following Silver-layer results:

| Dataset | Records |
|---|---:|
| Stops | 42,421 |
| Routes | 1,287 |
| Trips | 261,282 |
| Stop Times | 5,785,831 |

Referential integrity checks reported:

- Unknown trip IDs: **0**
- Unknown stop IDs: **0**

Both Gold-layer datasets contain 20 records.

### Top Scheduled Stops

Examples from the Gold output:

| Stop | Scheduled Stop Events |
|---|---:|
| Hertzallee (Berlin), platform ID ending `::3` | 6,170 |
| S+U Zoologischer Garten Bhf (Berlin) | 5,606 |
| Hertzallee (Berlin), platform ID ending `::2` | 5,128 |
| S Savignyplatz (Berlin) | 4,194 |
| Berlin, Moritzstr. | 3,925 |

### Top Scheduled Routes

| Route | Scheduled Trips |
|---|---:|
| U6 | 3,094 |
| M4 | 2,620 |
| M41 | 2,325 |
| U3 | 2,060 |
| M32 | 2,051 |

GTFS identifiers may represent individual platforms or route variants. The results should not be interpreted as passenger-demand rankings.

## 9. Testing and Continuous Integration

The project uses Pytest for automated validation.

Tests cover:

- GTFS data cleaning.
- Required fields and identifiers.
- Data relationships.
- Analytical Gold outputs.
- Local object storage.
- GTFS event publishing and consumption.
- Queue acknowledgement and retries.
- Dead Letter Queue behavior.
- File integrity verification.

### Verified Test Results

| Environment | Result |
|---|---|
| Windows local environment | 76 tests passed |
| GitHub Actions CI | 50 tests passed |
| Airflow full DAG execution | 9 of 9 tasks successful |

The latest verified GitHub Actions run completed successfully for commit `46d33ec` on November 15, 2026.

GitHub Actions runs dataset-independent tests because the large GTFS and Parquet datasets are not committed to the repository.

The complete dataset-dependent test suite is executed locally after preparing the data.

**GitHub Actions workflow:** `.github/workflows/ci.yml`

## 10. Running the Project

### Prerequisites

- Python 3.10 or a compatible version.
- Docker Desktop with Docker Compose.
- Git.
- Access to the VBB GTFS dataset.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform.git
cd German-Public-Transport-Data-Engineering-Platform
```

### Step 2 — Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 3 — Prepare the GTFS Dataset

Download a compatible GTFS archive from the VBB data source and place it at:

`data/raw/gtfs.zip`

The archive must contain the GTFS files listed in the Data Source section.

The dataset is not included in the repository.

### Step 4 — Start Apache Airflow

```bash
docker compose -f airflow/docker-compose.yml up -d
```

The container installs the Python packages specified in the Docker Compose configuration when starting.

Open the Airflow interface:

http://localhost:8080

### Step 5 — Execute the Pipeline

In the Airflow interface:

1. Locate the `german_transport_pipeline` DAG.
2. Enable the DAG if necessary.
3. Trigger a manual run.
4. Monitor the nine tasks.
5. Confirm that the DAG finishes successfully.

### Step 6 — Inspect the Results

After successful execution, check:

`data/silver/`

`data/gold/`

The Gold directory should contain:

- `top_stops.parquet`
- `top_routes.parquet`

### Step 7 — Run Local Tests

From the project root:

```bash
python -m pytest tests/ -q
```

The full suite requires the locally generated datasets.

## 11. Project Structure

```text
German-Public-Transport-Data-Engineering-Platform/
|
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|
|-- airflow/
|   |-- dags/
|   |   `-- transport_pipeline.py
|   `-- docker-compose.yml
|
|-- data/                   # Local datasets, excluded from Git
|   |-- raw/
|   |-- bronze/
|   |-- silver/
|   |-- gold/
|   `-- cloud_storage/
|
|-- docs/
|-- docker/
|
|-- sql/
|   |-- top_stops.sql
|   `-- top_routes.sql
|
|-- src/
|   |-- cloud/
|   |   |-- storage.py
|   |   |-- message_queue.py
|   |   |-- gtfs_event.py
|   |   |-- gtfs_consumer.py
|   |   `-- run_gtfs_ingestion.py
|   |
|   |-- ingest_gtfs.py
|   |-- clean_stops.py
|   |-- clean_routes.py
|   |-- clean_trips.py
|   |-- clean_stop_times.py
|   |-- check_relationships.py
|   `-- run_gold.py
|
|-- tests/
|-- .gitignore
|-- requirements.txt
`-- README.md
```

## 12. Current Scope and Limitations

The project is a functional local data engineering platform with several limitations:

- **Regional dataset:** The current data covers Berlin-Brandenburg, not all of Germany.
- **Local cloud simulation:** Object storage and messaging are implemented locally rather than through actual AWS infrastructure.
- **In-memory messaging:** Queue messages are not persisted across process restarts.
- **Manual orchestration:** The Airflow DAG is triggered manually rather than through a recurring schedule.
- **Static timetables:** GTFS schedule data is processed; real-time vehicle positions and passenger counts are not available.
- **Local data dependency:** Full pipeline execution requires downloading the source dataset.
- **CI scope:** GitHub Actions executes dataset-independent tests rather than the entire data-dependent integration suite.

These limitations are documented to distinguish implemented functionality from potential future enhancements.

## 13. Future Improvements

Potential extensions include:

- AWS S3 integration for object storage.
- AWS SQS integration for durable event messaging.
- Deployment on AWS EC2 or another cloud execution environment.
- Scheduled GTFS ingestion.
- Persistent event processing and improved retry handling.
- Pipeline monitoring and operational metrics.
- A visualization dashboard.
- Integration of additional regional GTFS feeds to expand coverage across Germany.

These are future improvements and are not presented as completed features.

## 14. Conclusion

The German Public Transport Data Engineering Platform demonstrates a working end-to-end data processing pipeline built with Python, Pandas, DuckDB, Apache Airflow, Docker, and Parquet.

The project integrates local cloud-style ingestion, message processing, layered data transformations, SQL analytics, data quality validation, automated testing, and GitHub Actions CI.

It provides a reproducible local implementation and a foundation for further development toward a cloud-based public transport data platform.

---

**Author:** Eman Nazari

**Project:** German Public Transport Data Engineering Platform

**Repository:** https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform