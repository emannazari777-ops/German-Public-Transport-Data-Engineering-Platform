
# German Public Transport Data Engineering Platform

**An end-to-end data engineering platform for processing, validating, analyzing, and visualizing German public transport timetable data.**

**Author:** Eman Nazari  
**Repository:** https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform

---

## 1. Project Overview

The German Public Transport Data Engineering Platform is a practical data engineering project built around the General Transit Feed Specification (GTFS).

The platform processes public transport timetable data through a Bronze, Silver, and Gold architecture. It combines Python, DuckDB, Apache Airflow, Docker, PostgreSQL, and Streamlit to demonstrate the main stages of a modern data engineering workflow.

The current implementation uses GTFS data from the **Berlin–Brandenburg region of Germany**, provided by Verkehrsverbund Berlin-Brandenburg (VBB).

The platform runs locally without requiring paid cloud services.

### Key Features

- GTFS data ingestion and validation
- Bronze, Silver, and Gold data architecture
- Local S3-style object storage simulation
- Local SQS-style event-driven messaging
- Automated data pipelines using Apache Airflow
- Data processing and SQL analytics using DuckDB
- PostgreSQL analytical database
- Data quality validation and monitoring
- SHA-256 integrity verification
- Interactive Streamlit dashboard
- Automated testing with Pytest
- Continuous integration with GitHub Actions

> **Important:** The current project uses local cloud simulations rather than actual AWS services. Its geographic coverage is Berlin–Brandenburg, not all of Germany.

---

## 2. Project Objectives

The project aims to:

1. Build an end-to-end data engineering workflow.
2. Process large public transport timetable datasets.
3. Implement a structured Bronze–Silver–Gold data architecture.
4. Clean and validate GTFS data.
5. Perform analytical transformations using SQL.
6. Automate data processing through Apache Airflow.
7. Demonstrate event-driven ingestion concepts.
8. Store analytical results in PostgreSQL.
9. Present data through an interactive dashboard.
10. Validate the system through automated testing.

---

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and pipeline development |
| Pandas | Data cleaning and validation |
| DuckDB | SQL processing and analytical transformations |
| Apache Parquet | Efficient columnar data storage |
| Apache Airflow 3.1 | Workflow orchestration |
| Docker | Containerized execution |
| Docker Compose | Container configuration and networking |
| PostgreSQL 16 | Analytical database |
| Psycopg 3 | Python and PostgreSQL integration |
| Streamlit | Interactive analytics dashboard |
| Plotly | Interactive data visualization |
| Pytest | Automated testing |
| GitHub Actions | Continuous integration |
| SHA-256 | Data integrity verification |
| Git / GitHub | Version control and project documentation |

### Cloud Architecture Concepts

The project includes local implementations of:

- S3-style object storage
- SQS-style message processing
- Event-driven ingestion
- Message acknowledgements and retries
- Dead-letter queue behavior

These components demonstrate cloud engineering concepts without provisioning actual AWS infrastructure.

---

## 4. Data Source

**Data provider:** Verkehrsverbund Berlin-Brandenburg (VBB)

**Provider information:**  
https://unternehmen.vbb.de/digitale-services/datensaetze/

**Geographic coverage:** Berlin–Brandenburg, Germany

**Data format:** General Transit Feed Specification (GTFS)

The GTFS archive is stored locally at:

`data/raw/gtfs.zip`

### Main GTFS Files

| File | Description |
|---|---|
| `agency.txt` | Transport operators |
| `stops.txt` | Public transport stops and stations |
| `routes.txt` | Transport routes |
| `trips.txt` | Scheduled trips |
| `stop_times.txt` | Scheduled arrival and departure events |
| `calendar.txt` | Regular service calendars |
| `calendar_dates.txt` | Service exceptions |

Raw and generated datasets are not committed to GitHub because of their size.

The original download URL and timestamp of the current archive have not been independently verified in the project metadata.

---

## 5. Data Architecture

The platform follows a Bronze–Silver–Gold architecture.

