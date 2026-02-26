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

## Eligibility (what qualifies as a truth artifact)

A receipt is eligible if it has:

- **Primary evidence** (issue, PR, logs, release note, or postmortem)
- A **clear failure mode** worth naming (hazard)
- At least one constraint (“must be true”) and one knob (“we can tune this”)
- A **verification path** (how you’d prove the mitigation worked)

Receipts may be sourced from **public issues/PRs/releases even when the incident is already fixed** — already fixed is fine **if the evidence is still legible and the mitigation generalizes.**

## Receipt worthiness (tight / expensive truth)

This repo is intentionally **high-signal**. Not every “bug” or “rate limit” is a receipt.

A candidate is receipt-worthy only if it meets **all** of:

1) **Real failure, not a wishlist**
   - Evidence of an actual incident: error output, status codes, timeouts, CI failure logs, user impact.
   - Not just “implement X” / “add rate limiting” / generic hardening.
   - If the issue has no incident evidence (only ‘please add rate limiting’), it’s not a receipt.

2) **Reusable pattern**
   - The failure mode generalizes beyond one codebase (e.g., 429 + Retry-After, retry budget exhaustion, deadline exceeded masking root cause).
   - If it’s a one-off patch detail, it doesn’t belong here.

3) **Leverage**
   - The constraints/knobs materially change outcomes (reduce recurrence, bound blast radius, make diagnosis faster).
   - A receipt should teach a guardrail, not narrate a fix.

Radar can surface candidates; **this repo is the final filter.**

If it wouldn’t help a different team six months from now, don’t capture it.

## Structure

- `index.json` — machine entrypoint (registry of receipts)
- `schemas/receipt.v0.json` — JSON schema for curated truth artifacts
- `schemas/decision_event.v1.schema.json` — canonical execution receipt schema
- `pitstop_truth/ingest.py` — JSONL ingest + `decision_event.v1` validation
- `receipts/YYYY/MM/<receipt-id>/receipt.json` — one curated receipt per folder

---

## Two layers of receipts

This repo works with **two distinct receipt types**:

### 1) Execution receipts (`decision_event.v1`)

Machine-emitted execution records (produced by **Pitstop Guard** in `pitstop-commons`) and consumable by `pitstop-scan`.

- Schema: `schemas/decision_event.v1.schema.json`
- Format: JSONL (one event per line)
- Ingested here by: `pitstop_truth.ingest`

These receipts capture runtime facts:

- operation + endpoint
- budget + retry envelope
- outcome + error classification
- latency + cost
- policy decision

They are **canonical and mechanical**, not editorial.

Example ingest:

```bash
python -m pitstop_truth.ingest \
  --in ../pitstop-commons/proto/receipts.run.jsonl \
  --schema schemas/decision_event.v1.schema.json \
  --out receipts/_ingest/receipts.jsonl
  ```
Execution receipts are append-only and may be high volume.

### 2) Curated Truth Artifacts (receipt.v0)

Human-authored, normalized reliability learnings.

- Schema: `schemas/receipt.v0.json`
- Stored as: `receipts/YYYY/MM/<receipt-id>/receipt.json`
- Indexed via: `index.json`

These receipts answer:

**hazard → constraints → knobs → verification**

They are editorial and high-signal.

#### In practice:

- Many execution receipts may roll up into a single curated truth artifact.
- Truth artifacts describe the generalizable lesson.

#### Schema enforcement:

- `decision_event.v1` is validated via `jsonschema` during ingest (`pitstop_truth/ingest.py`).
- `receipt.v0` is validated via `scripts/validate_receipts.py` (jsonschema over `receipts/**/receipt.json`).

## Receipt contract (v0)

A receipt is a single JSON file that conforms to `schemas/receipt.v0.json`.

### Required fields
- `schema_version`: must be `"receipt.v0"`

