# Executed validation report: BatchGuard electronic batch record (eBR) v1.0.0

| Item | Value |
|---|---|
| Executed (UTC) | 2026-09-25T13:13:50+00:00 |
| Executed by | Achi-Vyshnavi |
| Code version | git commit `b20721c` |
| Environment | Windows-11-10.0.26200-SP0, Python 3.12.8 |
| GAMP 5 category | 5 (custom application) |
| Intended use | Record the execution of tablet-manufacturing batches against an approved master batch record, capture electronic signatures, manage deviations, and support QA release decisions. Demonstration system; not used for commercial GMP manufacturing. |

## 1. Installation Qualification (IQ)
| ID | Check | Expected | Actual | Result | Executed (UTC) |
|---|---|---|---|---|---|
| IQ-01 | Python runtime version | 3.12.x | 3.12.8 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.fastapi | Package fastapi installed at pinned version | 0.141.1 | 0.141.1 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.httpx | Package httpx installed at pinned version | 0.28.1 | 0.28.1 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.itsdangerous | Package itsdangerous installed at pinned version | 2.2.0 | 2.2.0 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.Jinja2 | Package Jinja2 installed at pinned version | 3.1.6 | 3.1.6 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.pytest | Package pytest installed at pinned version | 9.1.1 | 9.1.1 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.python-multipart | Package python-multipart installed at pinned version | 0.0.32 | 0.0.32 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.PyYAML | Package PyYAML installed at pinned version | 6.0.3 | 6.0.3 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.SQLAlchemy | Package SQLAlchemy installed at pinned version | 2.0.54 | 2.0.54 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.uvicorn | Package uvicorn installed at pinned version | 0.53.0 | 0.53.0 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.playwright | Package playwright installed at pinned version | 1.63.0 | 1.63.0 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.pytest-playwright | Package pytest-playwright installed at pinned version | 0.9.0 | 0.9.0 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.openpyxl | Package openpyxl installed at pinned version | 3.1.5 | 3.1.5 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-02.python-dotenv | Package python-dotenv installed at pinned version | 1.2.3 | 1.2.3 | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-03 | Database schema created | audit_trail, batches, deviations, signatures, step_entries, template_steps, templates, users | audit_trail, batches, deviations, signatures, step_entries, template_steps, templates, users | PASS | 2026-09-25T13:13:50+00:00 |
| IQ-04 | Master batch record and demo users load | 5 steps, 4 users | 5 steps, 4 users | PASS | 2026-09-25T13:13:51+00:00 |
| IQ-05 | UI templates present | alcoa.html, audit.html, base.html, batch.html, home.html, login.html | alcoa.html, audit.html, base.html, batch.html, home.html, login.html | PASS | 2026-09-25T13:13:51+00:00 |

## 2. Operational Qualification (OQ)
Each test exercises one functional requirement, including negative cases (wrong role, wrong password, missing reason, tampering).

| Test | FRS | Result | Duration (s) | Error |
|---|---|---|---|---|
| test_frs01_login_locks_after_three_failures | FRS-01 | PASS | 0.533 |  |
| test_frs02_roles_are_enforced | FRS-02 | PASS | 0.114 |  |
| test_frs03_entries_are_attributable_and_contemporaneous | FRS-03 | PASS | 0.003 |  |
| test_frs04_out_of_spec_value_raises_deviation | FRS-04 | PASS | 0.006 |  |
| test_frs05_corrections_keep_the_original_and_need_a_reason | FRS-05 | PASS | 0.004 |  |
| test_frs06_signature_requires_password_and_records_name_time_meaning | FRS-06 | PASS | 0.198 |  |
| test_frs07_two_person_rule | FRS-07 | PASS | 0.093 |  |
| test_frs08_release_blocked_until_complete_verified_and_deviations_closed | FRS-08 | PASS | 0.606 |  |
| test_frs09_audit_trail_detects_tampering | FRS-09 | PASS | 0.008 |  |
| test_frs10_released_batch_is_locked | FRS-10 | PASS | 0.523 |  |
| test_frs11_alcoa_report | FRS-11 | PASS | 0.013 |  |
| test_frs12_deviation_closure_needs_qa_signature_and_summary | FRS-12 | PASS | 0.198 |  |

