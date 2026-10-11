
import pandas as pd
import pytest

from src.transformation.migration import migrate_transactions


def test_migration_preserves_record_count(tmp_path):
    source = tmp_path / "source.csv"
    target = tmp_path / "target.csv"

    df = pd.DataFrame({
        "transaction_id": ["T001", "T002"],
        "customer_id": ["C001", "C002"],
        "amount": [500, 750],
        "transaction_date": ["2026-10-01", "2026-10-02"],
        "payment_method": ["upi", "card"],
    })
    df.to_csv(source, index=False)

    result = migrate_transactions(source, target)

    assert result["source_records"] == 2
    assert result["target_records"] == 2
    assert result["records_reconciled"] is True
    assert result["status"] == "SUCCESS"
    assert target.exists()


def test_migration_rejects_missing_required_column(tmp_path):
    source = tmp_path / "incomplete.csv"
    target = tmp_path / "target.csv"

    pd.DataFrame({
        "transaction_id": ["T001"],
        "customer_id": ["C001"],
        "amount": [500],
        "transaction_date": ["2026-10-01"],
    }).to_csv(source, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        migrate_transactions(source, target)


def test_migration_rejects_missing_source_file(tmp_path):
    source = tmp_path / "does_not_exist.csv"
    target = tmp_path / "target.csv"

    with pytest.raises(FileNotFoundError):
        migrate_transactions(source, target)
