
import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = PROJECT_ROOT / "data" / "migrated" / "transactions.csv"

load_dotenv(PROJECT_ROOT / ".env")


def load_transactions(csv_path: Path = DEFAULT_CSV) -> dict:
    """Load migrated CSV records into PostgreSQL and verify the row count."""

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Migrated CSV not found: {csv_path}")

   
    df = pd.read_csv(csv_path)
    required_columns = {
    "transaction_id",
    "customer_id",
    "amount",
    "transaction_date",
    "payment_method",
    }

    missing_columns = sorted(required_columns - set(df.columns))

    if missing_columns:
        raise ValueError(
        f"CSV is missing required columns: {missing_columns}"
    )

    # Convert date strings into Python date objects for PostgreSQL.
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    ).dt.date

    # Convert missing values to None so PostgreSQL stores them as NULL.
    df = df.astype(object).where(pd.notna(df), None)


    required_env = [
        "PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"
    ]
    missing = [key for key in required_env if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing database settings: {missing}")

    with psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
    ) as conn:
        with conn.cursor() as cur:
            # Replace existing demo records so reruns don't duplicate them.
            cur.execute("TRUNCATE TABLE transactions")

            insert_sql = """
                INSERT INTO transactions (
                    transaction_id, customer_id, amount,
                    transaction_date, payment_method
                )
                VALUES (%s, %s, %s, %s, %s)
            """

            rows = [
                (
                    row.transaction_id,
                    row.customer_id,
                    row.amount,
                    row.transaction_date,
                    row.payment_method,
                )
                for row in df.itertuples(index=False)
            ]

            cur.executemany(insert_sql, rows)
            cur.execute("SELECT COUNT(*) FROM transactions")
            target_count = cur.fetchone()[0]

            if target_count != len(df):
                raise RuntimeError(
                    f"Record count mismatch: CSV={len(df)}, "
                    f"database={target_count}"
                )

    result = {
        "source_records": len(df),
        "database_records": target_count,
        "records_reconciled": len(df) == target_count,
        "status": "SUCCESS",
    }

    print("\n=== POSTGRESQL LOAD REPORT ===")
    for key, value in result.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    return result


if __name__ == "__main__":
    load_transactions()