## 3. Performance Qualification (PQ)
End-to-end batch lifecycle through the web UI by three users (operator, supervisor, QA): HTTP-level tests
(`tests/test_web.py`) and real-browser tests (`tests/ui/`, Playwright/Chromium) with screenshot evidence.

| Test | FRS | Result | Duration (s) | Error |
|---|---|---|---|---|
| test_pq_full_batch_lifecycle | FRS-08 | PASS | 1.701 |  |
| test_ui_blocks_actions_outside_role | FRS-02 | PASS | 0.701 |  |
| test_unauthenticated_users_are_redirected | FRS-01 | PASS | 0.428 |  |
| test_pq_ui_batch_lifecycle_with_screenshots[chromium] | FRS-08 | PASS | 4.166 |  |
| test_pq_ui_lockout_after_three_failed_logins[chromium] | FRS-01 | PASS | 0.895 |  |

### Screenshot evidence (`evidence/`)
- `batch_lifecycle_with_screenshots__01_batch_created.png`
- `batch_lifecycle_with_screenshots__02_values_recorded_oos_flagged.png`
- `batch_lifecycle_with_screenshots__03_critical_steps_verified.png`
- `batch_lifecycle_with_screenshots__04_release_blocked_by_deviation.png`
- `batch_lifecycle_with_screenshots__05_batch_released.png`
- `batch_lifecycle_with_screenshots__06_alcoa_report_9_of_9.png`
- `batch_lifecycle_with_screenshots__07_audit_trail_intact.png`
- `lockout_after_three_failed_logins__01_account_locked.png`

## 4. Requirements traceability matrix (URS → FRS → test → result)
| URS | Risk | FRS | Verified by | Result |
|---|---|---|---|---|
| URS-01 | high | FRS-01 | test_frs01_login_locks_after_three_failures, test_unauthenticated_users_are_redirected, test_pq_ui_lockout_after_three_failed_logins[chromium] | pass |
| URS-02 | high | FRS-02 | test_frs02_roles_are_enforced, test_ui_blocks_actions_outside_role | pass |
| URS-03 | high | FRS-03 | test_frs03_entries_are_attributable_and_contemporaneous | pass |
| URS-04 | high | FRS-04 | test_frs04_out_of_spec_value_raises_deviation | pass |
| URS-05 | high | FRS-05 | test_frs05_corrections_keep_the_original_and_need_a_reason | pass |
| URS-06 | high | FRS-06 | test_frs06_signature_requires_password_and_records_name_time_meaning | pass |
| URS-07 | high | FRS-07 | test_frs07_two_person_rule | pass |
| URS-08 | high | FRS-08 | test_frs08_release_blocked_until_complete_verified_and_deviations_closed, test_pq_full_batch_lifecycle, test_pq_ui_batch_lifecycle_with_screenshots[chromium] | pass |
| URS-09 | high | FRS-09 | test_frs09_audit_trail_detects_tampering | pass |
| URS-10 | high | FRS-10 | test_frs10_released_batch_is_locked | pass |
| URS-11 | medium | FRS-11 | test_frs11_alcoa_report | pass |
| URS-12 | high | FRS-12 | test_frs12_deviation_closure_needs_qa_signature_and_summary | pass |

## 5. Summary
- IQ: 17/17 passed
- OQ: 12/12 passed
- PQ: 5/5 passed
- Requirements without a test: none
- Deviations raised during validation: see `validation/07_deviation_log.md`

## 6. Conclusion
All acceptance criteria met. The system is fit for its intended (demonstration) use.

Raw evidence: `test_log.txt` (full pytest output), `results.json`, `evidence/*.png` (UI screenshots).
