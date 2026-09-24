# Release notes: BatchGuard 1.0.0 (2026-09-24)

## What's new
- **Batch execution:** record each master-record step; out-of-specification values are flagged and raise a deviation automatically.
- **Corrections without data loss:** corrections require a reason and keep the original value visible ("earlier values").
- **Electronic signatures (21 CFR Part 11):** signing asks for your password again and records your printed name, the time (UTC) and the meaning (performed, verified, reviewed, approved for release, closed).
- **Second-person verification:** critical steps (API weight, hardness, tablet weight) must be verified by someone other than the person who recorded them.
- **Review and release:** a batch cannot be submitted while steps are missing or unverified, and cannot be released while deviations are open. The reviewer and the releaser must be different people.
- **Tamper-evident audit trail:** every action is logged with before/after values and reason; the page shows whether the hash chain is intact.
- **ALCOA+ report:** nine automatic data-integrity checks per batch.

## Security
Accounts lock after 3 failed logins. Sessions end after 15 minutes idle.

## Validation status
Executed IQ 13/13, OQ 12/12, PQ 3/3; all 12 functional requirements traced to passing tests. One deviation (DEV-001) found and closed during OQ. See `validation/`.

## Known limitations
Single-site SQLite database; no backup/restore; no ERP or LIMS interface; demo passwords are public.
