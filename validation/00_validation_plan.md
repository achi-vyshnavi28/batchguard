# 00 Validation plan: BatchGuard eBR v1.0.0

## 1. Purpose and scope
Demonstrate that BatchGuard, an electronic batch record system, is fit for its intended use and meets 21 CFR Part 11
and EU GMP Annex 11 expectations for electronic records and signatures. In scope: user access, batch execution,
corrections, e-signatures, deviations, review and release, audit trail, ALCOA+ reporting.
Out of scope: infrastructure qualification of a production host, backup/restore, and interfaces to ERP/LIMS (none exist).

> BatchGuard is a portfolio demonstration. The documents follow real CSV practice, but the system is not used for GMP manufacturing.

## 2. Approach (GAMP 5, 2nd edition + FDA CSA)
- **Category 5** (custom application): full life cycle, with specifications, risk assessment and scripted testing for high-risk functions.
- **Risk-based effort** (`03_risk_assessment.md`): high-risk requirements get scripted automated tests with negative cases; medium risk gets scripted positive tests.
- **Automated, repeatable execution**: `python -m tools.run_validation` executes IQ, OQ and PQ and writes a timestamped executed package with raw evidence.

## 3. Deliverables
| # | Document | Status |
|---|---|---|
| 00 | Validation plan | this document |
| 01 | URS (user requirements) | generated from `requirements.yaml` |
| 02 | FRS (functional requirements) | generated from `requirements.yaml` |
| 03 | Risk assessment | written |
| 04 | IQ protocol | written; executed automatically |
| 05 | OQ protocol | written; executed automatically (`tests/test_oq.py`) |
| 06 | PQ protocol | written; executed automatically (`tests/test_web.py`) |
| 07 | Deviation log | written |
| 08 | Executed package + traceability matrix | `validation/executed/<timestamp>/` |
| — | Release notes, user guide, configuration guide | `docs/` |

## 4. Roles
| Role | Responsibility |
|---|---|
| System owner / author | Specifications, protocols, execution (Vyshnavi Achi) |
| QA reviewer | Review and approve protocols and the executed package (reviewer to be assigned) |

## 5. Acceptance criteria
All IQ checks pass; all OQ and PQ tests pass; every FRS is covered by at least one passing test;
every deviation is documented with root cause, impact, and resolution before release.
