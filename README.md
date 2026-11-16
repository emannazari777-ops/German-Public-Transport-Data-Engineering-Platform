
# German Public Transport Data Engineering Platform

**An end-to-end Data Engineering platform for processing, validating, analyzing, and visualizing public transport timetable data using Python, DuckDB, Apache Airflow, Docker, Streamlit, and local cloud simulation.**

**Project Author:** Eman Nazari

**Repository:** https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform

## 1. Project Overview

The German Public Transport Data Engineering Platform is a practical data engineering project that processes public transportation data using the General Transit Feed Specification (GTFS).

The current implementation uses timetable data from the Berlin–Brandenburg region of Germany, provided by Verkehrsverbund Berlin-Brandenburg (VBB).

The project demonstrates:

- GTFS data ingestion and validation
- Bronze, Silver, and Gold data architecture
- Local cloud-style object storage and event-driven messaging
- Automated data processing with Apache Airflow
- SQL analytics using DuckDB
- Data quality monitoring and referential integrity checks
- Dataset metadata and SHA-256 integrity tracking
- Interactive analytics with Streamlit and Plotly
- Automated testing with Pytest
- Continuous integration with GitHub Actions

The platform runs locally without requiring paid AWS services.

## 2. Project Objectives

The main objectives are to:

1. Build a reproducible end-to-end data pipeline.
2. Process large GTFS timetable datasets.
3. Organize raw, cleaned, and analytical data into separate layers.
4. Validate identifiers, relationships, and data quality.
5. Generate analytical datasets using SQL.
6. Automate processing through Apache Airflow.
7. Simulate cloud storage and message-driven ingestion.
8. Visualize processed data through an interactive dashboard.
9. Verify functionality through automated tests.
10. Prepare the architecture for future cloud integration.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data ingestion, processing, and automation |
| Pandas | Data cleaning and transformation |
| DuckDB | SQL analytics and data processing |
| Apache Parquet | Columnar data storage |
| Apache Airflow 3.1 | Pipeline orchestration |
| Docker / Docker Compose | Containerized execution |
| Streamlit | Interactive analytics dashboard |
| Plotly | Interactive data visualization |
| Pytest | Automated testing |
| GitHub Actions | Continuous integration |
| LocalStorage | Local S3-style object storage simulation |
| LocalMessageQueue | Local SQS-style messaging simulation |
| SHA-256 | File integrity verification |
| Git / GitHub | Version control and collaboration |

The current cloud components are local Python implementations.

The project does not currently require actual AWS infrastructure.

## 4. Data Source

The project processes publicly available GTFS timetable data from Verkehrsverbund Berlin-Brandenburg (VBB).

**Data provider:** Verkehrsverbund Berlin-Brandenburg (VBB)

**Provider information:**

https://unternehmen.vbb.de/digitale-services/datensaetze/

**Geographic coverage:** Berlin–Brandenburg, Germany.

The current implementation does not process public transport data from all German regions.

The GTFS archive is stored locally at:

`data/raw/gtfs.zip`

The primary GTFS files include:

- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `calendar_dates.txt`

Raw and processed datasets are excluded from Git because of their size.

The original archive download URL and download timestamp have not been independently verified in the project's metadata.

## 5. Data Architecture

The platform uses a Bronze, Silver, and Gold architecture.

### Bronze Layer

The Bronze layer contains extracted GTFS source files.

**Location:** `data/bronze/`

The ingestion process checks the required files before extracting the archive.

### Silver Layer

The Silver layer contains cleaned and validated datasets stored in Apache Parquet format.

**Location:** `data/silver/`

Processing includes:

- Required-column validation
- Identifier validation
- Duplicate detection
- Coordinate validation
- Timetable and route-field validation
- Calendar and service-date processing
- Referential integrity checks
- Conversion to Parquet

The main Silver datasets are:

| Dataset | Records |
|---|---:|
| Stops | 42,421 |
| Routes | 1,287 |
| Trips | 261,282 |
| Stop Times | 5,785,831 |
| Calendar | 4,485 |
| Calendar Dates | 205,448 |

### Gold Layer

The Gold layer contains analytical datasets generated with DuckDB and SQL.

**Location:** `data/gold/`

| Dataset | Description | Records |
|---|---|---:|
| `top_stops.parquet` | Stops ranked by scheduled stop events | 20 |
| `top_routes.parquet` | Routes ranked by scheduled trips | 20 |
| `stop_connectivity.parquet` | Stops ranked by distinct serving routes | 20 |
| `service_by_weekday.parquet` | Scheduled service analysis by weekday | 7 |

The SQL queries are stored in the `sql/` directory.

These results describe scheduled services, not actual passenger counts or real-time transport performance.

## 6. Local Cloud and Event-Driven Ingestion

The platform includes a local cloud simulation for demonstrating object storage and event-driven processing without provisioning AWS resources.

### Local Object Storage

The `LocalStorage` implementation provides file upload and download operations.

Objects are stored under:

`data/cloud_storage/`

The implementation includes object-key validation and path safety checks.

This demonstrates S3-style object storage concepts, but it is not an actual AWS S3 service.

