import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def get_postgres_connection():
    postgresql_uri = os.getenv("POSTGRESQL_URI")
    if not postgresql_uri:
        raise RuntimeError("POSTGRESQL_URI is not set.")

    return psycopg.connect(
        postgresql_uri,
        sslmode="require",
        row_factory=dict_row,
        connect_timeout=5,
    )


def get_postgres_database_info():
    with get_postgres_connection() as postgres_connection:
        with postgres_connection.cursor() as cursor:
            cursor.execute("SELECT current_database() AS database_name, current_user AS user_name")
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("PostgreSQL database info could not be loaded.")
            return row
