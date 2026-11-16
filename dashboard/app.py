
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
QUALITY_REPORT_PATH = (
    PROJECT_ROOT / "data" / "metadata" / "quality_report.json"
)


st.set_page_config(
    page_title="German Public Transport | Analytics",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_gold_dataset(filename):
    """Read a Gold-layer Parquet dataset."""
    file_path = GOLD_DIR / filename

    if not file_path.is_file():
        raise FileNotFoundError(f"Missing dataset: {file_path}")

    return pd.read_parquet(file_path)


@st.cache_data
def load_quality_report():
    """Read the latest data quality report."""
    if not QUALITY_REPORT_PATH.is_file():
        return None

    with QUALITY_REPORT_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def horizontal_chart(data, value_column, label_column, title):
    """Create an interactive horizontal bar chart."""
    chart_data = data.sort_values(value_column, ascending=True)

    figure = px.bar(
        chart_data,
        x=value_column,
        y=label_column,
        orientation="h",
        title=title,
        hover_data={value_column: ":,"},
        labels={
            value_column: "Scheduled Count",
            label_column: "",
        },
    )

    figure.update_layout(
        height=max(450, len(chart_data) * 34),
        margin=dict(l=20, r=30, t=65, b=30),
        yaxis_title=None,
        xaxis_title="Count",
    )

    return figure


# --------------------------------------------------
# Load data
# --------------------------------------------------

try:
    top_stops = load_gold_dataset("top_stops.parquet")
    top_routes = load_gold_dataset("top_routes.parquet")
    connectivity = load_gold_dataset("stop_connectivity.parquet")
    weekday_service = load_gold_dataset("service_by_weekday.parquet")

except (FileNotFoundError, OSError, ValueError) as error:
    st.error(f"Unable to load Gold data: {error}")
    st.info("Run the Airflow pipeline to generate Gold datasets.")
    st.stop()

quality_report = load_quality_report()


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.title("🚆 Transport Analytics")

st.sidebar.caption(
    "VBB Berlin–Brandenburg GTFS"
)

st.sidebar.divider()
st.sidebar.subheader("Chart Filters")

stop_limit = st.sidebar.slider(
    "Top Stops",
    min_value=5,
    max_value=min(20, len(top_stops)),
    value=min(10, len(top_stops)),
)

route_limit = st.sidebar.slider(
    "Top Routes",
    min_value=5,
    max_value=min(20, len(top_routes)),
    value=min(10, len(top_routes)),
)

connectivity_limit = st.sidebar.slider(
    "Connected Stops",
    min_value=5,
    max_value=min(20, len(connectivity)),
    value=min(10, len(connectivity)),
)

st.sidebar.divider()

st.sidebar.info(
    "This dashboard shows scheduled transport activity, "
    "not actual passenger numbers or real-time delays."
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("🚆 German Public Transport")
st.subheader("Data Engineering Analytics Platform")

st.caption(
    "Region: Berlin–Brandenburg | "
    "Source: VBB GTFS | "
    "Processing: Python, DuckDB, Parquet and Airflow"
)


# --------------------------------------------------
# Overview
# --------------------------------------------------

st.divider()
st.header("Overview")

if quality_report is not None:
    quality_status = quality_report.get(
        "overall_status",
        "UNKNOWN",
    )

    if quality_status == "PASS":
        st.success(
            "Data Quality: PASS — "
            "All configured checks passed."
        )
    else:
        st.warning(f"Data Quality: {quality_status}")
else:
    st.warning("Data quality report is unavailable.")


metrics = (
    quality_report.get("dataset_metrics", {})
    if quality_report is not None
    else {}
)

stops_count = metrics.get("stops", {}).get("row_count", 0)
routes_count = metrics.get("routes", {}).get("row_count", 0)
trips_count = metrics.get("trips", {}).get("row_count", 0)
events_count = metrics.get("stop_times", {}).get("row_count", 0)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Stops", f"{stops_count:,}")
col2.metric("Routes", f"{routes_count:,}")
col3.metric("Scheduled Trips", f"{trips_count:,}")
col4.metric("Stop-Time Records", f"{events_count:,}")


# --------------------------------------------------
# Top stops
# --------------------------------------------------

st.divider()
st.header("Top Stops")

stop_data = top_stops.head(stop_limit).copy()

stop_data["label"] = (
    stop_data["stop_name"].fillna("Unknown").astype(str)
    + " | "
    + stop_data["stop_id"].astype(str)
)

figure = horizontal_chart(
    stop_data,
    "scheduled_stop_count",
    "label",
    "Top Stops by Scheduled Stop Events",
)

st.plotly_chart(figure, width="stretch")

with st.expander("View Top Stops Data"):
    st.dataframe(
        top_stops,
        width="stretch",
        hide_index=True,
    )


# --------------------------------------------------
# Top routes
# --------------------------------------------------

st.divider()
st.header("Top Routes")

route_data = top_routes.head(route_limit).copy()

route_data["label"] = (
    route_data["route_short_name"]
    .fillna("Unknown")
    .astype(str)
    + " | "
    + route_data["route_id"].astype(str)
)

figure = horizontal_chart(
    route_data,
    "scheduled_trip_count",
    "label",
    "Top Routes by Scheduled Trips",
)

st.plotly_chart(figure, width="stretch")

with st.expander("View Top Routes Data"):
    st.dataframe(
        top_routes,
        width="stretch",
        hide_index=True,
    )


# --------------------------------------------------
# Connectivity
# --------------------------------------------------

st.divider()
st.header("Stop Connectivity")

connectivity_data = connectivity.head(
    connectivity_limit
).copy()

connectivity_data["label"] = (
    connectivity_data["stop_name"].fillna("Unknown").astype(str)
    + " | "
    + connectivity_data["stop_id"].astype(str)
)

figure = horizontal_chart(
    connectivity_data,
    "distinct_route_count",
    "label",
    "Stops with the Most Distinct Routes",
)

st.plotly_chart(figure, width="stretch")

with st.expander("View Connectivity Data"):
    st.dataframe(
        connectivity,
        width="stretch",
        hide_index=True,
    )


# --------------------------------------------------
# Weekday service
# --------------------------------------------------

st.divider()
st.header("Weekly Service Patterns")

weekday_data = weekday_service.sort_values(
    "weekday_number"
).copy()

figure = px.bar(
    weekday_data,
    x="weekday_name",
    y="average_trips_per_active_date",
    title="Average Scheduled Trips per Active Service Date",
    labels={
        "weekday_name": "Weekday",
        "average_trips_per_active_date": "Average Trips",
    },
)

figure.update_layout(
    height=460,
    margin=dict(l=20, r=20, t=65, b=30),
)

st.plotly_chart(figure, width="stretch")

with st.expander("View Weekday Service Data"):
    st.dataframe(
        weekday_service,
        width="stretch",
        hide_index=True,
    )


# --------------------------------------------------
# Data quality
# --------------------------------------------------

st.divider()
st.header("Data Quality & Validation")

if quality_report is None:
    st.warning("Quality report not found.")
else:
    status = quality_report.get("overall_status", "UNKNOWN")
    issues = quality_report.get("issues", [])

    quality_col1, quality_col2 = st.columns(2)

    quality_col1.metric("Quality Status", status)
    quality_col2.metric("Reported Issues", len(issues))

    with st.expander("View Full Quality Report"):
        st.json(quality_report)


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "German Public Transport Data Engineering Platform | "
    "VBB Berlin–Brandenburg GTFS | "
    "Local analytics environment"
)
