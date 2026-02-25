from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .schema_validate import SchemaValidationError, validate_jsonl_against_schema, iter_jsonl, load_schema, validate_against_schema


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _append_jsonl(out_path: Path, obj: Dict[str, Any]) -> None:
    _ensure_parent(out_path)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":"), sort_keys=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="pitstop-truth ingest",
        description="Validate decision_event.v1 JSONL and append to a truth ledger JSONL.",
    )
    ap.add_argument("--in", dest="in_path", required=True, help="Input receipts JSONL path")
    ap.add_argument("--schema", dest="schema_path", required=True, help="decision_event.v1 schema path")
    ap.add_argument(
        "--out",
        dest="out_path",
        default="receipts/_ingest/receipts.jsonl",
        help="Output ledger JSONL path (default: receipts/_ingest/receipts.jsonl)",
    )
    ap.add_argument("--fail-fast", action="store_true", default=True, help="Fail on first invalid line (default: true)")

    args = ap.parse_args()

    in_path = Path(args.in_path)
    schema_path = Path(args.schema_path)
    out_path = Path(args.out_path)

    if not in_path.exists() or in_path.stat().st_size == 0:
        raise SystemExit(f"ERROR: missing/empty input: {in_path}")
    if not schema_path.exists():
        raise SystemExit(f"ERROR: missing schema: {schema_path}")

    schema = load_schema(schema_path)

    n = 0
    for line_no, obj in iter_jsonl(in_path):
        try:
            validate_against_schema(obj, schema=schema, line_no=line_no)
        except SchemaValidationError as e:
            # clear, single-line failure
            raise SystemExit(f"SCHEMA ERROR: {e}") from e

        _append_jsonl(out_path, obj)
        n += 1

    if n == 0:
        raise SystemExit(f"ERROR: no events found (empty JSONL): {in_path}")

    print(f"OK: ingested {n} receipts -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())