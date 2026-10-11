
import pandas as pd
import pytest

from src.ml.anomaly_detector import detect_anomalies


def create_transactions():
    return pd.DataFrame({
        "transaction_id": [f"T{i:03d}" for i in range(1, 9)],
        "customer_id": ["C001"] * 8,
        "amount": [400, 450, 500, 550, 600, 650, 700, None],
        "transaction_date": ["2026-10-01"] * 8,
        "payment_method": ["UPI"] * 8,
    })


def test_anomaly_detector_scores_valid_amounts(tmp_path):
    source = tmp_path / "transactions.csv"
    model_file = tmp_path / "model.joblib"
    result_file = tmp_path / "results.csv"

    create_transactions().to_csv(source, index=False)

    result = detect_anomalies(source, model_file, result_file)

    assert len(result) == 8
    assert (result["anomaly_label"] != "not_scored").sum() == 7
    assert result.loc[7, "anomaly_label"] == "not_scored"
    assert result.loc[:6, "anomaly_score"].notna().all()
    assert model_file.exists()
    assert result_file.exists()


def test_missing_amount_column_is_rejected(tmp_path):
    source = tmp_path / "invalid.csv"

    pd.DataFrame({
        "transaction_id": ["T001"],
        "customer_id": ["C001"],
    }).to_csv(source, index=False)

    with pytest.raises(ValueError, match="amount"):
        detect_anomalies(
            source,
            tmp_path / "model.joblib",
            tmp_path / "results.csv",
        )


def test_too_few_valid_amounts_are_rejected(tmp_path):
    source = tmp_path / "small.csv"

    pd.DataFrame({
        "transaction_id": ["T001", "T002"],
        "amount": [100, None],
    }).to_csv(source, index=False)

    with pytest.raises(ValueError, match="At least 5"):
        detect_anomalies(
            source,
            tmp_path / "model.joblib",
            tmp_path / "results.csv",
        )
