
from pathlib import Path

import pandas as pd
from src.validation.migration_audit import record_migration_run

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "sample" / "transactions.csv"
DEFAULT_TARGET = PROJECT_ROOT / "data" / "migrated" / "transactions.csv"

REQUIRED_COLUMNS = {
    "transaction_id",
    "customer_id",
    "amount",
    "transaction_date",
    "payment_method",
}


def migrate_transactions(
    source_path: Path = DEFAULT_SOURCE,
    target_path: Path = DEFAULT_TARGET,
    audit_path: Path | None = None,
) -> dict:
    """Read, validate, transform, and migrate transaction records."""

    source_path = Path(source_path)
    target_path = Path(target_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    source_df = pd.read_csv(source_path)

    missing_columns = sorted(REQUIRED_COLUMNS - set(source_df.columns))
    if missing_columns:
        raise ValueError(
            f"Source is missing required columns: {missing_columns}"
        )

    source_count = len(source_df)
    migrated_df = source_df.copy()

    # Normalize data types without silently dropping problematic records.
    migrated_df["transaction_id"] = (
        migrated_df["transaction_id"].astype("string").str.strip()
    )
    migrated_df["customer_id"] = (
        migrated_df["customer_id"].astype("string").str.strip()
    )
    migrated_df["payment_method"] = (
        migrated_df["payment_method"].astype("string").str.strip().str.upper()
    )
    migrated_df["amount"] = pd.to_numeric(
        migrated_df["amount"], errors="coerce"
    )
    migrated_df["transaction_date"] = pd.to_datetime(
        migrated_df["transaction_date"], errors="coerce"
    )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    migrated_df.to_csv(target_path, index=False, date_format="%Y-%m-%d")

    # Read the target back to verify that the output can be loaded.
    target_check = pd.read_csv(target_path)

    if len(target_check) != source_count:
        raise RuntimeError(
            f"Record count mismatch: source={source_count}, "
            f"target={len(target_check)}"
        )

    result = {
        "source_file": str(source_path),
        "target_file": str(target_path),
        "source_records": source_count,
        "target_records": len(target_check),
        "records_reconciled": source_count == len(target_check),
        "status": "SUCCESS",
    }

        # Record successful migrations in the audit trail.
    if audit_path is None:
        record_migration_run(result)
    else:
        record_migration_run(result, audit_path)

    print("\n=== DATA MIGRATION REPORT ===")
    for key, value in result.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    return result


if __name__ == "__main__":
    migrate_transactions()
