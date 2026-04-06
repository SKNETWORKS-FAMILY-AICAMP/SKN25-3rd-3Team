from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_ETL_LIMIT = 10


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MongoDB raw recipe -> PostgreSQL parsed ETL")
    parser.add_argument("--limit", type=int, default=DEFAULT_ETL_LIMIT, help="이번 실행에서 처리할 최대 건수")
    parser.add_argument(
        "--start-after-id",
        type=str,
        default=None,
        help="이 Mongo ObjectId 이후의 문서부터 이어서 처리",
    )
    return parser


def _load_run_etl():
    if __package__ in {None, ""}:
        project_root = Path(__file__).resolve().parents[2]
        if str(project_root) not in sys.path:
            sys.path.append(str(project_root))
        from app.etl.raw_recipe_etl import run_etl
    else:
        from .raw_recipe_etl import run_etl

    return run_etl


if __name__ == "__main__":
    args = _build_parser().parse_args()
    run_etl = _load_run_etl()
    run_etl(limit=args.limit, start_after_id=args.start_after_id)
