from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in {None, ""}:
    from postgres_db import get_postgres_connection
else:
    from .postgres_db import get_postgres_connection


SCHEMA_FILES = (
    "00_extensions.sql",
    "10_parsed_layer.sql",
    "20_canonical_layer.sql",
    "30_recipe_layer.sql",
    "40_user_layer.sql",
    "50_indexes.sql",
)


def get_schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "sql" / "recipe_normalization"


def apply_sql_file(postgres_connection, schema_dir: Path, file_name: str) -> None:
    file_path = schema_dir / file_name
    sql_text = file_path.read_text(encoding="utf-8")

    print(f"Applying {file_name}...")

    with postgres_connection.transaction():
        postgres_connection.execute(sql_text, prepare=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply recipe normalization PostgreSQL schema.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the SQL files in execution order without applying them.",
    )
    args = parser.parse_args()

    schema_dir = get_schema_dir()

    if args.dry_run:
        print("Schema apply order:")
        for file_name in SCHEMA_FILES:
            print(schema_dir / file_name)
        return

    with get_postgres_connection() as postgres_connection:
        for file_name in SCHEMA_FILES:
            apply_sql_file(postgres_connection, schema_dir, file_name)

    print("Schema applied successfully.")


if __name__ == "__main__":
    main()
