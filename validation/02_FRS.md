# 02 Functional Requirements Specification (FRS)

System: BatchGuard electronic batch record (eBR) v1.0.0 · GAMP 5 category 5

Intended use: Record the execution of tablet-manufacturing batches against an approved master batch record, capture electronic signatures, manage deviations, and support QA release decisions. Demonstration system; not used for commercial GMP manufacturing.

| ID | Traces to | Function |
|---|---|---|
| FRS-01 | URS-01 | Username + password login (PBKDF2-hashed); account locks after 3 failed attempts; sessions expire after 15 minutes. |
| FRS-02 | URS-02 | Role permissions: operators record; supervisors create batches, verify and submit; QA verifies, closes deviations and releases. |
| FRS-03 | URS-03 | Entries store user and server timestamp; observation time cannot be in the future or more than 30 minutes before recording. |
| FRS-04 | URS-04 | An out-of-specification value automatically raises a deviation linked to the entry. |
| FRS-05 | URS-05 | Entries cannot be overwritten or deleted; a correction requires a reason (>= 10 chars) and supersedes, not replaces, the original. |
| FRS-06 | URS-06 | Signing requires password re-entry and a meaning; the manifest shows printed name, date/time (UTC) and meaning. |
| FRS-07 | URS-07 | The person who recorded a critical step cannot verify it; the batch reviewer cannot also release it. |
| FRS-08 | URS-08 | Submit/release is blocked while steps are missing, critical steps unverified, or deviations open; release needs a QA signature. |
| FRS-09 | URS-09 | Append-only audit trail (user, time, action, before/after, reason) hash-chained with SHA-256; chain verification detects edits. |
| FRS-10 | URS-10 | Released or rejected batches reject all further changes. |
| FRS-11 | URS-11 | Per-batch ALCOA+ report with automatic checks for all nine principles. |
| FRS-12 | URS-12 | Deviation closure requires QA role, an investigation summary (>= 20 chars) and an e-signature. |