- `id`: `PT-YYYY-MM-DD-<slug> where <slug> is lowercase a–z / 0–9 / '-' and length ≥ 8.`
  - `<slug>` must be lowercase `a–z / 0–9 / '-'`  
  - minimum length ≥ 8 characters  
  - **Convention:** prefix the slug with a source hint such as `github-issue-`, `github-pr-`, `log-`, `incident-`

- `created_at`: ISO 8601 datetime (UTC recommended, e.g. `2026-02-26T07:31:39Z`)

- `source`:
  - `url` (primary evidence)
  - `kind`: `github_issue | github_pr | log | incident_postmortem | other`
  - optional: `repo`, `issue_or_pr`, plus any additional metadata (allowed)

- `hazard`:
  - `class`: array of hazard class strings  
    (e.g. `rate_limit_429`, `retry_budget_exhausted`)
  - `summary`: one-line description of the failure mode
  - `signals`: array of machine-readable-ish strings extracted from evidence  
    (error text, headers, log fragments, “--parallel 1 fixes”, etc.)

- `constraints`: array of “must be true” guardrails that prevent recurrence

- `knobs`: array of configurable controls  
  (limits, backoff params, concurrency caps, driver flags, etc.)

- `verification`: array of steps to prove mitigation worked

### Optional fields
Optional fields may be omitted.

- `notes`: freeform context (background, edge cases, why the mitigation mattered, etc.)

- `tags`: array of strings for lightweight grouping  
  (e.g. `ci`, `rate_limit`, `timeout`, `driver`, `control_plane`)

- `mitigation_signature`: compact, comparable summary of the guardrail pattern  
  Intended for clustering and deduplication across receipts.  
  Typical structure:
  - `hazards`: normalized hazard labels
  - `constraints`: distilled guardrail invariants
  - `knobs`: key control surfaces
  - `anti_patterns`: common failure shapes this prevents

- `routing_impact`: router / executor-facing implications of the hazard  
  Describes how a runtime system should behave when this pattern is detected.  
  May include:
  - `default_action` (e.g. `cooldown_and_route_away`, `failfast_with_hint`)
  - cooldown semantics or scope keys
  - probe strategy guidance
  - classification rules
  - detection thresholds (log signatures, repeat counts, etc.)

Schema: `schemas/receipt.v0.json`

Schema enforcement:
- `decision_event.v1` is validated via `jsonschema` during ingest (`pitstop_truth/ingest.py`).
- `receipt.v0` is validated via `scripts/validate_receipts.py` (jsonschema across `receipts/**/receipt.json`).

Run locally:
```bash
python3 scripts/validate_receipts.py
```

## Adding a new receipt (daily workflow)

1) Create a new receipt folder:

```bash
DATE="YYYY-MM-DD"
YYYY="${DATE%%-*}"
MM="${DATE#*-}"; MM="${MM%%-*}"
RID="PT-$DATE-<slug>"   # where slug starts with github-issue-... / github-pr-... etc
mkdir -p "receipts/$YYYY/$MM/$RID"
```

2. Add receipt.json in that folder and validate it locally:

```bash
python3 scripts/validate_receipts.py
python3 -m json.tool index.json >/dev/null
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

4. Validate receipts + index (schema + JSON):
```bash
python3 scripts/validate_receipts.py && python3 -m json.tool index.json >/dev/null && echo "ok ✅"
```

5. Commit + push:

```bash
python3 -m json.tool index.json >/dev/null
git add index.json "receipts/YYYY/MM/$RID/receipt.json"
git commit -m "receipt: add $RID"
git push
```

## Conventions

- IDs: PT-YYYY-MM-DD-<slug> (slug convention: github-issue-..., github-pr-..., log-..., incident-...)
- Immutability: receipts should be treated as immutable once published; if you must revise, add a new receipt or note a superseding receipt in notes.
- Index stability: index.json is the canonical list for machines; paths are repo-relative.

## License

Apache-2.0

