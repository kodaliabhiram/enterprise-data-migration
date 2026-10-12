
import pandas as pd
import pytest

from src.validation.migration_audit import (
    AUDIT_COLUMNS,
    read_migration_history,
    record_migration_run,
)


def sample_result():
    return {
        "source_file": "data/sample/transactions.csv",
        "target_file": "data/migrated/transactions.csv",
        "source_records": 10,
        "target_records": 10,
        "records_reconciled": True,
        "status": "SUCCESS",
    }


def test_record_migration_run_creates_audit_file(tmp_path):
    audit_path = tmp_path / "migration_audit.csv"

    record = record_migration_run(sample_result(), audit_path)

    assert record["status"] == "SUCCESS"
    assert record["records_reconciled"] is True
    assert record["source_records"] == 10

    saved = pd.read_csv(audit_path)
    assert list(saved.columns) == AUDIT_COLUMNS
    assert len(saved) == 1
    assert saved.iloc[0]["status"] == "SUCCESS"


def test_audit_preserves_multiple_runs(tmp_path):
    audit_path = tmp_path / "migration_audit.csv"

    record_migration_run(sample_result(), audit_path)
    record_migration_run(sample_result(), audit_path)

    history = read_migration_history(audit_path)

    assert len(history) == 2
    assert history["run_id"].nunique() == 2


def test_read_missing_audit_returns_empty_history(tmp_path):
    audit_path = tmp_path / "missing_audit.csv"

    history = read_migration_history(audit_path)

    assert history.empty
    assert list(history.columns) == AUDIT_COLUMNS


def test_record_migration_run_rejects_incomplete_result(tmp_path):
    audit_path = tmp_path / "migration_audit.csv"

    with pytest.raises(
        ValueError,
        match="Migration result is missing required keys",
    ):
        record_migration_run({"status": "SUCCESS"}, audit_path)

    assert not audit_path.exists()


def test_read_audit_rejects_unexpected_schema(tmp_path):
    audit_path = tmp_path / "migration_audit.csv"
    pd.DataFrame({"unexpected_column": [1]}).to_csv(
        audit_path, index=False
    )

    with pytest.raises(
        ValueError,
        match="unexpected schema",
    ):
        read_migration_history(audit_path)