
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_FILE = (
    PROJECT_ROOT / "data" / "migration_audit.csv"
)

AUDIT_COLUMNS = [
    "run_id",
    "run_timestamp_utc",
    "source_file",
    "target_file",
    "source_records",
    "target_records",
    "records_reconciled",
    "status",
]


def record_migration_run(
    migration_result: dict,
    audit_path: Path = DEFAULT_AUDIT_FILE,
) -> dict:
    """Append a migration result to the audit history."""

    required_keys = {
        "source_file",
        "target_file",
        "source_records",
        "target_records",
        "records_reconciled",
        "status",
    }

    missing_keys = sorted(required_keys - set(migration_result))
    if missing_keys:
        raise ValueError(
            f"Migration result is missing required keys: {missing_keys}"
        )

    audit_path = Path(audit_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate a unique identifier and an explicit UTC timestamp.
    timestamp = datetime.now(timezone.utc)
    run_id = timestamp.strftime("%Y%m%dT%H%M%S%fZ")

    record = {
        "run_id": run_id,
        "run_timestamp_utc": timestamp.isoformat(),
        "source_file": str(migration_result["source_file"]),
        "target_file": str(migration_result["target_file"]),
        "source_records": int(migration_result["source_records"]),
        "target_records": int(migration_result["target_records"]),
        "records_reconciled": bool(
            migration_result["records_reconciled"]
        ),
        "status": str(migration_result["status"]),
    }

    # Preserve existing history when appending another run.
    if audit_path.exists():
        history = pd.read_csv(audit_path)

        if list(history.columns) != AUDIT_COLUMNS:
            raise ValueError(
                "Existing audit file has an unexpected schema."
            )

        history = pd.concat(
            [history, pd.DataFrame([record])],
            ignore_index=True,
        )
    else:
        history = pd.DataFrame([record], columns=AUDIT_COLUMNS)

    history.to_csv(audit_path, index=False)

    return record


def read_migration_history(
    audit_path: Path = DEFAULT_AUDIT_FILE,
) -> pd.DataFrame:
    """Read the saved migration history."""

    audit_path = Path(audit_path)

    if not audit_path.exists():
        return pd.DataFrame(columns=AUDIT_COLUMNS)

    history = pd.read_csv(audit_path)

    if list(history.columns) != AUDIT_COLUMNS:
        raise ValueError(
            "Existing audit file has an unexpected schema."
        )

    return history