import pandas as pd
import requests
import duckdb
import pyarrow
import pytest


def check_environment():
    packages = {
        "pandas": pd.__version__,
        "requests": requests.__version__,
        "duckdb": duckdb.__version__,
        "pyarrow": pyarrow.__version__,
        "pytest": pytest.__version__,
    }

    print("German Public Transport Data Engineering Platform")
    print("Environment check")
    print("-" * 45)

    for package, version in packages.items():
        print(f"{package}: {version}")

    print("-" * 45)
    print("All required Python packages are available.")


if __name__ == "__main__":
    check_environment()