"""Operational Qualification (OQ) tests. Each test verifies one functional requirement (FRS-xx)
and is executed to produce the objective evidence in validation/executed/.
"""

from datetime import timedelta

import pytest
from sqlalchemy import update

from batchguard.alcoa import alcoa_report
from batchguard.models import AuditEvent, utcnow
from batchguard.services import (RuleViolation, authenticate, close_deviation, correct_value, current_entries,
                                 record_value, release_batch, release_blockers, sign, submit_for_review,
                                 verify_audit_chain)

GOOD = {1: 50.0, 2: 17, 3: 22, 4: 10, 5: 600}
PW = {"op1": "Operator#2026", "op2": "Operator#2026", "sup1": "Supervisor#2026", "qa1": "QualityA#2026"}


def _record_all(w, values=GOOD):
    return {seq: record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][seq].id, v) for seq, v in values.items()}


def _verify_critical(w, entries):
    for seq, step in w["steps"].items():
        if step.critical:
            sign(w["db"], w["users"]["sup1"], PW["sup1"], "step_entry", entries[seq].id, "verified")


@pytest.mark.frs("FRS-01")
def test_frs01_login_locks_after_three_failures(world):
    db = world["db"]
    assert authenticate(db, "op1", PW["op1"]).username == "op1"
    for _ in range(3):
        with pytest.raises(RuleViolation):
            authenticate(db, "op1", "wrong-password")
    with pytest.raises(RuleViolation, match="locked"):
        authenticate(db, "op1", PW["op1"])


@pytest.mark.frs("FRS-02")
def test_frs02_roles_are_enforced(world):
    w = world
    with pytest.raises(RuleViolation, match="not allowed"):
        record_value(w["db"], w["users"]["qa1"], w["batch"].id, w["steps"][1].id, 50.0)  # QA cannot record
    entries = _record_all(w)
    with pytest.raises(RuleViolation, match="not allowed"):
        sign(w["db"], w["users"]["op2"], PW["op2"], "step_entry", entries[1].id, "verified")  # operators cannot verify


@pytest.mark.frs("FRS-03")
def test_frs03_entries_are_attributable_and_contemporaneous(world):
    w = world
    e = record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][2].id, 17)
    assert e.recorded_by == w["users"]["op1"].id and e.recorded_at is not None
    with pytest.raises(RuleViolation, match="future"):
        record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][3].id, 22, observed_at=utcnow() + timedelta(hours=1))
    with pytest.raises(RuleViolation, match="contemporaneous"):
        record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][3].id, 22, observed_at=utcnow() - timedelta(hours=2))


@pytest.mark.frs("FRS-04")
def test_frs04_out_of_spec_value_raises_deviation(world):
    w = world
    record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][4].id, 14)  # hardness spec 8-12 kP
    blockers = release_blockers(w["db"], w["batch"].id)
    assert any("Deviation" in b and "Hardness" in b for b in blockers)


@pytest.mark.frs("FRS-05")
def test_frs05_corrections_keep_the_original_and_need_a_reason(world):
    w = world
    first = record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][2].id, 17)
    with pytest.raises(RuleViolation, match="already recorded"):
        record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][2].id, 18)
    with pytest.raises(RuleViolation, match="reason"):
        correct_value(w["db"], w["users"]["op1"], first.id, 18, "typo")
    new = correct_value(w["db"], w["users"]["op1"], first.id, 18, "Transcription error: timer showed 18 min")
    assert first.superseded_by == new.id and first.value == 17  # original preserved, not overwritten
    assert current_entries(w["db"], w["batch"].id)[w["steps"][2].id].value == 18


@pytest.mark.frs("FRS-06")
def test_frs06_signature_requires_password_and_records_name_time_meaning(world):
    w = world
    entries = _record_all(w)
    with pytest.raises(RuleViolation, match="password"):
        sign(w["db"], w["users"]["sup1"], "wrong", "step_entry", entries[1].id, "verified")
    sig = sign(w["db"], w["users"]["sup1"], PW["sup1"], "step_entry", entries[1].id, "verified")
    assert sig.printed_name == "Meera Supervisor" and sig.meaning == "verified" and sig.signed_at is not None


