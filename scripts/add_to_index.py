import json
from datetime import datetime, timezone
from pathlib import Path
import argparse

def now_utc_z():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--date", required=True)  # YYYY-MM-DD
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--path", required=True)  # receipts/.../receipt.json
    ap.add_argument("--hazard", action="append", default=[])
    ap.add_argument("--signal", action="append", default=[])
    ap.add_argument("--knob", action="append", default=[])
    args = ap.parse_args()

    idx = Path("index.json")
    data = json.loads(idx.read_text())

    entry = {
        "id": args.id,
        "date": args.date,
        "hazard_class": args.hazard,
        "source_url": args.source_url,
        "repo": args.repo,
        "signals": args.signal,
        "knobs": args.knob,
        "path": args.path,
    }

    # upsert by id (so re-running doesn't duplicate)
    receipts = data.get("receipts", [])
    receipts = [r for r in receipts if r.get("id") != args.id]
    receipts.append(entry)
    data["receipts"] = receipts
    data["updated_at"] = now_utc_z()

    idx.write_text(json.dumps(data, indent=2) + "\n")
    print("Updated index.json")

if __name__ == "__main__":
    main()
