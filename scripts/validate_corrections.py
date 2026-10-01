#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "correction.v0.json"
INDEX_PATH = ROOT / "index.json"
CORRECTIONS_ROOT = ROOT / "corrections"

ID_RE = re.compile(
    r"^PTC-(\d{4})-(\d{2})-(\d{2})-[a-z0-9-]{8,}$"
)

INDEX_CORRECTION_FIELDS = {
    "evidence_status",
    "correction_id",
    "correction_path",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f"{path}: {exc}")


def main() -> None:
    schema = load_json(SCHEMA_PATH)
    index = load_json(INDEX_PATH)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    entries = index.get("receipts")
    if not isinstance(entries, list):
        fail("index.json does not contain a receipts list")

    index_by_id = {}

    for entry in entries:
        rid = entry.get("id")
        if not rid:
            fail("index entry missing id")

        index_by_id.setdefault(rid, []).append(entry)

        present = INDEX_CORRECTION_FIELDS.intersection(entry)

        if present and present != INDEX_CORRECTION_FIELDS:
            fail(
                f"{rid}: correction metadata must include all of "
                f"{sorted(INDEX_CORRECTION_FIELDS)}"
            )

        if present and entry["evidence_status"] != "qualified":
            fail(
                f"{rid}: unsupported evidence_status "
                f"{entry['evidence_status']!r}"
            )

    files = sorted(
        CORRECTIONS_ROOT.rglob("correction.json")
    )

    seen_correction_ids = set()
    corrections_by_id = {}

    for correction_path in files:
        correction = load_json(correction_path)

        errors = sorted(
            validator.iter_errors(correction),
            key=lambda e: list(e.absolute_path),
        )

        if errors:
            for error in errors:
                location = ".".join(
                    str(part) for part in error.absolute_path
                ) or "<root>"

                print(
                    f"ERROR: {correction_path}: "
                    f"{location}: {error.message}",
                    file=sys.stderr,
                )

            raise SystemExit(1)

        cid = correction["id"]

        if cid in seen_correction_ids:
            fail(f"duplicate correction id: {cid}")

        seen_correction_ids.add(cid)
        corrections_by_id[cid] = (correction_path, correction)

        if correction_path.parent.name != cid:
            fail(
                f"{correction_path}: folder name does not "
                f"match correction id {cid}"
            )

        match = ID_RE.fullmatch(cid)
        if not match:
            fail(f"{correction_path}: invalid correction id {cid}")

        yyyy, mm, dd = match.groups()

        if correction_path.parent.parent.name != mm:
            fail(f"{correction_path}: month path does not match id")

        if correction_path.parent.parent.parent.name != yyyy:
            fail(f"{correction_path}: year path does not match id")

        expected_relative_path = (
            Path("corrections")
            / yyyy
            / mm
            / cid
            / "correction.json"
        )

        actual_relative_path = correction_path.relative_to(ROOT)

        if actual_relative_path != expected_relative_path:
            fail(
                f"{correction_path}: correction path must be "
                f"{expected_relative_path}"
            )

        expected_date = f"{yyyy}-{mm}-{dd}"

        if not correction["created_at"].startswith(expected_date):
            fail(
                f"{correction_path}: created_at does not "
                f"match id date {expected_date}"
            )

        target_id = correction["target_receipt_id"]
        target_entries = index_by_id.get(target_id, [])

        if len(target_entries) != 1:
            fail(
                f"{correction_path}: expected exactly one "
                f"index entry for {target_id}; "
                f"found {len(target_entries)}"
            )

        target_entry = target_entries[0]
        target_path = ROOT / target_entry["path"]

        if not target_path.exists():
            fail(
                f"{correction_path}: target receipt missing: "
                f"{target_path}"
            )

        target_receipt = load_json(target_path)

        if target_receipt.get("id") != target_id:
            fail(
                f"{correction_path}: target receipt id mismatch"
            )

        if target_entry.get("evidence_status") != correction["disposition"]:
            fail(
                f"{target_id}: index evidence_status does not "
                f"match correction disposition"
            )

        if target_entry.get("correction_id") != cid:
            fail(
                f"{target_id}: index correction_id does not "
                f"match {cid}"
            )

        expected_path = correction_path.relative_to(ROOT).as_posix()

        if target_entry.get("correction_path") != expected_path:
            fail(
                f"{target_id}: index correction_path does not "
                f"match {expected_path}"
            )

    # Reverse integrity:
    # every correction-bearing index entry must resolve to a real correction.
    for entry in entries:
        if "evidence_status" not in entry:
            continue

        cid = entry["correction_id"]

        if cid not in corrections_by_id:
            fail(
                f"{entry['id']}: correction_id {cid} "
                f"does not resolve to a correction artifact"
            )

        correction_path, correction = corrections_by_id[cid]

        if correction["target_receipt_id"] != entry["id"]:
            fail(
                f"{entry['id']}: correction targets "
                f"{correction['target_receipt_id']}"
            )

    print(f"OK: validated {len(files)} correction(s)")


if __name__ == "__main__":
    main()