### Local Message Queue

The `LocalMessageQueue` implementation provides:

- Message publishing
- Message receiving
- Message acknowledgement
- Processing-attempt tracking
- Retry handling
- Dead-letter queue behavior

The queue operates in Python memory.

It does not provide the persistence or distributed messaging capabilities of AWS SQS.

### Integrated Ingestion Workflow

The integrated workflow performs these operations:

1. Stages the GTFS archive in local object storage.
2. Publishes a `gtfs_staged` event.
3. Receives the event through the local queue.
4. Downloads the archived object.
5. Verifies file size and SHA-256 checksum.
6. Replaces the pipeline input archive after successful verification.
7. Acknowledges the processed message.

The workflow is implemented in:

`src/cloud/run_gtfs_ingestion.py`

The publisher and consumer operate within one Python process because the queue is in-memory.

## 7. Apache Airflow Orchestration

Apache Airflow coordinates the end-to-end pipeline.

**DAG ID:** `german_transport_pipeline`

**Execution mode:** Manual (`schedule=None`)

The DAG currently contains 12 sequential tasks.

| Step | Airflow Task | Purpose |
|---|---|---|
| 1 | `cloud_ingestion` | Local cloud-style ingestion |
| 2 | `ingest_gtfs` | Extract and validate GTFS archive |
| 3 | `create_manifest` | Generate archive metadata and SHA-256 |
| 4 | `clean_stops` | Clean stop records |
| 5 | `clean_routes` | Clean route records |
| 6 | `clean_trips` | Clean trip records |
| 7 | `clean_stop_times` | Clean timetable records |
| 8 | `clean_calendar` | Process service calendars |
| 9 | `check_relationships` | Validate data relationships |
| 10 | `build_gold` | Generate analytical datasets |
| 11 | `generate_quality_report` | Generate data quality report |
| 12 | `run_quality_tests` | Execute automated tests |

Each task must complete successfully before the next task begins.

The DAG runs in Docker using project directories mounted from the local machine.

**Latest verified execution:** November 16, 2026.

**Result:** All 12 Airflow tasks completed successfully.

## 8. Dataset Metadata and Lineage

The project generates a metadata manifest for the GTFS source archive.

**Script:** `src/create_manifest.py`

**Output:** `data/metadata/gtfs_manifest.json`

The manifest includes:

- Dataset name
- Archive filename
- File format
- File size
- SHA-256 checksum
- File modification timestamp
- Manifest creation timestamp
- Source URL field
- Download timestamp field

Unverified source information is recorded as null rather than invented.

The manifest is generated automatically during Airflow execution.

This provides basic source-file traceability and integrity metadata.

It is not a complete column-level data lineage system.

## 9. Data Quality and Validation

The project generates a structured data quality report.

**Script:** `src/generate_quality_report.py`

**Output:** `data/metadata/quality_report.json`

The report includes:

- Dataset row counts
- Dataset column counts
- Missing key-value counts
- Duplicate identifier counts
- Referential integrity results
- Overall validation status
- Reported issues

### Latest Verified Results

| Quality Check | Result |
|---|---:|
| Datasets checked | 10 |
| Duplicate stop IDs | 0 |
| Duplicate route IDs | 0 |
| Duplicate trip IDs | 0 |
| Unknown trip references | 0 |
| Unknown stop references | 0 |
| Reported issues | 0 |

**Overall status: PASS**

All currently configured quality checks passed.

This does not imply that every possible data quality issue has been tested.

The report is generated automatically as part of the Airflow pipeline.

## 10. Interactive Analytics Dashboard

The platform includes an interactive dashboard built with Streamlit and Plotly.

**Application:** `dashboard/app.py`

The dashboard reads Gold-layer Parquet datasets and the data quality report.

### Dashboard Features

**Overview**

Displays:

- Total stops
- Total routes
- Total scheduled trips
- Total stop-time records
- Current data quality status

**Top Stops**

Interactive horizontal bar chart showing stops ranked by scheduled stop events.

**Top Routes**

Interactive chart showing routes ranked by scheduled trips.

**Stop Connectivity**

Interactive chart showing stops with the highest number of distinct serving routes.

**Weekly Service Patterns**

Interactive chart showing average scheduled trips per active service date for each weekday.

**Data Quality**

Displays the current validation status, reported issues, and detailed JSON quality report.

### Interactive Features

- Sidebar chart filters
- Interactive Plotly charts
- Hover information
- Expandable data tables
- Data quality indicators

### Run the Dashboard

From the project root:

```powershell
python -m streamlit run dashboard/app.py
```

Open:

http://localhost:8501

The dashboard requires Gold-layer datasets generated by the pipeline.

## 11. Testing and Continuous Integration

The project uses Pytest for automated validation.

Tests cover:

- GTFS cleaning and transformations
- Required fields and identifiers
- Calendar processing
- Data relationships
- Gold-layer analytics
- Local object storage
- Event publishing and consumption
- Queue acknowledgement and retries
- Dead-letter queue behavior
- Archive integrity verification
- Manifest generation
- Data quality reporting

