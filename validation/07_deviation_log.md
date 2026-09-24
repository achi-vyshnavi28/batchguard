# 07 Deviation log

| ID | Date | Found during | Description | Root cause | Impact assessment | Resolution | Status |
|---|---|---|---|---|---|---|---|
| DEV-001 | 2026-09-24 | OQ dry run (test_frs11) | ALCOA+ "Consistent" check failed for a compliant batch: step 3 appeared to be observed after step 4. | A correction stored the **correction time** as the observation time, so a corrected earlier step looked newer than later steps. A correction changes *what* was recorded, not *when* it was observed. | Would have falsely flagged compliant batches and misrepresented observation times in the record (data integrity). No released records affected (found before first execution). | `correct_value` keeps the original `observed_at`; the correction time stays in `recorded_at` and the audit trail. Re-executed OQ: 12/12 pass. | Closed |

## How deviations are handled
1. Stop and record: what was expected, what happened, evidence (test log, screenshot, audit event id).
2. Assess impact on product quality and data integrity; decide whether testing can continue.
3. Find the root cause; fix; re-execute the affected tests **and** a regression run (`python -m tools.run_validation`).
4. Close only when the executed package shows the requirement passing.
