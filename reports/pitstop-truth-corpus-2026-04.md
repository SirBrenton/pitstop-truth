# Pitstop Truth Corpus — April 2026

## TL;DR

Across 51 production incidents, AI/API systems do not primarily fail due to missing retries.

They fail because execution signals lose integrity across layers:

- signals are ignored
- signals are misclassified
- signals are hidden or overwritten
- signals fail to reach the layer that makes the decision

The result is predictable:

- retry amplification
- blocked failover
- false liveness
- stalled workflows

---

## Corpus overview

- Receipts: 51  
- Repositories: 30+  
- Time range: July 2025 → April 2026  
- Primary hazard class: rate_limit_429  
- Secondary classes: timeout_deadline, retry_budget_exhausted  

Each receipt is structured:

hazard → constraints → knobs → verification

All receipts are:
- evidence-backed (issues, logs, PRs)
- schema-validated
- machine-readable (receipt.v0)

---

## Core patterns

### Pattern 1 — Retry-After ignored

Clients detect 429 but do not consult the Retry-After header.

Result:
- retries occur inside provider cooldown window
- all attempts are wasted

Effect: retry amplification

---

### Pattern 2 — STOP vs WAIT collapse

Different failure modes share the same retry path:

- transient rate limit (WAIT)
- quota exhaustion (STOP)

Result:
- systems retry when recovery is impossible

Effect: false liveness + wasted budget

---

### Pattern 3 — Signal lost at boundary

A signal exists in one layer but disappears before decision:

- typed error → string
- header → log
- SDK → tool interface

Result:
- downstream systems must guess behavior

Effect: incorrect retry + degraded routing

---

### Pattern 4 — Failover blocked by classification gap

Fallback logic only triggers for specific error types.

Equivalent signals from other providers are not recognized.

Result:
- system remains pinned to failing provider

Effect: blocked failover

---

### Pattern 5 — Hidden retries create false liveness

Retries occur inside transport or runtime layers without visibility.

Result:
- system appears healthy
- latency and cost increase silently

Effect: silent degradation

---

### Pattern 6 — Correct parsing, incomplete decisioning

The system reads the signal correctly but does not act on it correctly.

Examples:
- Retry-After parsed but not used to classify STOP vs WAIT
- Detector fixed but actor logic unchanged

Result:
- fix addresses syntax, not semantics

Effect: persistent failure despite partial fix

---

## Pattern propagation

Receipt PT-2026-04-19 documents a case where a fix in one repository
(cline/cline) was independently implemented in another (OpenClaw)
via issue citation.

This shows:

- failure patterns propagate across systems  
- fixes propagate the same way  
- a shared reference accelerates convergence  

The corpus is beginning to act as a coordination layer, not just a record.

---

## Signal integrity failures in well-architected systems

Several receipts originate from systems with:

- strong typing  
- structured error handling  
- extensive test coverage  
- formal methods (TLA+, Kani)

Despite this, failures still occur at execution boundaries.

Component correctness does not guarantee:

- correct classification  
- correct routing  
- correct propagation of signals  

The dominant failure mode is not implementation quality.

It is:

> loss of signal integrity across layers

---

## Signal topology (emerging model)

Receipts increasingly capture:

- where a signal originates
- where it fails
- which layer makes the decision
- what behavior results

This enables a new diagnostic frame:

Not just:
- what failed

But:
- where the signal broke

---

## What signal failures cost

Across documented cases, signal integrity failures convert
directly into predictable operational loss:

- retry loops burn API budget against conditions that cannot recover
- workflows stall while appearing active, blocking downstream systems
- failover paths never execute because classification never reaches routing

These are not intermittent failures.

They are deterministic outcomes of acting on signals
that are incomplete, misclassified, or lost across layers.

The system does not degrade gracefully.

It degrades *expensively and invisibly*.

---

## Implications

### 1. Retry logic alone is insufficient because it amplifies cost when classification is wrong.

Retries without classification create:

- amplification
- cost burn
- degraded systems that appear active

---

### 2. Classification must precede action

Every failure must be classified before:

- retry
- fallback
- cooldown
- escalation

---

### 3. Signal preservation is a first-class concern

Systems must preserve:

- Retry-After
- quota semantics
- scope (provider vs credential vs account)

Across all boundaries.

---

### 4. Execution is a cross-layer problem

Failures rarely live in one place.

They emerge from interactions between:

- transport
- runtime
- classifier
- orchestrator

---

## How to use this corpus

- Reference canonical receipts in issues and PRs  
- Compare system behavior against known failure patterns  
- Extract constraints and knobs into runtime policy  
- Validate fixes using the verification steps  

Corpus entrypoint:

- https://github.com/SirBrenton/pitstop-truth
- index.json
- capability.json

---

## Citation

If this report or corpus informs your work:

Pitstop Truth Corpus, April 2026 https://github.com/SirBrenton/pitstop-truth

---

## Closing

This corpus is not a collection of bugs.

It is a record of how systems fail when signals cannot be trusted.

The patterns are consistent.

The failures are reproducible.

And the fixes are beginning to propagate.