### Architecture Overview

```text
             GTFS Data Source
                    |
                    v
          Local Cloud Ingestion
          Storage + Message Queue
                    |
                    v
             BRONZE LAYER
             Raw GTFS Files
                    |
                    v
             SILVER LAYER
          Cleaned Parquet Data
                    |
                    v
              GOLD LAYER
          DuckDB / SQL Analytics
                    |
             +------+------+
             |             |
             v             v
         PostgreSQL     Streamlit
          Database      Dashboard
```

### 5.1 Bronze Layer

**Location:** `data/bronze/`

The Bronze layer contains extracted GTFS source files.

The ingestion process checks the required files before extracting the archive.

### 5.2 Silver Layer

**Location:** `data/silver/`

The Silver layer contains cleaned and validated Parquet datasets.

Processing includes:

- Required-column validation
- Identifier validation
- Duplicate detection
- Coordinate validation
- Calendar processing
- Referential integrity checks
- Parquet conversion

#### Verified Silver Data

| Dataset | Records |
|---|---:|
| Stops | 42,421 |
| Routes | 1,287 |
| Trips | 261,282 |
| Stop Times | 5,785,831 |
| Calendar | 4,485 |
| Calendar Dates | 205,448 |

### 5.3 Gold Layer

**Location:** `data/gold/`

The Gold layer contains analytical datasets generated using DuckDB and SQL.

| Dataset | Analysis | Records |
|---|---|---:|
| `top_stops.parquet` | Stops ranked by scheduled stop events | 20 |
| `top_routes.parquet` | Routes ranked by scheduled trips | 20 |
| `stop_connectivity.parquet` | Stops ranked by distinct serving routes | 20 |
| `service_by_weekday.parquet` | Scheduled service analysis by weekday | 7 |

SQL queries are stored in the `sql/` directory.

**Note:** These results represent scheduled transport services, not passenger counts, actual vehicle movements, or real-time delays.

---

## 6. Local Cloud and Event-Driven Ingestion

The platform includes a local cloud simulation to demonstrate object storage and event-driven processing.

### Local Object Storage

The `LocalStorage` implementation provides upload and download operations.

Objects are stored under:

`data/cloud_storage/`

The implementation includes object-key validation and path safety checks.

### Local Message Queue

The `LocalMessageQueue` implementation supports:

- Message publishing
- Message receiving
- Message acknowledgement
- Retry handling
- Processing-attempt tracking
- Dead-letter queue behavior

The queue operates in Python memory and is not persistent across process restarts.

### Ingestion Workflow

The workflow:

1. Stages the GTFS archive in local object storage.
2. Publishes a `gtfs_staged` event.
3. Receives the event.
4. Downloads the staged archive.
5. Verifies file size and SHA-256 checksum.
6. Replaces the input archive after successful verification.
7. Acknowledges the processed message.

**Implementation:** `src/cloud/run_gtfs_ingestion.py`

These are local simulations, not actual AWS S3 or SQS services.

---

## 7. Apache Airflow Orchestration

Apache Airflow coordinates the data processing pipeline.

**DAG ID:** `german_transport_pipeline`

**DAG file:** `airflow/dags/transport_pipeline.py`

**Execution mode:** Manual (`schedule=None`)

### Pipeline Tasks

| Step | Task | Responsibility |
|---:|---|---|
| 1 | `cloud_ingestion` | Local cloud-style ingestion |
| 2 | `ingest_gtfs` | Extract and validate GTFS archive |
| 3 | `create_manifest` | Generate metadata and SHA-256 |
| 4 | `clean_stops` | Clean stop records |
| 5 | `clean_routes` | Clean route records |
| 6 | `clean_trips` | Clean trip records |
| 7 | `clean_stop_times` | Clean timetable events |
| 8 | `clean_calendar` | Process service calendars |
| 9 | `check_relationships` | Validate data relationships |
| 10 | `build_gold` | Generate analytical datasets |
| 11 | `generate_quality_report` | Generate quality report |
| 12 | `run_quality_tests` | Execute automated tests |

