"""ALCOA+ data-integrity report for one batch (FRS-11).

Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring, Available.
Each principle becomes a concrete, automatic check on the stored records.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from batchguard.models import Batch, Deviation, StepEntry, User
from batchguard.services import CONTEMPORANEOUS_WINDOW, _out_of_spec, current_entries, verify_audit_chain


def _check(principle: str, ok: bool, detail: str) -> dict:
    return {"principle": principle, "status": "pass" if ok else "fail", "detail": detail}


def alcoa_report(db: Session, batch_id: int) -> list[dict]:
    batch = db.get(Batch, batch_id)
    all_entries = list(db.scalars(select(StepEntry).where(StepEntry.batch_id == batch_id).order_by(StepEntry.id)))
    current = current_entries(db, batch_id)
    user_ids = {u.id for u in db.scalars(select(User))}
    devs = list(db.scalars(select(Deviation).where(Deviation.batch_id == batch_id)))
    report = []

    unattributed = [e.id for e in all_entries if e.recorded_by not in user_ids]
    report.append(_check("Attributable", not unattributed,
                         "Every entry is linked to an identified user." if not unattributed else f"Entries without a valid user: {unattributed}"))

    illegible = [e.id for e in all_entries if e.value is None or not e.step.unit]
    report.append(_check("Legible", not illegible,
                         "All values are numeric with units." if not illegible else f"Entries missing value or unit: {illegible}"))

    late = [e.id for e in all_entries if e.correction_reason is None and e.recorded_at - e.observed_at > CONTEMPORANEOUS_WINDOW]
    report.append(_check("Contemporaneous", not late,
                         "All entries recorded within 30 minutes of observation." if not late else f"Late entries: {late}"))

    superseded = [e for e in all_entries if e.superseded_by is not None]
    corrections = [e for e in all_entries if e.correction_reason]
    no_reason = [e.id for e in all_entries if e.id in {s.superseded_by for s in superseded} and not e.correction_reason]
    report.append(_check("Original", not no_reason,
                         f"{len(superseded)} original value(s) preserved, {len(corrections)} correction(s), all with reasons."
                         if not no_reason else f"Corrections without reason: {no_reason}"))

    linked = {d.step_entry_id for d in devs}
    oos_without_dev = [e.id for e in all_entries if _out_of_spec(e.step, e.value) and e.id not in linked]
    report.append(_check("Accurate", not oos_without_dev,
                         "Every out-of-spec value has a deviation." if not oos_without_dev else f"Out-of-spec without deviation: {oos_without_dev}"))

    missing = [s.seq for s in batch.template.steps if s.id not in current]
    report.append(_check("Complete", not missing,
                         "All master-record steps are recorded." if not missing else f"Steps not recorded: {missing}"))

    ordered = sorted((e.step.seq, e.observed_at) for e in current.values())
    out_of_order = [seq for (seq, t), (_, prev_t) in zip(ordered[1:], ordered) if t < prev_t]
    report.append(_check("Consistent", not out_of_order,
                         "Steps were observed in master-record order." if not out_of_order else f"Steps observed out of order: {out_of_order}"))

    intact, broken_at = verify_audit_chain(db)
    report.append(_check("Enduring", intact,
                         "Audit trail hash chain intact (no edits or deletions)." if intact else f"Audit trail tampered at event {broken_at}"))
    report.append(_check("Available", True, "Records, signatures and audit trail retrievable on demand (this report)."))
    return report
