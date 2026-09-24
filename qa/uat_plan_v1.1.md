# UAT plan: BatchGuard 1.1 (cleaning log and batch rejection)

| Item | Detail |
|---|---|
| Goal | Users confirm 1.1 supports their real process before release |
| Participants | 1 operator, 1 production supervisor, 1 QA reviewer (customer site) + product ops (facilitator) |
| Environment | UAT instance with seeded data: 2 products, 4 equipment items (1 with expired cleaning), 3 batches in different states |
| Entry criteria | OQ for 1.1 passed; all *high* spec gaps from `spec_review_v1.1.md` answered; test library v1.1 reviewed |
| Exit criteria | All scenarios pass or have an accepted deviation; no open S1/S2 bugs; sign-off below |

## Scenarios
| ID | Role | Scenario | Expected | Result | Tester / date | Bug |
|---|---|---|---|---|---|---|
| UAT-01 | Operator | Record a major cleaning of Blender BL-02 and sign | Record shows name, time, type; supervisor task created | | | |
| UAT-02 | Supervisor | Verify the major cleaning | Verification signature shown; equipment status "clean" | | | |
| UAT-03 | Supervisor | Start a batch on Granulator GR-01 (cleaning expired) | Blocked with message naming the equipment and expiry time | | | |
| UAT-04 | QA | Override the cleaning block *(pending gap GAP on US-104)* | Only with reason + e-signature; audit entry created | | | |
| UAT-05 | QA | Reject a batch in review with a reason | Status "rejected"; locked; audit entry; appears in reports | | | |
| UAT-06 | Operator | Try to reject a batch | Refused (QA only) | | | |
| UAT-07 | QA manager | Open the cleaning report | Shows cleanings for agreed filters *(pending gap on US-105)* | | | |
| UAT-08 | Any | Exploratory: 20 minutes of "try to break it" per role | Findings logged as bugs | | | |

## Bug severity
S1 blocks the process or risks data integrity · S2 wrong result with workaround · S3 minor · S4 cosmetic.

## Sign-off
| Role | Name | Decision (accept / accept with deviations / reject) | Signature | Date |
|---|---|---|---|---|
| Customer QA | | | | |
| Customer production | | | | |
| Product (Leucine side) | | | | |
