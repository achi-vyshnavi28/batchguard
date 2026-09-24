# Enablement one-pager: BatchGuard 1.1 (for sales, CS and implementation)

## In one sentence
Operators log equipment cleaning in the system, batches can't start on dirty equipment, and QA can formally reject a failed batch.

## Why customers care
- **Cross-contamination risk:** today, cleaning is on paper; QA finds gaps only at batch review.
- **Stuck batches:** failed batches sat "in review" forever; now they're rejected with a reason and signature, and locked.

## What to say / not say
| Say | Don't say |
|---|---|
| "Cleaning validity is enforced before a batch can start." | "It's impossible to start on dirty equipment" (QA override exists) |
| "Rejection requires a reason and an e-signature and is in the audit trail." | "Rejected batches can be reopened" (they can't) |
| "Validation evidence for 1.1 ships with the release." | "No validation needed" (customers still own their validation) |

## Likely customer questions
| Question | Answer |
|---|---|
| Can we set our own cleaning validity period? | Yes, per equipment (default 72 h). *Pending product confirmation: counted from the end of cleaning.* |
| Who can override the block? | QA only, with reason + e-signature, audit-trailed. *Pending product decision (spec gap on US-104).* |
| Does rejection delete data? | No. Records are kept and locked. |

## Demo script (5 minutes)
1. Show GR-01 with **expired** cleaning → try to start a batch → blocked.
2. Record a major cleaning (operator) → supervisor verifies → start succeeds.
3. Open a batch in review with an open deviation → QA **rejects** with reason → show the audit trail entry.
