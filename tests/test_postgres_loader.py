
import pandas as pd
import pytest

from src.ingestion.postgres_loader import load_transactions


def test_loader_rejects_missing_required_columns(tmp_path):
    csv_path = tmp_path / "invalid_transactions.csv"

    # Missing customer_id and payment_method.
    pd.DataFrame({
        "transaction_id": ["T2001"],
        "amount": [500.00],
        "transaction_date": ["2026-10-01"],
    }).to_csv(csv_path, index=False)

    with pytest.raises(
        ValueError,
        match="CSV is missing required columns",
    ):
        load_transactions(csv_path)


def test_loader_rejects_missing_file(tmp_path):
    csv_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(
        FileNotFoundError,
        match="Migrated CSV not found",
    ):
        load_transactions(csv_path)
