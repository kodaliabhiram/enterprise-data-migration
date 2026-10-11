import json

import pytest

from src.validation.data_quality import profile_transactions
import pandas as pd

from src.validation.data_quality import analyze_transactions


def sample_transactions():
    return pd.DataFrame(
        {
            "transaction_id": ["T001", "T002", "T002", "T004"],
            "customer_id": ["C001", "C002", "C002", "C999"],
            "amount": [500, None, 450, -20],
            "transaction_date": [
                "2026-10-01",
                "2026-10-02",
                "2026-10-02",
                "invalid-date",
            ],
            "payment_method": ["UPI", "CARD", "UPI", "CASH"],
        }
    )


def test_quality_report_detects_expected_issues():
    report = analyze_transactions(sample_transactions())

    assert report["total_records"] == 4
    assert report["missing_amounts"] == 1
    assert report["duplicate_id_records"] == 2
    assert report["invalid_dates"] == 1
    assert report["non_positive_amounts"] == 1
    assert report["unknown_customers"] == 1
    assert report["high_value_transactions"] == 0


def test_clean_data_has_no_quality_issues():
    clean = pd.DataFrame(
        {
            "transaction_id": ["T101", "T102"],
            "customer_id": ["C001", "C002"],
            "amount": [500, 750],
            "transaction_date": ["2026-10-01", "2026-10-02"],
            "payment_method": ["UPI", "CARD"],
        }
    )

    report = analyze_transactions(clean)

    assert report["total_records"] == 2
    assert report["missing_amounts"] == 0
    assert report["duplicate_id_records"] == 0
    assert report["invalid_dates"] == 0
    assert report["non_positive_amounts"] == 0
    assert report["unknown_customers"] == 0
    assert report["high_value_transactions"] == 0

def test_missing_required_column_is_rejected():
    incomplete = pd.DataFrame(
        {
            "transaction_id": ["T001"],
            "customer_id": ["C001"],
            "amount": [500],
            "transaction_date": ["2026-10-01"],
        }
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_transactions(incomplete)


def test_json_report_contains_summary_and_findings(tmp_path):
    source = tmp_path / "transactions.csv"
    report_file = tmp_path / "quality_report.json"

    sample_transactions().to_csv(source, index=False)

    report = profile_transactions(source, report_file)

    saved_report = json.loads(
        report_file.read_text(encoding="utf-8")
    )

    assert saved_report["summary"]["total_records"] == 4
    assert saved_report["findings"]
    assert "generated_at_utc" in saved_report
    assert report == saved_report


def test_empty_dataset_is_handled():
    empty = pd.DataFrame(
        columns=[
            "transaction_id",
            "customer_id",
            "amount",
            "transaction_date",
            "payment_method",
        ]
    )

    report = analyze_transactions(empty)

    assert report["total_records"] == 0
    assert report["findings"] == []