### Execution Status

A previous full pipeline execution completed all 12 tasks successfully.

After recreating the Airflow container, all 12 task definitions were successfully rediscovered.

A new complete execution after the container recreation has not yet been verified.

**Current limitation:** PostgreSQL loading is not yet integrated into the Airflow DAG. The database loading scripts currently run separately.

---

## 8. PostgreSQL Analytics Database

The project includes a local PostgreSQL 16 database running in Docker.

**Database:** `transport_analytics`

**Database user:** `transport_user`

**Docker container:** `german_transport_postgres`

PostgreSQL stores analytical datasets generated by the Gold layer.

### PostgreSQL Tables

| Table | Primary Key | Verified Records |
|---|---|---:|
| `top_stops` | `stop_id` | 20 |
| `top_routes` | `route_id` | 20 |
| `stop_connectivity` | `stop_id` | 20 |
| `service_by_weekday` | `weekday_number` | 7 |
| **Total** | | **67** |

### Python Loading Scripts

The project currently includes four database loading scripts:

```text
src/load_gold_to_postgres.py
src/load_top_routes_to_postgres.py
src/load_stop_connectivity_to_postgres.py
src/load_service_by_weekday_to_postgres.py
```

These scripts use Psycopg to connect Python to PostgreSQL.

They validate the source datasets and use:

`INSERT ... ON CONFLICT DO UPDATE`

This allows existing records to be updated without creating duplicate primary-key entries.

### PostgreSQL Setup

Create a local file:

`docker/postgres/.env`

Add:

```dotenv
POSTGRES_PASSWORD=your_own_strong_password
```

Never commit this file to GitHub.

Start PostgreSQL:

```bash
docker compose -f docker/postgres/docker-compose.yml up -d
```

Check database availability:

```bash
docker exec german_transport_postgres pg_isready -U transport_user -d transport_analytics
```

### Database Initialization

The four PostgreSQL tables have been created and tested locally.

**Current limitation:** Table creation has been performed manually. A version-controlled database initialization script has not yet been added.

On a new machine, the tables must be created before running the loading scripts.

### Load Gold Data into PostgreSQL

After generating the Gold datasets and creating the tables, run:

```bash
python src/load_gold_to_postgres.py
python src/load_top_routes_to_postgres.py
python src/load_stop_connectivity_to_postgres.py
python src/load_service_by_weekday_to_postgres.py
```

The first loader supports environment-based database connection settings. The other three currently use local connection defaults.

### Verify PostgreSQL Data

```bash
docker exec german_transport_postgres psql -U transport_user -d transport_analytics -c "SELECT 'top_stops' AS table_name, COUNT(*) AS total_rows FROM top_stops UNION ALL SELECT 'top_routes', COUNT(*) FROM top_routes UNION ALL SELECT 'stop_connectivity', COUNT(*) FROM stop_connectivity UNION ALL SELECT 'service_by_weekday', COUNT(*) FROM service_by_weekday;"
```

Expected table counts:

```text
top_stops           20
top_routes          20
stop_connectivity   20
service_by_weekday   7
```

### Docker Networking

Airflow and PostgreSQL communicate through a shared Docker network.

The Airflow Compose configuration references the external network:

`postgres_default`

PostgreSQL must be started before Airflow so this network exists.

The Psycopg dependency is included in the Airflow container's startup configuration.

**Important:** PostgreSQL is running locally in Docker. It is not an actual AWS RDS deployment.

---

## 9. Data Quality and Validation

The project generates a structured data quality report.

**Script:** `src/generate_quality_report.py`

**Output:** `data/metadata/quality_report.json`

The report includes:

- Dataset row counts
- Dataset column counts
- Missing key-value checks
- Duplicate identifier checks
- Referential integrity checks
- Overall validation status
- Reported issues

### Latest Verified Quality Results

