# 04–06 IQ, OQ and PQ protocols

All three are executed by one command so results are repeatable and every run leaves dated evidence:

```bash
python -m tools.run_validation
```

## 04 Installation Qualification (IQ)
**Objective:** confirm the system is installed as specified.
| ID | Check | Acceptance criterion |
|---|---|---|
| IQ-01 | Python runtime | 3.12.x |
| IQ-02.* | Each dependency | Installed version equals the pin in `requirements.txt` |
| IQ-03 | Database schema | All 8 tables created |
| IQ-04 | Configuration data | Master batch record (5 steps) and 4 role users load |
| IQ-05 | UI components | All 6 page templates present |

## 05 Operational Qualification (OQ)
**Objective:** confirm each function works as specified, including when users do the wrong thing.
Script: `tests/test_oq.py`. One test per FRS; each includes the negative cases from the risk assessment.

| Test | FRS | Key steps and expected result |
|---|---|---|
| test_frs01 | FRS-01 | 3 wrong passwords → account locked; correct password then refused |
| test_frs02 | FRS-02 | QA tries to record → refused; operator tries to verify → refused |
| test_frs03 | FRS-03 | Entry stores user + server time; future time refused; entry 2 h late refused |
| test_frs04 | FRS-04 | Hardness 14 kP (spec 8–12) → deviation raised and blocks release |
| test_frs05 | FRS-05 | Second recording refused; correction without reason refused; correction keeps original value |
| test_frs06 | FRS-06 | Wrong password → signature refused; manifest shows name, time, meaning |
| test_frs07 | FRS-07 | Recorder verifying own entry → refused |
| test_frs08 | FRS-08 | Submit refused while incomplete/unverified; release refused with open deviation; release succeeds after QA closure |
| test_frs09 | FRS-09 | Audit event edited directly in the database → chain verification reports that event |
| test_frs10 | FRS-10 | Correction after release → refused |
| test_frs11 | FRS-11 | All nine ALCOA+ checks pass for a compliant batch; correction counted as preserved original |
| test_frs12 | FRS-12 | Supervisor closure refused; short summary refused; wrong password refused; QA closure succeeds |

## 06 Performance Qualification (PQ)
**Objective:** confirm the system supports the real business process end to end, through the user interface.
Script: `tests/test_web.py`.
| Test | Scenario | Expected |
|---|---|---|
| test_pq_full_batch_lifecycle | Supervisor creates batch → operator records 5 steps (one out of spec) → supervisor verifies 3 critical steps and submits → QA release blocked by deviation → QA closes deviation → QA releases | Batch released; ALCOA+ 9/9 pass; audit chain intact |
| test_ui_blocks_actions_outside_role | Supervisor records a value; operator creates a batch | Both refused with a clear message |
| test_unauthenticated_users_are_redirected | Anonymous user opens batches and audit trail | Redirected to login |
