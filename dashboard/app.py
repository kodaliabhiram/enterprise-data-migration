
from pathlib import Path
import sys
import tempfile
import uuid
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validation.data_quality import analyze_transactions
from src.validation.migration_audit import read_migration_history
from src.ml.anomaly_detector import detect_anomalies
from src.transformation.migration import migrate_transactions


DATA_FILE = PROJECT_ROOT / "data" / "sample" / "transactions.csv"

st.set_page_config(
    page_title="Enterprise Data Quality Monitor",
    page_icon="📊",
    layout="wide",
)

st.title("Enterprise Data Migration & Intelligent Data Quality Monitoring")
st.caption(
    "Interactive demonstration of migration validation, "
    "data quality checks, and machine-learning anomaly detection."
)


@st.cache_data
def load_transactions():
    """Load the sample dataset."""
    return pd.read_csv(DATA_FILE)



st.subheader("Choose your dataset")

uploaded_file = st.file_uploader(
    "Upload a transaction CSV",
    type=["csv"],
    help=(
        "CSV must contain transaction_id, customer_id, "
        "amount, transaction_date, and payment_method."
    ),
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        required_columns = {
            "transaction_id",
            "customer_id",
            "amount",
            "transaction_date",
            "payment_method",
        }

        missing_columns = sorted(required_columns - set(df.columns))

        if missing_columns:
            st.error(
                f"CSV is missing required columns: {missing_columns}"
            )
            st.stop()

        st.success(
            f"Uploaded {len(df)} transaction records successfully."
        )

    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(f"Could not read the uploaded CSV: {exc}")
        st.stop()
else:
    df = load_transactions()
    st.info("Using the built-in sample dataset (10 demo records).")



# Store the latest migration result for this browser session.
if "migration_result" not in st.session_state:
    st.session_state["migration_result"] = None

st.subheader("Run data migration")
st.write(
    "Migrate the currently selected dataset and record the result."
)

if st.button("Run Migration", type="primary"):
    try:
        run_id = uuid.uuid4().hex

        if uploaded_file is not None:
            uploads_dir = PROJECT_ROOT / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)

            original_stem = Path(uploaded_file.name).stem
            safe_stem = "".join(
                char if char.isalnum() or char in "-_" else "_"
                for char in original_stem
            )[:60] or "uploaded_transactions"

            source_file = uploads_dir / f"{safe_stem}_{run_id}.csv"
            source_file.write_bytes(uploaded_file.getvalue())
        else:
            source_file = DATA_FILE

        target_dir = PROJECT_ROOT / "data" / "migrated"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"transactions_{run_id}.csv"

        migration_result = migrate_transactions(
            source_path=source_file,
            target_path=target_file,
        )

        st.session_state["migration_result"] = migration_result
        st.success("Migration completed and audit result recorded.")

    except Exception as exc:
        st.session_state["migration_result"] = None
        st.error(f"Migration failed: {exc}")

migration = st.session_state["migration_result"]


st.divider()

# Data quality checks use the current sample dataset.
quality = analyze_transactions(df)

# Run anomaly detection using temporary files.
with tempfile.TemporaryDirectory() as temp_dir:
    temp_dir = Path(temp_dir)
    input_file = temp_dir / "transactions.csv"
    model_file = temp_dir / "model.joblib"
    result_file = temp_dir / "anomaly_results.csv"

    df.to_csv(input_file, index=False)

    anomalies = detect_anomalies(
        input_path=input_file,
        model_path=model_file,
        result_path=result_file,
    )

# Dataset overview
st.subheader("Dataset overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total transactions", quality["total_records"])
c2.metric("Missing amounts", quality["missing_amounts"])
c3.metric("Duplicate ID records", quality["duplicate_id_records"])
c4.metric(
    "Anomalies detected",
    int(anomalies["anomaly_label"].eq("anomaly").sum()),
)

st.divider()

# Migration reconciliation
st.subheader("Data migration reconciliation")