| Quality Check | Result |
|---|---:|
| Datasets checked | 10 |
| Duplicate stop IDs | 0 |
| Duplicate route IDs | 0 |
| Duplicate trip IDs | 0 |
| Unknown trip references | 0 |
| Unknown stop references | 0 |
| Reported issues | 0 |
| Overall status | **PASS** |

All configured quality checks passed for the tested dataset.

This does not mean that every possible data quality issue has been tested.

---

## 10. Dataset Metadata and Integrity

The project generates a metadata manifest for the GTFS archive.

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

Unverified source information is recorded as null.

The manifest provides basic source-file traceability and integrity metadata.

It is not a complete column-level lineage system.

---

## 11. Interactive Analytics Dashboard

The platform includes an interactive dashboard built with Streamlit and Plotly.

**Application:** `dashboard/app.py`

### Dashboard Features

**Overview**

Displays key metrics including:

- Total stops
- Total routes
- Total scheduled trips
- Total stop-time records
- Data quality status

**Top Stops**

Displays stops ranked by scheduled stop events.

**Top Routes**

Displays routes ranked by scheduled trips.

**Stop Connectivity**

Displays stops with the highest number of distinct serving routes.

**Weekly Service Patterns**

Displays average scheduled trips per active service date for each weekday.

**Data Quality**

Displays validation status, reported issues, and the quality report.

### Interactive Features

- Sidebar filters
- Interactive Plotly charts
- Hover information
- Expandable data tables
- Data quality indicators

### Run the Dashboard

From the project root:

```bash
python -m streamlit run dashboard/app.py
```

Open:

http://localhost:8501

The dashboard reads Gold Parquet files and the quality report.

It does not currently query PostgreSQL directly.

---

## 12. Testing and Continuous Integration

The project uses Pytest for automated validation.

Tests cover:

- GTFS ingestion and transformations
- Required fields and identifiers
- Calendar processing
- Data relationships
- Gold-layer analytics
- Local object storage
- Event publishing and consumption
- Queue acknowledgement and retries
- Dead-letter queue behavior
- Archive integrity verification
- Metadata generation
- Data quality reporting

### Verified Test Results

| Environment | Result |
|---|---|
| Local Windows environment | 90 tests passed |
| GitHub Actions | 58 tests passed |
| Previous full Airflow execution | 12 of 12 tasks successful |

The dashboard and 12-task Airflow changes were previously committed and pushed to GitHub.

**Commit:** `b15084f`

The newer PostgreSQL changes have not yet been verified by GitHub Actions.

### Run Local Tests

```bash
python -m pytest tests/ -q
```

GitHub Actions runs dataset-independent tests because the large GTFS and Parquet files are not committed to the repository.

The full dataset-dependent test suite runs locally after the required datasets are generated.

---

## 13. Running the Project

### Prerequisites

- Python 3.10 or a compatible version
- Git
- Docker and Docker Compose
- Access to a compatible VBB GTFS archive
- Available ports 8080, 8501, and 5432

The project is intended to support Windows, Linux, and macOS.

Some setup steps are still being improved for fully reproducible execution on a new machine.

### Step 1 — Clone the Repository

```bash
git clone https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform.git
cd German-Public-Transport-Data-Engineering-Platform
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
python -m pip install -r requirements.txt
```

The PostgreSQL loading scripts also require:

```bash
python -m pip install "psycopg[binary]"
```

This dependency is being added to the project requirements as part of the PostgreSQL integration update.

### Step 4 — Prepare GTFS Data

Download a compatible GTFS archive from VBB.

Place it at:

`data/raw/gtfs.zip`

The archive is not included in the GitHub repository.

### Step 5 — Start PostgreSQL

Create:

`docker/postgres/.env`

Add a strong password:

```dotenv
POSTGRES_PASSWORD=your_own_strong_password
```

Then start PostgreSQL:

```bash
docker compose -f docker/postgres/docker-compose.yml up -d
```

### Step 6 — Start Airflow

```bash
docker compose -f airflow/docker-compose.yml up -d
```