### Verified Test Results

| Environment | Result |
|---|---|
| Windows local environment | 90 tests passed |
| GitHub Actions CI | 58 tests passed |
| Apache Airflow | 12 of 12 tasks successful |

The latest confirmed GitHub Actions result relates to commit `9c274e4`.

The newer Dashboard and 12-task Airflow changes have not yet been committed and pushed at the time of this README update.

### GitHub Actions

Workflow:

`.github/workflows/ci.yml`

GitHub Actions runs dataset-independent tests because the large GTFS and Parquet files are not committed to the repository.

The complete dataset-dependent test suite is executed locally after the required datasets are generated.

### Run Local Tests

```powershell
python -m pytest tests/ -q
```

## 12. Running the Project

### Prerequisites

- Python 3.10 or a compatible version
- Docker Desktop
- Docker Compose
- Git
- Access to the VBB GTFS dataset

### Step 1 — Clone the Repository

```powershell
git clone https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform.git

cd German-Public-Transport-Data-Engineering-Platform
```

### Step 2 — Create a Virtual Environment

```powershell
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3 — Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

The requirements file must include the Dashboard dependencies before the next GitHub release.

### Step 4 — Prepare GTFS Data

Download a compatible GTFS archive from the VBB data provider.

Place the archive at:

`data/raw/gtfs.zip`

The archive must contain the required GTFS files.

The dataset is not included in GitHub.

### Step 5 — Start Apache Airflow

```powershell
docker compose -f airflow/docker-compose.yml up -d
```

Open the Airflow interface:

http://localhost:8080

### Step 6 — Execute the Pipeline

In the Airflow interface:

1. Locate `german_transport_pipeline`.
2. Enable the DAG if necessary.
3. Trigger a manual run.
4. Monitor all 12 tasks.
5. Confirm that the DAG finishes successfully.

### Step 7 — Inspect the Results

After successful execution, check:

- `data/bronze/`
- `data/silver/`
- `data/gold/`
- `data/metadata/`

The Gold directory should contain:

- `top_stops.parquet`
- `top_routes.parquet`
- `stop_connectivity.parquet`
- `service_by_weekday.parquet`

The metadata directory should contain:

- `gtfs_manifest.json`
- `quality_report.json`

### Step 8 — Start the Dashboard

```powershell
python -m streamlit run dashboard/app.py
```

Open:

http://localhost:8501

### Step 9 — Run Tests

```powershell
python -m pytest tests/ -q
```

The complete test suite requires locally generated datasets.

## 13. Project Structure

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
|-- dashboard/
|   `-- app.py
|
|-- data/
|   |-- raw/
|   |-- bronze/
|   |-- silver/
|   |-- gold/
|   |-- metadata/
|   `-- cloud_storage/
|
|-- docs/
|
|-- docker/
|
|-- sql/
|   |-- top_stops.sql
|   |-- top_routes.sql
|   |-- stop_connectivity.sql
|   `-- service_by_weekday.sql
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
|   |-- clean_calendar.py
|   |-- check_relationships.py
|   |-- run_gold.py
|   |-- create_manifest.py
|   `-- generate_quality_report.py
|
|-- tests/
|-- .gitignore
|-- requirements.txt
`-- README.md
```

The `data/` directory contains local datasets and generated outputs and is excluded from Git.

## 14. Current Scope and Limitations

The platform is functional in a local development environment, with the following limitations:

**Regional coverage:** The current dataset covers Berlin–Brandenburg, not all of Germany.

**Local cloud simulation:** Storage and messaging are implemented locally rather than through actual AWS services.

**In-memory queue:** Queue messages do not persist across process restarts.

**Manual orchestration:** The Airflow DAG uses manual triggering rather than a recurring schedule.

**Scheduled timetable data:** The project does not contain actual passenger counts, live vehicle positions, or real-time delays.

**Local dataset dependency:** Full pipeline execution requires the source GTFS archive.

**CI scope:** GitHub Actions runs dataset-independent tests rather than the complete dataset-dependent integration suite.

These limitations distinguish implemented functionality from planned extensions.

## 15. Future Improvements

Potential future improvements include:

- S3-compatible local API integration
- SQS-compatible local messaging integration
- Lambda-style event processing simulation
- IAM-style access-control demonstrations
- PostgreSQL integration as a local database service
- Docker-based server deployment demonstrations
- Scheduled GTFS ingestion
- Persistent message processing
- Improved operational monitoring
- Additional regional GTFS feeds
- Further Dashboard enhancements

These capabilities are planned extensions and are not presented as completed features.

## 16. Conclusion

The German Public Transport Data Engineering Platform demonstrates an end-to-end local data engineering workflow.

The implementation combines:

- Event-driven ingestion simulation
- Layered data processing
- SQL analytics
- Workflow orchestration
- Automated data validation
- Metadata and integrity tracking
- Interactive visualization
- Automated testing
- Continuous integration

The platform provides a practical foundation for further development toward cloud-based data engineering systems.

---

**Author:** Eman Nazari

**Project:** German Public Transport Data Engineering Platform

**Repository:** https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform
