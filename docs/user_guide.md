# User guide: BatchGuard

## Roles at a glance
| Role | Can | Cannot |
|---|---|---|
| Operator | Record step values, correct own entries (with reason), raise deviations | Verify, submit, release, close deviations |
| Supervisor | Create batches, verify critical steps, correct entries, submit for QA review | Record values, release, close deviations |
| QA | Verify critical steps, close deviations, release batches | Record values, create or submit batches |

## Operator: recording a step
1. Open the batch from **Batches**.
2. In the step's row, type the measured value and click **Record**. The value is stamped with your name and the server time.
3. If the value is outside the specification, it turns red and a deviation is created automatically. Tell your supervisor.
4. Made a mistake? Open **Correct**, enter the right value and a reason (at least 10 characters), then **Save**. The original value stays visible under "earlier values".

> Record values as you work. Entries more than 30 minutes after the observation are refused; raise a deviation instead.

## Supervisor: verifying and submitting
1. For each step marked **critical**, check the value, enter your password next to **Verify**, and click it. You cannot verify an entry you recorded yourself.
2. When every step is recorded and every critical step verified, enter your password under **Review and release** and click **Submit for QA review**.

## QA: deviations and release
1. Under **Deviations**, write the investigation summary (root cause, impact, action; at least 20 characters), enter your password, and click **Close**.
2. When **Release blocked** shows nothing, enter your password and click **Release batch**. You cannot release a batch you submitted.
3. Check **ALCOA+ report** and **Audit trail** before releasing; the audit trail should show "intact".

## Messages you may see
| Message | Meaning | What to do |
|---|---|---|
| "Two-person rule…" | You tried to verify/release your own work | Ask a colleague |
| "…not contemporaneous…" | Entry too late | Raise a deviation describing what happened |
| "Release blocked: …" | Something is missing or open | Fix each listed item |
| "Account is locked" | 3 failed logins | Contact an administrator |
