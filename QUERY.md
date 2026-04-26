# Querying Pitstop Truth

Pitstop Truth is a machine-readable corpus of execution failures and signal integrity breakdowns in AI/API systems.

This document shows how to query and use the corpus—for humans, agents, and tools.

---

## Data surfaces

The corpus exposes three primary entry points:

### 1. Capability (patterns + summary)

id="7g5s0x" https://raw.githubusercontent.com/SirBrenton/pitstop-truth/main/capability.json

Contains:
- known failure patterns
- canonical receipts
- hazard classes
- classification model (WAIT / CAP / STOP)

---

### 2. Index (receipt registry)

id="l9k9l2" https://raw.githubusercontent.com/SirBrenton/pitstop-truth/main/index.json

Contains:
- list of all receipts
- paths to each artifact
- metadata (repo, date, hazard)

---

### 3. Receipt (ground truth)

id="2dzn1n" receipts/YYYY/MM/<receipt-id>/receipt.json

Each receipt contains:

id="1h63yx" hazard → constraints → knobs → verification

---

## Human workflow

Use Pitstop Truth to classify and resolve failures:

1. Identify the failure
   - 429
   - timeout
   - retry loop
   - workflow stall

2. Search for a matching pattern
   - via capability.json
   - or by scanning pattern IDs

3. Open the canonical receipt

4. Apply:
   - constraints (what must be true)
   - knobs (what to change)

5. Validate using verification steps

---

## Agent usage (recommended prompt)

Agents can map raw failures to known patterns.

### Input

- error trace / logs / issue text

### Prompt

text id="2w4hsp" Given the following failure, map it to Pitstop Truth:  Return: - matching pattern_id (if any) - canonical receipt_id - hazard class - signal_failure_type (if inferable) - likely failure_layer - recommended constraints - recommended knobs - whether this appears to be a new pattern  Failure: <INSERT TRACE OR ISSUE> 

---

## Tool integration

### Goal

Turn Pitstop Truth into a classification backend.

### Minimal flow

1. Load capability.json
2. Match input against:
   - pattern summaries
   - hazard classes
3. Return:
   - pattern_id
   - receipt_id
   - classification (WAIT / CAP / STOP)
   - mitigation hints

---

### Example output

json id="g0m5yx" {   "pattern_id": "retry-after-ignored-under-concurrency",   "receipt_id": "PT-2026-03-21-github-openclaw-venice-models-429-retry-after-unwired",   "hazard": "rate_limit_429",   "classification": "WAIT mishandled as immediate retry",   "recommended_action": "respect_retry_after_header",   "confidence": 0.91 } 

---

## Classification model

Pitstop Truth uses a simple execution taxonomy:

- WAIT — transient pressure, retry after delay  
- CAP — reduce concurrency / rate  
- STOP — terminal or quota exhaustion, do not retry  

Most failures come from collapsing these into one branch.

---

## When to query the corpus

Use Pitstop Truth when:

- debugging rate limits (429)
- investigating retry loops
- diagnosing timeouts or stalls
- designing retry / routing / failover logic
- evaluating agent or tool behavior

---

## Design principles

- patterns are generalizable, not repo-specific
- receipts are minimal and verifiable
- signals are analyzed across system boundaries

The corpus is optimized for:

> decision support, not documentation

---

## Notes

- capability.json is the fastest entry point
- receipts provide ground truth detail
- index enables traversal and discovery

---

## Repository

https://github.com/SirBrenton/pitstop-truth