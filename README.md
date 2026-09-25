# BatchGuard: electronic batch record with a full CSV validation package

A small, working **electronic batch record (eBR)** for tablet manufacturing, built to 21 CFR Part 11 and ALCOA+ expectations,
and **validated like a GxP system**: URS → FRS → risk assessment → IQ/OQ/PQ executed with evidence → traceability matrix → deviation log.

> Portfolio demonstration. Documents follow real Computer System Validation (CSV/CSA) practice; not used for GMP manufacturing.

## What it enforces
| Regulation / principle | How |
|---|---|
| Part 11 §11.10(e) audit trail | Append-only, SHA-256 hash-chained; any edit is detected and shown |
| Part 11 §11.50 / §11.200 e-signatures | Password re-entry at signing; printed name, UTC time, meaning |
| Part 11 §11.10(d) access control | Roles, account lockout after 3 failures, 15-min session timeout |
| ALCOA+ | Per-batch report with nine automatic checks |
| GMP second-person verification | Recorder ≠ verifier; reviewer ≠ releaser |
| Release gating | Blocked while steps missing, unverified, or deviations open |

## Validation package (`validation/`)
| Doc | |
|---|---|
| 00 Validation plan | Scope, GAMP 5 category 5, CSA risk-based approach, acceptance criteria |
| 01 URS / 02 FRS | Generated from one source (`requirements.yaml`) |
| 03 Risk assessment | Severity × probability × detectability per function, driving test depth |
| 04–06 IQ / OQ / PQ protocols | Steps and acceptance criteria |
| 07 Deviation log | Includes a real deviation found during OQ, with root cause and fix |
| `executed/<timestamp>/` | Executed report, traceability matrix, raw test log |

Latest execution: **IQ 17/17 · OQ 12/12 · PQ 5/5 (2 of them real-browser Playwright runs with screenshot evidence) · 12/12 requirements traced to passing tests.**

## Testing beyond the protocols
| Layer | Tool | What it proves |
|---|---|---|
| Unit / OQ | pytest | Each FRS requirement, tagged and traced |
| UI / PQ | Playwright | Operator → supervisor → QA flow in a real browser; screenshots saved as objective evidence |
| API | Postman + Newman | 14 requests, 24 assertions on `/api/v1` (auth, roles, 401/403/422 contracts, audit-chain check); see `postman/` |
| Data | SQL | Product questions (right-first-time, deviation hot spots, review cycle time) in `qa/product_questions.sql` |

## Product work: release 1.1 (cleaning log + batch rejection)
- **PRD** `docs/prd/PRD-1.1_cleaning_log_and_rejection.md`, reviewed by **SpecCheck** (`python -m speccheck`): lints vague or untestable
  requirements and missing GxP controls, drafts test cases with Gemini, and exports a versioned **Excel test library**,
  a **Jira import CSV** and a spec review (`qa/`). The gaps became the live Jira backlog; 4 were closed by the
  spec-review decisions.
  SpecCheck has since become its own project, **[github.com/achi-vyshnavi28/speccheck](https://github.com/achi-vyshnavi28/speccheck)**,
  with more rules, a web app, traceability, and a held-out evaluation (rules 90% precision; rules + LLM 100% recall).
- All documents in one place: [Notion workspace](https://app.notion.com/p/BatchGuard-eBR-validation-and-product-docs-3e58d914640c81ca9175c726b9da7547)
- UAT plan, spec-review meeting notes, enablement one-pager, competitor teardown (`qa/`, `docs/product/`)
- **Wireframes**: 6 screens in Figma ([BatchGuard wireframes](https://www.figma.com/design/r25fpOdui1TT7TynBe7snc/Wireframes--BatchGuard--RootCause--SpecCheck?node-id=0-1)),
  generated from `design/make_wireframes.py` (SVG sources in `design/wireframes/`)

## Run it
```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn batchguard.web:app            # http://localhost:8000
python -m tools.run_validation         # executes IQ/OQ/PQ, writes the executed package
```
Demo users: `op1` / `op2` (operator, `Operator#2026`), `sup1` (supervisor, `Supervisor#2026`), `qa1` (QA, `QualityA#2026`).

## Docs
[Release notes](docs/release_notes.md) · [User guide](docs/user_guide.md) · [Configuration guide](docs/configuration_guide.md)