if migration is None:
    st.info("Click **Run Migration** to start a migration.")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Source records", migration["source_records"])
    m2.metric("Migrated records", migration["target_records"])
    m3.metric(
        "Records reconciled",
        "YES" if migration["records_reconciled"] else "NO",
    )

    if (
        migration["status"] == "SUCCESS"
        and migration["records_reconciled"]
    ):
        st.success(
            "Migration successful — source and target record counts match."
        )
    else:
        st.error(
            "Migration reconciliation failed. Check the migration report."
        )

st.divider()

# Transaction amounts and data quality charts
left, right = st.columns(2)

with left:
    st.subheader("Transaction amounts")

    chart_df = df.copy()
    chart_df["amount"] = pd.to_numeric(
        chart_df["amount"], errors="coerce"
    )
    chart_df = chart_df.dropna(subset=["amount"])

    fig = px.bar(
        chart_df,
        x="transaction_id",
        y="amount",
        title="Amount by transaction",
        labels={
            "transaction_id": "Transaction ID",
            "amount": "Transaction amount",
        },
    )
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Data quality summary")

    summary_keys = [
        ("Missing amounts", "missing_amounts"),
        ("Duplicate ID records", "duplicate_id_records"),
        ("Invalid dates", "invalid_dates"),
        ("Non-positive amounts", "non_positive_amounts"),
        ("Unknown customers", "unknown_customers"),
        ("High-value transactions", "high_value_transactions"),
    ]

    summary_df = pd.DataFrame(
        [
            {"Issue": label, "Affected records": quality[key]}
            for label, key in summary_keys
        ]
    )

    fig = px.bar(
        summary_df,
        x="Issue",
        y="Affected records",
        title="Records flagged by each quality check",
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, width="stretch")

st.divider()

# Detailed quality findings
st.subheader("Detailed quality findings")

findings_df = pd.DataFrame(quality["findings"])

if findings_df.empty:
    st.success("No data quality issues found.")
else:
    issue_types = sorted(
        findings_df["issue_type"].unique().tolist()
    )

    selected_issues = st.multiselect(
        "Filter by issue type",
        options=issue_types,
        default=issue_types,
    )

    st.dataframe(
        findings_df[
            findings_df["issue_type"].isin(selected_issues)
        ],
        width="stretch",
        hide_index=True,
    )

st.divider()

# Machine-learning anomaly results
st.subheader("Machine-learning anomaly results")

st.warning(
    "This model uses a small synthetic dataset. Its flags are exploratory "
    "and should not be interpreted as proof of fraud."
)

labels = sorted(
    anomalies["anomaly_label"].dropna().unique().tolist()
)

selected_labels = st.multiselect(
    "Filter by model label",
    options=labels,
    default=labels,
)

st.dataframe(
    anomalies[
        anomalies["anomaly_label"].isin(selected_labels)
    ],
    width="stretch",
    hide_index=True,
)

with st.expander("View original demo transactions"):
    st.dataframe(df, width="stretch", hide_index=True)

st.divider()

# Migration audit history
st.subheader("Migration audit history")

audit_history = read_migration_history()

if audit_history.empty:
    st.info(
        "No migration history recorded yet. "
        "Click Run Migration to create the first audit entry."
    )
else:
    total_runs = len(audit_history)
    latest_run = audit_history.iloc[-1]

    a1, a2, a3 = st.columns(3)
    a1.metric("Total migration runs", total_runs)
    a2.metric("Latest run status", latest_run["status"])

    reconciled_value = latest_run["records_reconciled"]
    is_reconciled = (
        str(reconciled_value).strip().lower() == "true"
    )

    a3.metric(
        "Latest reconciliation",
        "YES" if is_reconciled else "NO",
    )

    st.dataframe(
        audit_history.sort_values(
            "run_timestamp_utc",
            ascending=False,
        ),
        width="stretch",
        hide_index=True,
    )

st.caption(
    "Demo data only. PostgreSQL ingestion and migration validation "
    "are demonstrated separately by the local pipeline."
)
