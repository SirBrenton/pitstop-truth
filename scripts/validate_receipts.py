#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "receipt.v0.json"
RECEIPTS_DIR = ROOT / "receipts"

def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    receipt_paths = sorted(RECEIPTS_DIR.glob("**/receipt.json"))

    if not receipt_paths:
        print("No receipts found under receipts/**/receipt.json")
        return 0

    bad = 0
    for p in receipt_paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            jsonschema.validate(instance=data, schema=schema)
        except Exception as e:
            bad += 1
            print(f"INVALID: {p}: {e}", file=sys.stderr)

    if bad:
        print(f"FAIL: {bad} invalid receipt(s)", file=sys.stderr)
        return 2

    print(f"OK: validated {len(receipt_paths)} receipt(s)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