Open:

http://localhost:8080

### Step 7 — Execute the Pipeline

In the Airflow interface:

1. Find `german_transport_pipeline`.
2. Enable the DAG if necessary.
3. Trigger a manual run.
4. Monitor all 12 tasks.
5. Confirm successful completion.

### Step 8 — Inspect the Results

Generated datasets are stored in:

```text
data/bronze/
data/silver/
data/gold/
data/metadata/
```

The Gold layer should contain:

```text
top_stops.parquet
top_routes.parquet
stop_connectivity.parquet
service_by_weekday.parquet
```

### Step 9 — Load PostgreSQL

After manually creating the four database tables, run the loading scripts listed in Section 8.

Database schema initialization and automated loading through Airflow are still being developed.

### Step 10 — Start the Dashboard

```bash
python -m streamlit run dashboard/app.py
```

Open:

http://localhost:8501

### Step 11 — Run Tests

```bash
python -m pytest tests/ -q
```

---

## 14. Project Structure

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
|-- docker/
|   `-- postgres/
|       |-- docker-compose.yml
|       `-- .env
|
|-- docs/
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
|   |-- generate_quality_report.py
|   |-- load_gold_to_postgres.py
|   |-- load_top_routes_to_postgres.py
|   |-- load_stop_connectivity_to_postgres.py
|   `-- load_service_by_weekday_to_postgres.py
|
|-- tests/
|
|-- .gitignore
|-- requirements.txt
`-- README.md
```

The `data/` directory contains local datasets and generated outputs that are excluded from Git.

The `.env` file contains local database credentials and must never be committed.

---

## 15. Current Scope and Limitations

The platform currently provides:

- Regional GTFS ingestion
- Bronze, Silver, and Gold data processing
- SQL analytics
- Data quality monitoring
- Local cloud-style ingestion
- Twelve-task Airflow orchestration
- Interactive Streamlit dashboard
- Four PostgreSQL analytical tables
- Automated testing and GitHub Actions

### Current Limitations

**Geographic coverage:** The current dataset covers Berlin–Brandenburg, not all of Germany.

**Cloud services:** AWS S3, SQS, EC2, RDS, IAM, and Lambda are not deployed.

**Local message queue:** Messages are stored in memory and do not survive process restarts.

**Airflow scheduling:** The DAG is manually triggered.

**PostgreSQL integration:** The Gold datasets have been loaded successfully, but loading is not yet automated through Airflow.

**Database initialization:** PostgreSQL table creation is not yet automated.

**Reproducibility:** Fresh-machine installation and cross-platform execution still require additional validation.

**Real-time analytics:** The project does not currently process live vehicle locations, real-time delays, or passenger counts.

---

## 16. Next Development Steps

The remaining priorities are:

1. Complete PostgreSQL and Airflow integration.
2. Automate PostgreSQL table initialization.
3. Add database loading tasks to the Airflow pipeline.
4. Verify a complete end-to-end pipeline execution.
5. Improve cross-platform Docker setup.
6. Complete final testing and documentation.
7. Publish the verified updates to GitHub.

Potential future improvements include:

- Actual AWS integration
- Persistent message processing
- Scheduled GTFS ingestion
- Additional German regional GTFS feeds
- Improved monitoring and alerting
- Further dashboard enhancements

These are future improvements and are not presented as completed features.

---

## 17. Conclusion

The German Public Transport Data Engineering Platform demonstrates a practical end-to-end data engineering workflow.

The implementation combines:

- Data ingestion
- Layered data processing
- SQL analytics
- Workflow orchestration
- PostgreSQL storage
- Data validation
- Metadata and integrity tracking
- Interactive visualization
- Automated testing
- Continuous integration

The project provides a foundation for further development toward production-oriented and cloud-based data engineering systems.

---

**Author:** Eman Nazari  
**Project:** German Public Transport Data Engineering Platform  
**Repository:** https://github.com/emannazari777-ops/German-Public-Transport-Data-Engineering-Platform
