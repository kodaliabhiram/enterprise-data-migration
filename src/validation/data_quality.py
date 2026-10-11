
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "sample" / "transactions.csv"

KNOWN_CUSTOMER_IDS = {"C001", "C002", "C003", "C004"}
HIGH_VALUE_THRESHOLD = 100_000


def analyze_transactions(df: pd.DataFrame) -> dict:
    """Return data-quality issue counts for a transaction DataFrame."""

    df = df.copy()

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    )

    return {
        "total_records": len(df),
        "missing_amounts": int(df["amount"].isna().sum()),
        "duplicate_id_records": int(
            df["transaction_id"].duplicated(keep=False).sum()
        ),
        "invalid_dates": int(df["transaction_date"].isna().sum()),
        "non_positive_amounts": int((df["amount"] <= 0).sum()),
        "unknown_customers": int(
            (~df["customer_id"].isin(KNOWN_CUSTOMER_IDS)).sum()
        ),
        "high_value_transactions": int(
            (df["amount"] > HIGH_VALUE_THRESHOLD).sum()
        ),
    }


def profile_transactions(file_path: Path = DATA_FILE) -> None:
    """Load transactions and print a data-quality report."""

    df = pd.read_csv(file_path)
    report = analyze_transactions(df)

    print("\n=== TRANSACTION DATA QUALITY REPORT ===")
    for metric, value in report.items():
        print(f"{metric.replace('_', ' ').title()}: {value}")


if __name__ == "__main__":
    profile_transactions()
