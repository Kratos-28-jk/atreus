import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DEFAULT_DB_PATH = 'pac3200_readings.db'
REFRESH_INTERVAL_SEC = 60  # auto-refresh interval

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def get_connection(db_path: str):
    """Return a SQLite connection (read-only)."""
    # Opening in read-only mode prevents accidental writes from the dashboard
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


def load_latest_records(db_path: str, limit: int = 20) -> pd.DataFrame:
    """Load the latest *limit* records from the readings table."""
    query = (
        "SELECT * FROM pac3200_readings ORDER BY timestamp DESC LIMIT ?"
    )
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=[limit])
    return df


def load_time_range(db_path: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Load all records between *start* and *end* timestamps."""
    query = (
        "SELECT * FROM pac3200_readings WHERE timestamp BETWEEN ? AND ?"
        " ORDER BY timestamp ASC"
    )
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=[start, end])
    return df


def load_parameter_definitions(db_path: str) -> pd.DataFrame:
    """Return parameter definitions table as DataFrame."""
    query = (
        "SELECT parameter_name AS parameter, register_address AS register, unit, description "
        "FROM parameter_definitions ORDER BY register"
    )
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn)
    return df


# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="PAC3200 Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚡ SENTRON PAC3200 – Real-time Dashboard")

# Sidebar ---------------------------------------------------------------------

st.sidebar.header("Settings")

db_path = st.sidebar.text_input("Database path", value=DEFAULT_DB_PATH)

refresh_interval = st.sidebar.number_input(
    "Auto-refresh interval (seconds)",
    min_value=5,
    max_value=300,
    value=REFRESH_INTERVAL_SEC,
    step=5,
)

page = st.sidebar.radio("Select view", ["Overview", "Trend Charts", "Parameter Definitions"])

# Auto-refresh mechanism
st.experimental_set_query_params(_time=int(datetime.utcnow().timestamp()))

# Overview --------------------------------------------------------------------

if page == "Overview":
    st.subheader("Latest Measurements")

    df_latest = load_latest_records(db_path, limit=1)
    if df_latest.empty:
        st.warning("No data found in the database.")
    else:
        row = df_latest.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("V1-N Voltage (V)", f"{row['V1_N_Voltage']:.2f}")
        col2.metric("V2-N Voltage (V)", f"{row['V2_N_Voltage']:.2f}")
        col3.metric("V3-N Voltage (V)", f"{row['V3_N_Voltage']:.2f}")
        col4.metric("Frequency (Hz)", f"{row['Frequency']:.2f}")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("L1 Current (A)", f"{row['L1_Current']:.2f}")
        col6.metric("L2 Current (A)", f"{row['L2_Current']:.2f}")
        col7.metric("L3 Current (A)", f"{row['L3_Current']:.2f}")
        col8.metric("Total Active Power (W)", f"{row['Total_Active_Power']:.2f}")

        st.write("### Raw record")
        st.dataframe(df_latest)

# Trend Charts ----------------------------------------------------------------

elif page == "Trend Charts":
    st.subheader("Historical Trends")

    # Time range selection
    col_a, col_b = st.columns(2)

    with col_a:
        hours_back = st.number_input(
            "Show data from the last N hours", min_value=1, max_value=168, value=24
        )
    with col_b:
        limit_records = st.number_input(
            "Maximum records to fetch", min_value=100, max_value=10000, value=2000, step=100
        )

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_back)

    data = load_time_range(db_path, start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'))

    if data.empty:
        st.warning("No data for selected period.")
    else:
        st.success(f"Loaded {len(data)} records from database")

        # Parameter selection
        numeric_cols = [c for c in data.columns if c not in ('id', 'timestamp')]
        selection = st.multiselect(
            "Parameters to plot", options=numeric_cols, default=["V1_N_Voltage", "V2_N_Voltage", "V3_N_Voltage"]
        )

        if selection:
            melted = data.melt(id_vars=['timestamp'], value_vars=selection, var_name='parameter', value_name='value')
            fig = px.line(
                melted,
                x='timestamp',
                y='value',
                color='parameter',
                title='Parameter Trend',
            )
            fig.update_layout(xaxis_title='Time', yaxis_title='Value')
            st.plotly_chart(fig, use_container_width=True)

        st.write("### Raw data table")
        st.dataframe(data.tail(limit_records))

# Parameter Definitions --------------------------------------------------------

elif page == "Parameter Definitions":
    st.subheader("Modbus Register Map & Descriptions")
    defs = load_parameter_definitions(db_path)
    st.dataframe(defs)

# Footer ----------------------------------------------------------------------

st.caption("Dashboard refreshes automatically every few seconds. Made with Streamlit © 2025")