
from pathlib import Path
import sys
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validation.data_quality import analyze_transactions
from src.ml.anomaly_detector import detect_anomalies

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
    return pd.read_csv(DATA_FILE)

df = load_transactions()

# Run the existing data quality checks.
quality = analyze_transactions(df)

# Use a temporary CSV because the current ML function accepts a file path.
# Temporary output files avoid reliance on generated project artifacts.
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

left, right = st.columns(2)

with left:
    st.subheader("Transaction amounts")

    chart_df = df.copy()
    chart_df["amount"] = pd.to_numeric(chart_df["amount"], errors="coerce")
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
    st.plotly_chart(fig, use_container_width=True)

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

    summary_df = pd.DataFrame([
        {"Issue": label, "Affected records": quality[key]}
        for label, key in summary_keys
    ])

    fig = px.bar(
        summary_df,
        x="Issue",
        y="Affected records",
        title="Records flagged by each quality check",
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Detailed quality findings")

findings_df = pd.DataFrame(quality["findings"])
if findings_df.empty:
    st.success("No data quality issues found.")
else:
    issue_types = sorted(findings_df["issue_type"].unique().tolist())
    selected_issues = st.multiselect(
        "Filter by issue type",
        options=issue_types,
        default=issue_types,
    )
    st.dataframe(
        findings_df[findings_df["issue_type"].isin(selected_issues)],
        use_container_width=True,
        hide_index=True,
    )

st.divider()

st.subheader("Machine-learning anomaly results")
st.warning(
    "This model uses a small synthetic dataset. Its flags are exploratory "
    "and should not be interpreted as proof of fraud."
)

labels = sorted(anomalies["anomaly_label"].dropna().unique().tolist())
selected_labels = st.multiselect(
    "Filter by model label",
    options=labels,
    default=labels,
)

st.dataframe(
    anomalies[anomalies["anomaly_label"].isin(selected_labels)],
    use_container_width=True,
    hide_index=True,
)

with st.expander("View original demo transactions"):
    st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(
    "Demo data only. PostgreSQL ingestion and migration validation "
    "are demonstrated separately by the local pipeline."
)
