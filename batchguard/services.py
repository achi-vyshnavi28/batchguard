"""Business rules. Each rule is tagged with the functional requirement it implements (FRS-xx),
which the tests reference too, so the traceability matrix can be generated automatically.
"""

import json
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from batchguard.models import AuditEvent, Batch, Deviation, Signature, StepEntry, Template, TemplateStep, User, utcnow
from batchguard.security import GENESIS, chain_hash, hash_password, verify_password

MAX_FAILED_LOGINS = 3
CONTEMPORANEOUS_WINDOW = timedelta(minutes=30)
MEANINGS = {"performed", "verified", "reviewed", "approved_release", "closed"}
PERMISSIONS = {  # FRS-02
    "record": {"operator"},
    "correct": {"operator", "supervisor"},
    "verify": {"supervisor", "qa"},
    "raise_deviation": {"operator", "supervisor", "qa"},
    "close_deviation": {"qa"},
    "submit_review": {"supervisor"},
    "release": {"qa"},
    "create_batch": {"supervisor"},
}


class RuleViolation(Exception):
    """Raised when an action would break a GxP rule. The message is shown to the user and audited."""


# ---------- audit trail (FRS-09) ----------
def audit(db: Session, user: User | None, action: str, entity: str, entity_id: int | None,
          before: dict | None = None, after: dict | None = None, reason: str | None = None) -> AuditEvent:
    # Store exactly what will be hashed: JSON-safe copies (datetimes become strings).
    before, after = (json.loads(json.dumps(x, default=str)) if x is not None else None for x in (before, after))
    last = db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(1)).first()
    prev = last.hash if last else GENESIS
    at = utcnow()
    username = user.username if user else "system"
    payload = {"at": at, "username": username, "action": action, "entity": entity, "entity_id": entity_id,
               "before": before, "after": after, "reason": reason}
    event = AuditEvent(at=at, username=username, action=action, entity=entity, entity_id=entity_id,
                       before=before, after=after, reason=reason, prev_hash=prev, hash=chain_hash(prev, payload))
    db.add(event)
    db.flush()
    return event


def verify_audit_chain(db: Session) -> tuple[bool, int | None]:
    """Recompute every hash. Returns (intact, id of first broken event)."""
    prev = GENESIS
    for e in db.scalars(select(AuditEvent).order_by(AuditEvent.id)):
        payload = {"at": e.at, "username": e.username, "action": e.action, "entity": e.entity, "entity_id": e.entity_id,
                   "before": e.before, "after": e.after, "reason": e.reason}
        if e.prev_hash != prev or e.hash != chain_hash(prev, payload):
            return False, e.id
        prev = e.hash
    return True, None


