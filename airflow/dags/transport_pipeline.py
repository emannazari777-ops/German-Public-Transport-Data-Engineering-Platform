
from datetime import datetime
from pathlib import Path
import subprocess

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator


PROJECT_DIR = Path("/opt/airflow/project")


def run_script(script_name):
    """Run a project script and fail the task if execution fails."""

    script_path = PROJECT_DIR / "src" / script_name

    subprocess.run(
        ["python", str(script_path)],
        cwd=PROJECT_DIR,
        check=True,
    )


def run_cloud_ingestion():
    """Stage and retrieve GTFS data through the local cloud workflow."""

    subprocess.run(
        ["python", "-m", "src.cloud.run_gtfs_ingestion"],
        cwd=PROJECT_DIR,
        check=True,
    )


def run_tests():
    """Run the project quality checks."""

    subprocess.run(
        ["python", "-m", "pytest", "tests/", "-q"],
        cwd=PROJECT_DIR,
        check=True,
    )


with DAG(
    dag_id="german_transport_pipeline",
    description="German public transport data engineering pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["transport", "gtfs", "data-engineering"],
) as dag:

    cloud_ingestion = PythonOperator(
        task_id="cloud_ingestion",
        python_callable=run_cloud_ingestion,
    )

    ingest = PythonOperator(
        task_id="ingest_gtfs",
        python_callable=run_script,
        op_args=["ingest_gtfs.py"],
    )

    manifest = PythonOperator(
        task_id="create_manifest",
        python_callable=run_script,
        op_args=["create_manifest.py"],
    )

    clean_stops = PythonOperator(
        task_id="clean_stops",
        python_callable=run_script,
        op_args=["clean_stops.py"],
    )

    clean_routes = PythonOperator(
        task_id="clean_routes",
        python_callable=run_script,
        op_args=["clean_routes.py"],
    )

    clean_trips = PythonOperator(
        task_id="clean_trips",
        python_callable=run_script,
        op_args=["clean_trips.py"],
    )

    clean_stop_times = PythonOperator(
        task_id="clean_stop_times",
        python_callable=run_script,
        op_args=["clean_stop_times.py"],
    )

    clean_calendar = PythonOperator(
        task_id="clean_calendar",
        python_callable=run_script,
        op_args=["clean_calendar.py"],
    )

    check_relationships = PythonOperator(
        task_id="check_relationships",
        python_callable=run_script,
        op_args=["check_relationships.py"],
    )

    gold = PythonOperator(
        task_id="build_gold",
        python_callable=run_script,
        op_args=["run_gold.py"],
    )

    quality_report = PythonOperator(
        task_id="generate_quality_report",
        python_callable=run_script,
        op_args=["generate_quality_report.py"],
    )

    tests = PythonOperator(
        task_id="run_quality_tests",
        python_callable=run_tests,
    )

    (
        cloud_ingestion
        >> ingest
        >> manifest
        >> clean_stops
        >> clean_routes
        >> clean_trips
        >> clean_stop_times
        >> clean_calendar
        >> check_relationships
        >> gold
        >> quality_report
        >> tests
    )
