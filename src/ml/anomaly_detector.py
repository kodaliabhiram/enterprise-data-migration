
from pathlib import Path
from xml.parsers.expat import model

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "migrated" / "transactions.csv"
MODEL_FILE = PROJECT_ROOT / "data" / "isolation_forest.joblib"
RESULT_FILE = PROJECT_ROOT / "data" / "anomaly_results.csv"


def detect_anomalies(
    input_path: Path = DEFAULT_INPUT,
    model_path: Path = MODEL_FILE,
    result_path: Path = RESULT_FILE,
) -> pd.DataFrame:
    """Fit an Isolation Forest model and label unusual transaction amounts."""

    input_path = Path(input_path)
    model_path = Path(model_path)
    result_path = Path(result_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    if "amount" not in df.columns:
        raise ValueError("Input data must contain an 'amount' column")

    # Convert invalid or missing amounts to NaN.
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # Do not train on missing amounts or infinite values.
    valid_mask = df["amount"].notna() & df["amount"].map(
        lambda value: abs(value) != float("inf")
    )
    training_values = df.loc[valid_mask, ["amount"]]

    if len(training_values) < 5:
        raise ValueError(
            "At least 5 valid transaction amounts are required "
            "for this demonstration"
        )

    model = IsolationForest(
        n_estimators=200,
        contamination=0.15,
        random_state=42,
    )
    model.fit(training_values)

    
    df["anomaly_label"] = pd.Series(
    ["not_scored"] * len(df), index=df.index, dtype=object
)
    df["anomaly_score"] = float("nan")

    predictions = model.predict(training_values)
    labels = pd.Series(predictions, index=training_values.index).map(
    {1: "normal", -1: "anomaly"}
)

    df.loc[valid_mask, "anomaly_label"] = labels
    df.loc[valid_mask, "anomaly_score"] = model.decision_function(
    training_values
)

    df.loc[valid_mask, "anomaly_score"] = model.decision_function(
        training_values
    )

    model_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, model_path)
    df.to_csv(result_path, index=False)

    print("\n=== ANOMALY DETECTION REPORT ===")
    print(f"Total records: {len(df)}")
    print(f"Scored records: {int(valid_mask.sum())}")
    print(f"Not scored: {int((~valid_mask).sum())}")
    print(
        "Anomalies detected: "
        f"{int((df['anomaly_label'] == 'anomaly').sum())}"
    )
    print(f"Results saved to: {result_path}")
    print(f"Model saved to: {model_path}")

    return df


if __name__ == "__main__":
    detect_anomalies()
