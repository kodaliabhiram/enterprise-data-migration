
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data" / "sample" / "transactions.csv"
REPORT_FILE = PROJECT_ROOT / "data" / "quality_report.json"

KNOWN_CUSTOMER_IDS = {"C001", "C002", "C003", "C004"}
HIGH_VALUE_THRESHOLD = 100_000


def analyze_transactions(df: pd.DataFrame) -> dict:
    """Analyze transaction data and return summary counts and findings."""

    df = df.copy()

    required_columns = {
        "transaction_id",
        "customer_id",
        "amount",
        "transaction_date",
        "payment_method",
    }
    missing_columns = sorted(required_columns - set(df.columns))

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    raw_amounts = df["amount"].copy()
    raw_dates = df["transaction_date"].copy()

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    )

    duplicate_mask = df["transaction_id"].duplicated(keep=False)
    missing_amount_mask = raw_amounts.isna() | df["amount"].isna()
    invalid_date_mask = raw_dates.notna() & df["transaction_date"].isna()
    non_positive_mask = df["amount"].le(0).fillna(False)
    unknown_customer_mask = ~df["customer_id"].isin(KNOWN_CUSTOMER_IDS)
    high_value_mask = df["amount"].gt(HIGH_VALUE_THRESHOLD).fillna(False)

    findings = []

    checks = [
        ("missing_or_non_numeric_amount", missing_amount_mask),
        ("duplicate_transaction_id", duplicate_mask),
        ("invalid_transaction_date", invalid_date_mask),
        ("non_positive_amount", non_positive_mask),
        ("unknown_customer", unknown_customer_mask),
        ("high_value_transaction", high_value_mask),
    ]

    for issue_type, mask in checks:
        for index in df.index[mask]:
            findings.append(
                {
                    "row_number": int(df.index.get_loc(index)) + 2,
                    "transaction_id": (
                        str(df.at[index, "transaction_id"])
                        if pd.notna(df.at[index, "transaction_id"])
                        else None
                    ),
                    "issue_type": issue_type,
                }
            )

    return {
        "total_records": int(len(df)),
        "missing_amounts": int(missing_amount_mask.sum()),
        "duplicate_id_records": int(duplicate_mask.sum()),
        "invalid_dates": int(invalid_date_mask.sum()),
        "non_positive_amounts": int(non_positive_mask.sum()),
        "unknown_customers": int(unknown_customer_mask.sum()),
        "high_value_transactions": int(high_value_mask.sum()),
        "findings": findings,
    }


def profile_transactions(
    file_path: Path = DATA_FILE,
    report_path: Path = REPORT_FILE,
) -> dict:
    """Analyze a CSV file, save a JSON report, and return the report."""

    df = pd.read_csv(file_path)
    analysis = analyze_transactions(df)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": file_path.name,
        "summary": {
            key: value
            for key, value in analysis.items()
            if key != "findings"
        },
        "findings": analysis["findings"],
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== TRANSACTION DATA QUALITY REPORT ===")
    for metric, value in report["summary"].items():
        print(f"{metric.replace('_', ' ').title()}: {value}")
    print(f"\nJSON report saved to: {report_path}")

    return report


if __name__ == "__main__":
    profile_transactions()