@pytest.mark.frs("FRS-07")
def test_frs07_two_person_rule(world):
    w = world
    e = record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][1].id, 50.0)
    e.recorded_by = w["users"]["sup1"].id  # simulate a supervisor who recorded the value themself
    with pytest.raises(RuleViolation, match="Two-person"):
        sign(w["db"], w["users"]["sup1"], PW["sup1"], "step_entry", e.id, "verified")


@pytest.mark.frs("FRS-08")
def test_frs08_release_blocked_until_complete_verified_and_deviations_closed(world):
    w = world
    db, sup, qa = w["db"], w["users"]["sup1"], w["users"]["qa1"]
    with pytest.raises(RuleViolation, match="not recorded"):
        submit_for_review(db, sup, PW["sup1"], w["batch"].id)
    entries = _record_all(w, {**GOOD, 4: 13})  # hardness out of spec -> deviation
    with pytest.raises(RuleViolation, match="not verified"):
        submit_for_review(db, sup, PW["sup1"], w["batch"].id)
    _verify_critical(w, entries)
    submit_for_review(db, sup, PW["sup1"], w["batch"].id)
    with pytest.raises(RuleViolation, match="Deviation"):
        release_batch(db, qa, PW["qa1"], w["batch"].id)
    dev_id = int(release_blockers(db, w["batch"].id)[0].split("#")[1].split()[0])
    close_deviation(db, qa, PW["qa1"], dev_id, "Retest of 20 tablets within spec; tester calibration drift, CAPA-12 raised")
    assert release_batch(db, qa, PW["qa1"], w["batch"].id).status == "released"


@pytest.mark.frs("FRS-09")
def test_frs09_audit_trail_detects_tampering(world):
    w = world
    _record_all(w)
    assert verify_audit_chain(w["db"]) == (True, None)
    target = w["db"].query(AuditEvent).filter(AuditEvent.action == "record_value").first()
    w["db"].execute(update(AuditEvent).where(AuditEvent.id == target.id).values(reason="edited later"))
    w["db"].expire_all()
    intact, broken_at = verify_audit_chain(w["db"])
    assert not intact and broken_at == target.id


@pytest.mark.frs("FRS-10")
def test_frs10_released_batch_is_locked(world):
    w = world
    db = w["db"]
    entries = _record_all(w)
    _verify_critical(w, entries)
    submit_for_review(db, w["users"]["sup1"], PW["sup1"], w["batch"].id)
    release_batch(db, w["users"]["qa1"], PW["qa1"], w["batch"].id)
    with pytest.raises(RuleViolation, match="locked"):
        correct_value(db, w["users"]["op1"], entries[2].id, 18, "Attempted change after release")


@pytest.mark.frs("FRS-11")
def test_frs11_alcoa_report(world):
    w = world
    entries = _record_all(w)
    correct_value(w["db"], w["users"]["op1"], entries[3].id, 23, "Thermometer re-read after stabilising")
    report = {r["principle"]: r for r in alcoa_report(w["db"], w["batch"].id)}
    assert set(report) == {"Attributable", "Legible", "Contemporaneous", "Original", "Accurate", "Complete",
                           "Consistent", "Enduring", "Available"}
    assert all(r["status"] == "pass" for r in report.values())
    assert "1 original value(s) preserved" in report["Original"]["detail"]


@pytest.mark.frs("FRS-12")
def test_frs12_deviation_closure_needs_qa_signature_and_summary(world):
    w = world
    record_value(w["db"], w["users"]["op1"], w["batch"].id, w["steps"][5].id, 650)  # weight out of spec
    dev_id = int(release_blockers(w["db"], w["batch"].id)[-1].split("#")[1].split()[0])
    with pytest.raises(RuleViolation, match="not allowed"):
        close_deviation(w["db"], w["users"]["sup1"], PW["sup1"], dev_id, "Supervisor tries to close it themself")
    with pytest.raises(RuleViolation, match="summary"):
        close_deviation(w["db"], w["users"]["qa1"], PW["qa1"], dev_id, "ok")
    with pytest.raises(RuleViolation, match="password"):
        close_deviation(w["db"], w["users"]["qa1"], "bad", dev_id, "Punch wear confirmed; tooling replaced, batch retested")
    dev = close_deviation(w["db"], w["users"]["qa1"], PW["qa1"], dev_id, "Punch wear confirmed; tooling replaced, batch retested")
    assert dev.status == "closed"
