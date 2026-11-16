
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"

ANALYSES = {
    "top_stops": "top_stops.sql",
    "top_routes": "top_routes.sql",
    "stop_connectivity": "stop_connectivity.sql",
    "service_by_weekday": "service_by_weekday.sql",
}


def run_gold():
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    for analysis_name, sql_filename in ANALYSES.items():
        sql_file = SQL_DIR / sql_filename

        if not sql_file.is_file():
            raise FileNotFoundError(f"SQL file not found: {sql_file}")

        query = sql_file.read_text(encoding="utf-8")

        with duckdb.connect() as connection:
            result = connection.execute(query).df()

        if result.empty:
            raise ValueError(f"No results for {analysis_name}")

        destination = GOLD_DIR / f"{analysis_name}.parquet"
        temporary_file = GOLD_DIR / f"{analysis_name}.tmp.parquet"

        try:
            result.to_parquet(
                temporary_file,
                index=False,
                compression="zstd",
            )
            temporary_file.replace(destination)
        finally:
            temporary_file.unlink(missing_ok=True)

        print(f"\nGold Analysis: {analysis_name}")
        print("-" * 65)
        print(result.to_string(index=False))
        print(f"Total rows: {len(result)}")
        print(f"Saved to: {destination}")


if __name__ == "__main__":
    run_gold()
