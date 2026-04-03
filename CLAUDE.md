# pitstop-truth — Claude operating context

## What this repo is

Machine-readable corpus of execution failure receipts.
25 receipts. 13 documented patterns. capability.json v0.1.9.

Every receipt documents a real production failure —
classified, verified, and cross-referenced across systems.

## The taxonomy

WAIT — transient pressure. Retry after Retry-After duration.
CAP  — concurrency/throughput pressure. Reduce parallel requests first.
STOP — quota exhaustion or terminal error. Do not retry.

HTTP status alone is insufficient. Two 429s can require
opposite actions depending on body content and headers.

## Receipt worthiness filter

A candidate qualifies ONLY if ALL three are true:

1. Real failure evidence exists
   — logs, headers, error strings, session files
   — not a wishlist, not "please add rate limiting"

2. Pattern generalizes beyond one codebase
   — the failure shape recurs in other systems

3. Fix has leverage
   — changes outcomes, not just narrates them

If it wouldn't help a different team six months from now,
don't capture it.

## What makes a receipt strong

- Primary evidence: real logs, headers, error bodies
- Contrast: two failure shapes that look identical but
  require different responses
- Consequence: what actually broke downstream
- Scope: how far the failure propagated

The GSD billing-gate receipt (PT-2026-04-02) is a strong
example — documents correct classification with wrong
enforcement scope, confirmed by author tracing the code.

## What to skip immediately

- Issues with no incident evidence
- Bounty / student / hackathon repos
- Closed issues where fix is already merged and pattern
  doesn't generalize
- Threads where root cause is server infrastructure
  (500s, outages) — not classification problems
- ai-doctor spam comments — not signal

## Branch workflow

Never commit to main directly.
Branch naming: receipt/slug, manifest/slug
Always run validate_receipts.py before push.

## Receipt ID convention

PT-YYYY-MM-DD-github-{repo-slug}-{short-description}

## The ask that follows a good diagnosis

"If you can share one redacted response (status + headers +
error body), I can reduce this to the minimal decision rule."

## Current failure classes documented

1.  WAIT mishandled as immediate retry
2.  Correct primitive unwired at call sites
3.  Quota exhaustion misclassified as transient
4.  Throughput vs quota confusion (error taxonomy collapse)
5.  Autonomous agent taxonomy convergence
6.  Taxonomy adoption in production (MassGen)
7.  Message-content classification failure
8.  Polling amplification CAP
9.  Timeout misclassified as rate limit
10. Rolling-window overage disabled
11. Quota-window 429 failover gap
12. Billing gate — message-only, wrong enforcement scope
13. STOP parent/child propagation failure

## Classifier endpoint

POST https://web-production-273d3.up.railway.app/classify
{"status":429,"headers":{"retry-after":"30"},"provider":"anthropic"}

retry-after: 30   → WAIT
retry-after: 600  → STOP
no header         → CAP

## Landing page

https://sirbrenton.github.io/pitstop

## Corpus

https://github.com/SirBrenton/pitstop-truth