# ---------- users (FRS-01, FRS-02) ----------
def create_user(db: Session, username: str, full_name: str, role: str, password: str, by: User | None = None) -> User:
    if len(password) < 8:
        raise RuleViolation("Password must be at least 8 characters.")
    user = User(username=username, full_name=full_name, role=role, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    audit(db, by, "create_user", "user", user.id, after={"username": username, "role": role})
    return user


def authenticate(db: Session, username: str, password: str) -> User:
    user = db.scalars(select(User).where(User.username == username)).first()
    if user is None:
        raise RuleViolation("Invalid username or password.")
    if not user.active:
        raise RuleViolation("Account is locked. Contact an administrator.")
    if not verify_password(password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= MAX_FAILED_LOGINS:
            user.active = False
            audit(db, user, "account_locked", "user", user.id, reason=f"{MAX_FAILED_LOGINS} failed logins")
        else:
            audit(db, user, "login_failed", "user", user.id)
        raise RuleViolation("Invalid username or password.")
    user.failed_logins = 0
    audit(db, user, "login", "user", user.id)
    return user


def require(user: User, permission: str) -> None:
    if user.role not in PERMISSIONS[permission]:
        raise RuleViolation(f"Role '{user.role}' is not allowed to {permission.replace('_', ' ')}.")


# ---------- batches ----------
def _batch(db: Session, batch_id: int) -> Batch:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise RuleViolation("Batch not found.")
    return batch


def _require_editable(batch: Batch) -> None:  # FRS-10
    if batch.status in ("released", "rejected"):
        raise RuleViolation(f"Batch {batch.batch_no} is {batch.status} and locked against changes.")


def create_batch(db: Session, user: User, template_id: int, batch_no: str) -> Batch:
    require(user, "create_batch")
    batch = Batch(batch_no=batch_no, template_id=template_id, created_by=user.id)
    db.add(batch)
    db.flush()
    audit(db, user, "create_batch", "batch", batch.id, after={"batch_no": batch_no, "template_id": template_id})
    return batch


def current_entries(db: Session, batch_id: int) -> dict[int, StepEntry]:
    """Latest (non-superseded) entry per template step."""
    rows = db.scalars(select(StepEntry).where(StepEntry.batch_id == batch_id, StepEntry.superseded_by.is_(None)))
    return {e.step_id: e for e in rows}


def _out_of_spec(step: TemplateStep, value: float) -> bool:
    return (step.min_value is not None and value < step.min_value) or (step.max_value is not None and value > step.max_value)


def record_value(db: Session, user: User, batch_id: int, step_id: int, value: float,
                 observed_at: datetime | None = None) -> StepEntry:
    """FRS-03 attributable + contemporaneous; FRS-04 out-of-spec raises a deviation."""
    require(user, "record")
    batch = _batch(db, batch_id)
    _require_editable(batch)
    if batch.status != "in_progress":
        raise RuleViolation("Values can only be recorded while the batch is in progress.")
    step = db.get(TemplateStep, step_id)
    if step is None or step.template_id != batch.template_id:
        raise RuleViolation("Step does not belong to this batch's master record.")
    if step_id in current_entries(db, batch_id):
        raise RuleViolation("A value is already recorded for this step. Use a correction with a reason.")
    now = utcnow()
    observed_at = observed_at or now
    if observed_at > now + timedelta(minutes=1):
        raise RuleViolation("Observation time cannot be in the future.")
    if now - observed_at > CONTEMPORANEOUS_WINDOW:
        raise RuleViolation("Entry is not contemporaneous (more than 30 minutes late). Record a deviation instead.")
    entry = StepEntry(batch_id=batch_id, step_id=step_id, value=value, observed_at=observed_at, recorded_by=user.id)
    db.add(entry)
    db.flush()
    audit(db, user, "record_value", "step_entry", entry.id, after={"step": step.parameter, "value": value, "unit": step.unit})
    if _out_of_spec(step, value):
        raise_deviation(db, None, batch_id, f"{step.parameter} = {value} {step.unit} outside "
                        f"[{step.min_value}, {step.max_value}] {step.unit}", severity="major", step_entry_id=entry.id)
    return entry


def correct_value(db: Session, user: User, entry_id: int, new_value: float, reason: str) -> StepEntry:
    """FRS-05: never overwrite. The original stays visible; the new entry supersedes it."""
    require(user, "correct")
    if not reason or len(reason.strip()) < 10:
        raise RuleViolation("A correction needs a reason of at least 10 characters.")
    old = db.get(StepEntry, entry_id)
    if old is None or old.superseded_by is not None:
        raise RuleViolation("Only the current entry can be corrected.")
    batch = _batch(db, old.batch_id)
    _require_editable(batch)
    # The observation time stays the original one: a correction fixes WHAT was recorded, not WHEN it was observed.
    # When the correction itself happened is kept in recorded_at and the audit trail.
    new = StepEntry(batch_id=old.batch_id, step_id=old.step_id, value=new_value, observed_at=old.observed_at,
                    recorded_by=user.id, correction_reason=reason.strip())
    db.add(new)
    db.flush()
    old.superseded_by = new.id
    audit(db, user, "correct_value", "step_entry", new.id, before={"entry": old.id, "value": old.value},
          after={"entry": new.id, "value": new_value}, reason=reason.strip())
    if _out_of_spec(old.step, new_value):
        raise_deviation(db, None, old.batch_id, f"Corrected {old.step.parameter} = {new_value} still out of spec",
                        step_entry_id=new.id)
    return new


# ---------- e-signatures (FRS-06, FRS-07) ----------
def sign(db: Session, user: User, password: str, record_type: str, record_id: int, meaning: str) -> Signature:
    if meaning not in MEANINGS:
        raise RuleViolation(f"Unknown signature meaning '{meaning}'.")
    if not verify_password(password, user.password_hash):  # re-authentication at the moment of signing
        audit(db, user, "signature_failed", record_type, record_id, reason="wrong password")
        raise RuleViolation("Signature failed: password incorrect.")
    if record_type == "step_entry" and meaning == "verified":
        require(user, "verify")
        entry = db.get(StepEntry, record_id)
        if entry is None or entry.superseded_by is not None:
            raise RuleViolation("Only the current entry can be verified.")
        _require_editable(_batch(db, entry.batch_id))
        if entry.recorded_by == user.id:
            raise RuleViolation("Two-person rule: you cannot verify your own entry.")
    sig = Signature(record_type=record_type, record_id=record_id, user_id=user.id, printed_name=user.full_name, meaning=meaning)
    db.add(sig)
    db.flush()
    audit(db, user, "e_signature", record_type, record_id, after={"meaning": meaning, "printed_name": user.full_name,
                                                                  "signed_at": sig.signed_at})
    return sig


def signatures_for(db: Session, record_type: str, record_id: int) -> list[Signature]:
    return list(db.scalars(select(Signature).where(Signature.record_type == record_type, Signature.record_id == record_id)))


# ---------- deviations (FRS-04, FRS-12) ----------
def raise_deviation(db: Session, user: User | None, batch_id: int, description: str, severity: str = "major",
                    step_entry_id: int | None = None) -> Deviation:
    if user is not None:
        require(user, "raise_deviation")
    dev = Deviation(batch_id=batch_id, step_entry_id=step_entry_id, description=description, severity=severity)
    db.add(dev)
    db.flush()
    audit(db, user, "raise_deviation", "deviation", dev.id, after={"description": description, "severity": severity})
    return dev


def close_deviation(db: Session, user: User, password: str, deviation_id: int, reason: str) -> Deviation:
    require(user, "close_deviation")
    if not reason or len(reason.strip()) < 20:
        raise RuleViolation("Closure needs an investigation summary of at least 20 characters.")
    dev = db.get(Deviation, deviation_id)
    if dev is None or dev.status != "open":
        raise RuleViolation("Deviation not found or already closed.")
    sign(db, user, password, "deviation", deviation_id, "closed")
    dev.status, dev.closure_reason = "closed", reason.strip()
    audit(db, user, "close_deviation", "deviation", dev.id, before={"status": "open"}, after={"status": "closed"}, reason=reason.strip())
    return dev


# ---------- review and release (FRS-08, FRS-10) ----------
def release_blockers(db: Session, batch_id: int) -> list[str]:
    batch = _batch(db, batch_id)
    entries = current_entries(db, batch_id)
    blockers = []
    for step in batch.template.steps:
        entry = entries.get(step.id)
        if entry is None:
            blockers.append(f"Step {step.seq} ({step.parameter}) not recorded.")
        elif step.critical and not any(s.meaning == "verified" for s in signatures_for(db, "step_entry", entry.id)):
            blockers.append(f"Critical step {step.seq} ({step.parameter}) not verified by a second person.")
    open_devs = db.scalars(select(Deviation).where(Deviation.batch_id == batch_id, Deviation.status == "open")).all()
    blockers += [f"Deviation #{d.id} is open: {d.description}" for d in open_devs]
    return blockers


def submit_for_review(db: Session, user: User, password: str, batch_id: int) -> Batch:
    require(user, "submit_review")
    batch = _batch(db, batch_id)
    _require_editable(batch)
    missing = [b for b in release_blockers(db, batch_id) if "not recorded" in b or "not verified" in b]
    if missing:
        raise RuleViolation("Cannot submit for review: " + " ".join(missing))
    sign(db, user, password, "batch", batch_id, "reviewed")
    batch.status = "in_review"
    audit(db, user, "submit_review", "batch", batch_id, before={"status": "in_progress"}, after={"status": "in_review"})
    return batch


def release_batch(db: Session, user: User, password: str, batch_id: int) -> Batch:
    require(user, "release")
    batch = _batch(db, batch_id)
    if batch.status != "in_review":
        raise RuleViolation("Only batches in review can be released.")
    blockers = release_blockers(db, batch_id)
    if blockers:
        raise RuleViolation("Release blocked: " + " ".join(blockers))
    reviewer_ids = {s.user_id for s in signatures_for(db, "batch", batch_id) if s.meaning == "reviewed"}
    if user.id in reviewer_ids:
        raise RuleViolation("Two-person rule: the reviewer cannot also release the batch.")
    sign(db, user, password, "batch", batch_id, "approved_release")
    batch.status = "released"
    audit(db, user, "release_batch", "batch", batch_id, before={"status": "in_review"}, after={"status": "released"})
    return batch


# ---------- seed data ----------
def seed(db: Session) -> dict:
    """Demo users and a master batch record (paracetamol 500 mg tablets, illustrative values)."""
    users = {
        "op1": create_user(db, "op1", "Asha Operator", "operator", "Operator#2026"),
        "op2": create_user(db, "op2", "Ravi Operator", "operator", "Operator#2026"),
        "sup1": create_user(db, "sup1", "Meera Supervisor", "supervisor", "Supervisor#2026"),
        "qa1": create_user(db, "qa1", "Kiran QA", "qa", "QualityA#2026"),
    }
    t = Template(product="Paracetamol 500 mg tablets (demo)", version="1.0")
    db.add(t)
    db.flush()
    steps = [
        (1, "Dispense API: weigh paracetamol", "API weight", "kg", 49.5, 50.5, True),
        (2, "Blend for the specified time", "Blend time", "min", 15, 20, False),
        (3, "Record granulation temperature", "Granulation temp", "°C", 20, 25, False),
        (4, "Check tablet hardness (mean of 10)", "Hardness", "kP", 8, 12, True),
        (5, "Record average tablet weight", "Tablet weight", "mg", 570, 630, True),
    ]
    for seq, instr, param, unit, lo, hi, critical in steps:
        db.add(TemplateStep(template_id=t.id, seq=seq, instruction=instr, parameter=param, unit=unit,
                            min_value=lo, max_value=hi, critical=critical))
    db.flush()
    audit(db, None, "seed", "template", t.id, after={"product": t.product, "version": t.version})
    return {"users": users, "template": t}


def seed_demo_batches(db: Session) -> list[Batch]:
    """Hosted demo only (BATCHGUARD_DEMO=1): three batches in different states, created through the same rules, signatures
    and audit trail as any real batch, so a visitor sees the whole lifecycle without clicking through it first."""
    u = {name: db.scalar(select(User).where(User.username == name)) for name in ("op1", "op2", "sup1", "qa1")}
    pw = {"op1": "Operator#2026", "op2": "Operator#2026", "sup1": "Supervisor#2026", "qa1": "QualityA#2026"}
    t = db.scalar(select(Template).limit(1))
    step = {s.seq: s for s in t.steps}

    def record(batch, values, by="op1"):
        return {seq: record_value(db, u[by], batch.id, step[seq].id, v) for seq, v in values.items()}

    def verify(entry, by="sup1"):
        sign(db, u[by], pw[by], "step_entry", entry.id, "verified")

    # 1. Released: hardness out of spec, deviation investigated and closed by QA, one corrected entry, two-person release.
    released = create_batch(db, u["sup1"], t.id, "B-2026-014")
    e = record(released, {1: 50.1, 2: 18, 3: 22.5, 4: 12.6, 5: 598})
    e[3] = correct_value(db, u["op1"], e[3].id, 23.1, "Transcription error: thermometer read 23.1 °C")
    for seq in (1, 4, 5):
        verify(e[seq])
    submit_for_review(db, u["sup1"], pw["sup1"], released.id)
    dev = db.scalar(select(Deviation).where(Deviation.batch_id == released.id))
    close_deviation(db, u["qa1"], pw["qa1"], dev.id,
                    "Hardness tester found out of calibration; recalibrated and 10 retained tablets retested, mean 11.2 kP.")
    release_batch(db, u["qa1"], pw["qa1"], released.id)

    # 2. Blocked: all steps recorded, but an out-of-spec tablet weight raised a deviation that is still open.
    blocked = create_batch(db, u["sup1"], t.id, "B-2026-015")
    e = record(blocked, {1: 49.9, 2: 17, 3: 21.8, 4: 10.4, 5: 641}, by="op2")
    for seq in (1, 4):
        verify(e[seq])

    # 3. In progress: two steps recorded, the critical one waiting for second-person verification.
    running = create_batch(db, u["sup1"], t.id, "B-2026-016")
    record(running, {1: 50.2, 2: 16})
    return [released, blocked, running]
