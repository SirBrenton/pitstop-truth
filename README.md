# pitstop-truth

Machine-readable “truth artifacts” (receipts) for reliability failures: rate limits, retries, timeouts, flaky CI.

Each receipt links to primary evidence and normalizes:

**hazard → constraints → knobs → verification**

## What this repo is for

This repo is a public library of small, audit-friendly receipts that:
- point to primary evidence (issue, logs, PR, incident writeup)
- extract the failure mode (“hazard”)
- propose constraints/knobs that prevent recurrence
- describe how to verify the mitigation

## Structure

- `index.json` — machine entrypoint (registry of receipts)
- `schemas/receipt.v0.json` — JSON schema for receipts
- `receipts/YYYY/MM/<receipt-id>/receipt.json` — one receipt per folder

## Receipt contract (v0)

A receipt is a single JSON file that conforms to `schemas/receipt.v0.json`.

### Required fields
- `schema_version`: must be `"receipt.v0"`
- `id`: `PT-YYYY-MM-DD-<slug>` (lowercase a–z / 0–9 / `-`, slug len ≥ 8)
- `created_at`: ISO 8601 datetime (UTC recommended, `...Z`)
- `source`:
  - `url` (primary evidence)
  - `kind`: `github_issue | github_pr | log | incident_postmortem | other`
  - optional: `repo`, `issue_or_pr`, plus any extra metadata (allowed)
- `hazard`:
  - `class`: array of hazard class strings (e.g. `rate_limit_429`, `retry_budget_exhausted`)
  - `summary`: one-line description of the failure mode
  - `signals`: machine-readable-ish strings extracted from evidence (error text, headers, “--parallel 1 fixes”, etc.)
- `constraints`: array of “must be true” guardrails that prevent recurrence
- `knobs`: array of configurable controls (limits, backoff params, concurrency caps, etc.)
- `verification`: array of steps to prove mitigation worked

### Optional fields
- `notes`: freeform context
- `tags`: array of strings

Schema: `schemas/receipt.v0.json`

> Schema enforcement tooling not wired yet; for now we validate JSON syntax and keep the contract tight.

## Adding a new receipt (daily workflow)

1) Create a new receipt folder:

```bash
DATE="YYYY-MM-DD"
YYYY="${DATE%%-*}"
MM="${DATE#*-}"; MM="${MM%%-*}"
RID="PT-$DATE-<source>-<slug>"
mkdir -p "receipts/$YYYY/$MM/$RID"
```

2. Add receipt.json in that folder and validate it locally:

```bash
python3 -m json.tool "receipts/YYYY/MM/$RID/receipt.json" >/dev/null
```

3. Upsert it into index.json using the helper script:

```bash
python3 scripts/add_to_index.py \
  --id "$RID" \
  --date "$DATE" \
  --repo "owner/name" \
  --source-url "https://..." \
  --path "receipts/YYYY/MM/$RID/receipt.json" \
  --hazard "rate_limit_429" \
  --hazard "retry_budget_exhausted" \
  --signal "--parallel 1 fixes" \
  --signal "429 after backoff" \
  --knob "parallelism_cap" \
  --knob "backoff_jitter"
```

4. Validate + commit:

```bash
python3 -m json.tool index.json >/dev/null
git add index.json "receipts/YYYY/MM/$RID/receipt.json"
git commit -m "receipt: add $RID"
git push
```

## Conventions

- IDs: PT-YYYY-MM-DD-<source>-<slug>
- Immutability: receipts should be treated as immutable once published; if you must revise, add a new receipt or note a superseding receipt in notes.
- Index stability: index.json is the canonical list for machines; paths are repo-relative.

## License

Apache-2.0

