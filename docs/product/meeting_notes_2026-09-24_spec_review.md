# Spec review: PRD 1.1 (cleaning log and rejection)

**Date:** 2026-09-24 · **Attendees:** APM, product ops, engineering lead, QA SME · **Input:** `qa/spec_review_v1.1.md`

> Illustrative example of the format: attendees and decisions are a worked example, not a real meeting.

## Decisions
1. US-104 override **requires QA role + reason (≥ 20 chars) + e-signature + audit entry**. "As needed" removed.
2. Cleaning validity (US-102) counts **from the end of cleaning**; 72 h default, configurable per equipment.
3. US-103: "quickly / user-friendly" replaced by: rejection completes in ≤ 3 clicks after sign dialog; p95 response < 2 s.

## Action items
| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| 1 | Update PRD 1.1 with decisions 1–3 and re-run SpecCheck (target: 0 high gaps) | APM | 26 Sep | Open |
| 2 | Define "since its last use" for US-102 (batch start vs batch end) with QA SME | APM + QA SME | 26 Sep | Open |
| 3 | Decide report filters for US-105 (date range, equipment, status?) | APM | 29 Sep | Open |
| 4 | Add override and rejection to the FRS + risk assessment; draft OQ cases | Product ops | 30 Sep | Open |
| 5 | Update enablement one-pager once 1–3 are closed | Product ops | 1 Oct | Open |

## Parking lot
Should rejected batches support a formal "rework" path? (Out of scope for 1.1.)
