"""JSON API (v1) used by integrations and by the Postman collection in postman/.

Auth: the same session cookie as the web UI (POST /api/v1/login). Errors are JSON:
401 not logged in · 403 rule/permission violation · 404 not found · 422 invalid input.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from batchguard import services as svc
from batchguard.alcoa import alcoa_report
from batchguard.models import Batch, Deviation, User

router = APIRouter(prefix="/api/v1")


class Login(BaseModel):
    username: str
    password: str


class NewBatch(BaseModel):
    template_id: int
    batch_no: str = Field(min_length=3, max_length=30)


class Record(BaseModel):
    step_id: int
    value: float


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def _run(request: Request, fn, status: int = 200):
    """Authenticate, run a service call, commit, and map rule violations to 403."""
    from batchguard.web import SessionLocal, action

    with SessionLocal() as db:
        uid = request.session.get("uid")
        user = db.get(User, uid) if uid else None
        if user is None:
            return _error(401, "Not logged in.")
        try:
            with action(db):
                result = fn(db, user)
        except svc.RuleViolation as e:
            return _error(403, str(e))
        return JSONResponse(result, status_code=status)


def _batch_json(db, batch: Batch) -> dict:
    current = svc.current_entries(db, batch.id)
    return {
        "id": batch.id, "batch_no": batch.batch_no, "status": batch.status,
        "product": batch.template.product, "template_version": batch.template.version,
        "steps": [{"step_id": s.id, "seq": s.seq, "parameter": s.parameter, "unit": s.unit,
                   "min": s.min_value, "max": s.max_value, "critical": s.critical,
                   "value": current[s.id].value if s.id in current else None} for s in batch.template.steps],
        "release_blockers": svc.release_blockers(db, batch.id),
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/login")
def api_login(request: Request, body: Login):
    from batchguard.web import SessionLocal, action

    with SessionLocal() as db:
        try:
            with action(db):
                user = svc.authenticate(db, body.username, body.password)
        except svc.RuleViolation as e:
            return _error(401, str(e))
        request.session["uid"] = user.id
        return {"username": user.username, "role": user.role}


@router.get("/batches")
def list_batches(request: Request):
    return _run(request, lambda db, u: [{"id": b.id, "batch_no": b.batch_no, "status": b.status}
                                        for b in db.scalars(select(Batch).order_by(Batch.id))])


@router.post("/batches")
def create(request: Request, body: NewBatch):
    return _run(request, lambda db, u: _batch_json(db, svc.create_batch(db, u, body.template_id, body.batch_no)), 201)


@router.get("/batches/{batch_id}")
def get_batch(request: Request, batch_id: int):
    def fn(db, u):
        batch = db.get(Batch, batch_id)
        if batch is None:
            raise svc.RuleViolation("Batch not found.")
        return _batch_json(db, batch)
    return _run(request, fn)


@router.post("/batches/{batch_id}/entries")
def record(request: Request, batch_id: int, body: Record):
    def fn(db, u):
        entry = svc.record_value(db, u, batch_id, body.step_id, body.value)
        devs = db.scalars(select(Deviation).where(Deviation.step_entry_id == entry.id)).all()
        return {"entry_id": entry.id, "value": entry.value, "deviation_ids": [d.id for d in devs]}
    return _run(request, fn, 201)


@router.get("/batches/{batch_id}/alcoa")
def alcoa(request: Request, batch_id: int):
    return _run(request, lambda db, u: alcoa_report(db, batch_id))


@router.get("/audit/verify")
def verify_chain(request: Request):
    def fn(db, u):
        intact, broken = svc.verify_audit_chain(db)
        return {"intact": intact, "first_broken_event": broken}
    return _run(request, fn)
