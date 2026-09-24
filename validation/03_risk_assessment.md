# 03 Risk assessment (GAMP 5 functional risk assessment + CSA)

Scoring: Severity (S) and Probability (P) on 1-3; Detectability (D) 1 = certain detection, 3 = unlikely.
Risk priority = S × P × D. ≥ 12 → scripted testing with negative cases (CSA: "high process risk").

| FRS | Function | Failure mode | Impact | S | P | D | RPN | Control | Test approach |
|---|---|---|---|---|---|---|---|---|---|
| FRS-01 | Login / lockout | Brute-force or shared password | Unattributable records | 3 | 2 | 3 | 18 | PBKDF2 hashes, lockout after 3 failures, 15-min session | Scripted, negative |
| FRS-02 | Role permissions | Operator releases a batch | Unreviewed product released | 3 | 2 | 2 | 12 | Server-side permission check on every action | Scripted, negative (API + UI) |
| FRS-03 | Contemporaneous entry | Values back-filled hours later | Data not trustworthy | 3 | 2 | 3 | 18 | Server timestamps, 30-min window, future-time block | Scripted, negative |
| FRS-04 | OOS detection | Out-of-spec value missed | Defective batch released | 3 | 2 | 3 | 18 | Automatic deviation on every entry and correction | Scripted |
| FRS-05 | Corrections | Original overwritten | Loss of original record | 3 | 2 | 3 | 18 | Supersede model, reason required | Scripted, negative |
| FRS-06 | E-signature | Signature without re-authentication | Repudiation | 3 | 2 | 3 | 18 | Password re-entry, manifest with name/time/meaning | Scripted, negative |
| FRS-07 | Two-person rule | Self-verification | Independent check bypassed | 3 | 2 | 2 | 12 | Recorder ≠ verifier; reviewer ≠ releaser | Scripted, negative |
| FRS-08 | Release gating | Release with open deviation | Defective batch released | 3 | 2 | 2 | 12 | Blocker list checked at submit and release | Scripted + end-to-end |
| FRS-09 | Audit trail | Silent edit of history | Undetectable falsification | 3 | 1 | 3 | 9 | SHA-256 hash chain, verification on demand | Scripted (tampering simulated) |
| FRS-10 | Record lock | Change after release | Released record altered | 3 | 1 | 2 | 6 | Status lock on all mutating actions | Scripted |
| FRS-11 | ALCOA+ report | Wrong pass/fail | False assurance | 2 | 2 | 2 | 8 | Nine automatic checks | Scripted |
| FRS-12 | Deviation closure | Closed without investigation | Root cause unknown | 3 | 2 | 2 | 12 | QA-only, summary ≥ 20 chars, e-signature | Scripted, negative |

## Residual risks (accepted for the demonstration system)
- SQLite single-file database: no production backup/restore or high-availability qualification.
- Demo passwords are published in the README for reviewers; a real deployment requires unique passwords and periodic expiry.
- Clock source is the application server; a production system would use a synchronised, controlled time source.
