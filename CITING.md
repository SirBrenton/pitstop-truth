# Citing Pitstop Truth

Pitstop Truth is a machine-readable corpus of execution failures and signal integrity breakdowns in AI/API systems.

Receipts are designed to be **referenced in issues, PRs, documentation, and audits**.

---

## Citation format

Use the following format when referencing a specific receipt:

```code
Pitstop Truth Corpus, receipt <RECEIPT_ID>   <RECEIPT_URL>
```

### Example

```code
Pitstop Truth Corpus, receipt PT-2026-04-25-github-go-github-4180-retryafter-string-boundary
https://github.com/SirBrenton/pitstop-truth
```

---

## Referencing in GitHub issues / PRs

When filing or commenting on issues, include:

```md
Related pattern: <pattern-id>   Canonical receipt: <receipt-id> 
```

### Example

```md
Related pattern: retry-after-ignored-under-concurrency
Canonical receipt: PT-2026-03-21-github-openclaw-venice-models-429-retry-after-unwired
```

Optional context line:

```md This pattern is documented across multiple production systems:
https://github.com/SirBrenton/pitstop-truth 
```

---

## Referencing patterns (capability.json)

If referencing a generalized pattern instead of a single receipt:

md Related Pitstop Truth pattern: <pattern-id>   Corpus: https://github.com/SirBrenton/pitstop-truth 

---

## When to cite

Cite Pitstop Truth when:

- you identify a recurring failure pattern (e.g. 429 misclassification, retry loops)
- you want to show that an issue generalizes beyond a single codebase
- you are proposing a fix shape that has precedent
- you want to anchor discussion in **documented evidence**, not opinion

---

## Design intent

Receipts are:

- stable (canonical IDs)
- minimal (hazard → constraints → knobs → verification)
- reusable across systems

The goal is to make execution failures:

> **referenceable, comparable, and verifiable**

---

## Attribution

If Pitstop Truth materially influenced a fix, design, or investigation, attribution is appreciated but not required.

---

## Repository

https://github.com/SirBrenton/pitstop-truth