# EXECUTION FAILURE TAXONOMY v1

## Purpose

This document defines the **minimal classification system** required to
prevent AI/API execution failures from amplifying under retry.

It exists to answer one question:

> When a request fails, what should the system do next?

Most systems answer this incorrectly.

---

## The core problem

In real systems, failures are not rare — they are constant.

What breaks systems is not the failure itself, but **how the system
responds**.

Observed pattern across 57 production systems (canonical evidence: github.com/SirBrenton/pitstop-truth):


- 429 / timeout / provider errors occur
- system treats all failures as retryable
- retries amplify pressure
- fallback misfires or never triggers
- sessions loop, stall, or burn budget

Root cause:

> **Different failure types are collapsed into a single retry behavior.**

---

## The minimal model

All execution failures must be classified into one of three actions:

**WAIT** — Transient pressure. The system should delay and retry.

**CAP** — System-induced pressure. The system should reduce concurrency
before retrying.

**STOP** — Terminal condition. The system should not retry.

---

## Classification table

| Class | Meaning | Action |
|-------|---------|--------|
| WAIT | Temporary rate limit or overload | Delay and retry |
| CAP | Too much parallelism or burst | Reduce concurrency, then retry |
| STOP | Quota exhaustion / billing / auth / hard limit | Do not retry |

---

## What to classify from

Classification is derived from real response signals:

- HTTP status code (e.g. 429, 5xx, timeout)
- Retry-After header (presence, absence, magnitude)
- Response body semantics (quota, frequency, billing, reset time)
- Request pattern (single request vs concurrent / multi-instance)

HTTP status alone is insufficient.

Two identical 429 responses may require opposite actions depending on:

- header presence
- body content
- repetition pattern

---

## Canonical failure shapes

### 1. WAIT — transient pressure

**Examples**

- `429 Requests are too frequent`
- provider busy / overloaded
- short Retry-After headers
- temporary 5xx

**Correct behavior**

- honor Retry-After if present
- apply bounded backoff
- retry

**Failure when misclassified**

- immediate retry → retry storm
- synchronized retries across workers

---

### 2. CAP — concurrency amplification

**Examples**

- multiple agents polling the same endpoint
- parallel workers exceeding shared rate limit
- additive multi-instance load

**Correct behavior**

- reduce concurrency (workers, QPS, polling)
- retry only after reduction

**Failure when misclassified**

- backoff per instance → total pressure unchanged
- system never stabilizes

---

### 3. STOP — terminal / quota exhaustion

**Examples**

- `exceeded usage quota`
- `insufficient credits`
- rolling window exhaustion
- billing tier / context limit
- auth failures

**Correct behavior**

- do not retry
- surface to caller
- fail over or wait for reset

**Failure when misclassified**

- retries cannot succeed
- budget burn continues until exhaustion
- fallback never triggers correctly

---

## Key invariants

### 1. Classification must happen before retry

Retry logic must not run on raw errors.

```
response → classify → act
```

Not:

```
response → retry → hope
```

### 2. Same status ≠ same action

All of the following may return HTTP 429:

- throughput limit (WAIT)
- concurrency pressure (CAP)
- quota exhaustion (STOP)

Status code alone is insufficient.

### 3. Error body and headers are first-class signals

Classification must use:

- headers (Retry-After, provider-specific)
- error body (quota, billing, reset time)
- repetition patterns (same error, same message)

### 4. Misclassification compounds

Wrong classification does not fail fast. It causes:

- retry amplification
- fallback suppression
- infinite loops
- silent cost burn

---

## Documented misclassification patterns

Observed across real systems:

- **WAIT treated as immediate retry**
  Retry-After ignored → retry storm

- **STOP treated as WAIT**
  Quota exhaustion retried → budget burn

- **STOP treated as WAIT via message-pattern failure**
  Structural limit with no header → misclassified from body content alone

- **Timeout treated as rate limit**
  Unified cooldown schedule → unnecessary failover cascade

- **CAP from polling amplification**
  Per-instance backoff applied to shared limit → pressure never reduces

- **Quota-window 429 treated as transient**
  Reset semantics ignored → loop continues until window clears

- **Rolling-window STOP treated as throughput WAIT**
  Provider header family not consulted → wrong backoff applied

These patterns are drawn from real production failures across multiple
systems. Canonical receipts: [pitstop-truth](https://github.com/SirBrenton/pitstop-truth)

---

## Representative signals (from real systems)

- `"Retry-After": "30"`
- `"exceeded the 5-hour usage quota"`
- `"too frequent"`
- repeated identical error bodies
- same message ID repeated 95+ times in session logs
- fallback never triggered despite repeated failure

---

## Minimal decision rule

Given: `status + headers + error body`

The system must determine:

```
WAIT  → delay
CAP   → shrink
STOP  → halt
```

---

## Why this matters

Without this classification:

- retries amplify failures
- fallback logic becomes ineffective
- budget enforcement misfires
- systems appear flaky or expensive

With this classification:

- systems stabilize under pressure
- retries become bounded
- fallback works as intended
- failures become diagnosable

---

## Relationship to other layers

**Retry layer (upstream)**
Consumes classification and executes delay, shrink, or halt.

**Enforcement layer (e.g., Cycles / budget control)**
Assumes classification is correct and commits, releases, or manages budget.

If classification is wrong upstream:

> Enforcement behaves correctly on the wrong signal.

---

## What this taxonomy is not

- not a full reliability framework
- not a retry library
- not provider-specific logic

It is:

> **The minimal decision boundary required before any retry or enforcement
> logic runs.**

---

## Status

v1 reflects patterns observed across 57 production systems.
MassGen adopted this taxonomy as a production circuit breaker within 4 hours of first contact [PR #1024](https://github.com/massgen/MassGen/pull/1024).

Full corpus: https://github.com/SirBrenton/pitstop-truth

This taxonomy is expected to evolve as new failure shapes are observed.

---

*This taxonomy is grounded in real production failures.*
*Canonical evidence: [github.com/SirBrenton/pitstop-truth](https://github.com/SirBrenton/pitstop-truth)*

## Beyond classification: enforcement correctness

Correct classification alone does not guarantee correct system behavior.

Observed across multiple systems:

- ambiguous signals escalated into account-level or global blocking
- correct STOP classification not propagated to parent systems
- retry activity hidden from higher decision layers
- fallback logic applied at incorrect scope

This introduces a second requirement:

> Classification must be enforced at the correct scope and propagated to all relevant layers.

### Additional invariants

1. **Do not escalate ambiguous signals**
   - If quota exhaustion is not explicitly confirmed, do not apply STOP-level enforcement

2. **Match enforcement scope to signal scope**
   - Request-level signal → request-level action  
   - Account-level signal → account-level action  
   - System-level signal → system-level action  

3. **Propagate terminal conditions**
   - STOP must be visible to all upstream decision layers

4. **Expose execution state**
   - Retry, delay, and block decisions must be observable (logs, metrics, receipts)

Failure in these dimensions leads to:

- false unavailability
- workflow stalls
- silent degradation
- misrouted traffic