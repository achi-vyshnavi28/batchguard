# 01 User Requirements Specification (URS)

System: BatchGuard electronic batch record (eBR) v1.0.0 · GAMP 5 category 5

Intended use: Record the execution of tablet-manufacturing batches against an approved master batch record, capture electronic signatures, manage deviations, and support QA release decisions. Demonstration system; not used for commercial GMP manufacturing.

Risk: high = direct impact on product quality, patient safety or data integrity.

| ID | Requirement | Risk |
|---|---|---|
| URS-01 | Only authorised, identified users can access the system. | high |
| URS-02 | Users can only perform actions permitted for their role. | high |
| URS-03 | Every recorded value shows who recorded it and when, at the time it was observed. | high |
| URS-04 | Values outside the approved specification are flagged and investigated. | high |
| URS-05 | Original records are never lost; corrections are justified and visible. | high |
| URS-06 | Electronic signatures are legally equivalent to handwritten ones (21 CFR 11.50, 11.100, 11.200). | high |
| URS-07 | Critical steps are independently verified by a second person. | high |
| URS-08 | A batch cannot be released while the record is incomplete or deviations are open. | high |
| URS-09 | All GMP-relevant actions are captured in a secure, tamper-evident audit trail (21 CFR 11.10(e)). | high |
| URS-10 | Released records cannot be changed. | high |
| URS-11 | Data integrity can be reviewed against ALCOA+ principles per batch. | medium |
| URS-12 | Deviations are closed only by QA with a documented investigation. | high |
