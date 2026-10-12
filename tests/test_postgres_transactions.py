
import os
import uuid

import psycopg
import pytest
from dotenv import load_dotenv
from psycopg import sql

from src.ingestion.postgres_loader import PROJECT_ROOT


load_dotenv(PROJECT_ROOT / ".env")


@pytest.mark.skipif(
    not all(
        os.getenv(key)
        for key in (
            "PGHOST",
            "PGPORT",
            "PGDATABASE",
            "PGUSER",
            "PGPASSWORD",
        )
    ),
    reason="PostgreSQL connection settings are not configured",
)
def test_postgres_transaction_rolls_back_failed_insert():
    connection_settings = {
        "host": os.environ["PGHOST"],
        "port": os.environ["PGPORT"],
        "dbname": os.environ["PGDATABASE"],
        "user": os.environ["PGUSER"],
        "password": os.environ["PGPASSWORD"],
    }

    table_name = f"rollback_test_{uuid.uuid4().hex[:12]}"

    # Create an isolated temporary table in its own connection.
    with psycopg.connect(**connection_settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "CREATE TEMP TABLE {} (id INTEGER PRIMARY KEY)"
                ).format(sql.Identifier(table_name))
            )

            cur.execute(
                sql.SQL("INSERT INTO {} (id) VALUES (1)").format(
                    sql.Identifier(table_name)
                )
            )

            with pytest.raises(psycopg.errors.UniqueViolation):
                with conn.transaction():
                    cur.execute(
                        sql.SQL(
                            "INSERT INTO {} (id) VALUES (1)"
                        ).format(sql.Identifier(table_name))
                    )

            # The failed transaction should leave the original row intact.
            cur.execute(
                sql.SQL("SELECT id FROM {}").format(
                    sql.Identifier(table_name)
                )
            )
            assert cur.fetchall() == [(1,)]