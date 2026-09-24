"""Web UI (FastAPI + server-rendered HTML). Run:  uvicorn batchguard.web:app --reload"""

import os
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from batchguard import services as svc
from batchguard.alcoa import alcoa_report
from batchguard.models import AuditEvent, Batch, Deviation, StepEntry, Template, User, make_session_factory

HERE = Path(__file__).parent
DB_URL = os.getenv("BATCHGUARD_DB", "sqlite:///batchguard.sqlite3")
SessionLocal = make_session_factory(DB_URL)
templates = Jinja2Templates(directory=HERE / "templates")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    with SessionLocal() as db:  # first start: demo users + master batch record
        if db.scalar(select(User).limit(1)) is None:
            svc.seed(db)
            db.commit()
    yield


app = FastAPI(title="BatchGuard", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("BATCHGUARD_SECRET", "dev-only-change-me"),
                   max_age=15 * 60)  # automatic logoff after 15 minutes (Part 11 session control)


@contextmanager
def action(db):
    """Commit on success AND on rule violations (so failed logins/signatures stay in the audit trail)."""
    try:
        yield
        db.commit()
    except svc.RuleViolation:
        db.commit()
        raise


def _user(request: Request, db) -> User | None:
    uid = request.session.get("uid")
    return db.get(User, uid) if uid else None


def _flash(request: Request, message: str, kind: str = "error") -> None:
    request.session["flash"] = {"message": message, "kind": kind}


def _render(request: Request, name: str, **ctx) -> HTMLResponse:
    ctx["flash"] = request.session.pop("flash", None)
    return templates.TemplateResponse(request, name, ctx)


def _back(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return _render(request, "login.html")


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with SessionLocal() as db:
        try:
            with action(db):
                user = svc.authenticate(db, username, password)
        except svc.RuleViolation as e:
            _flash(request, str(e))
            return _back("/login")
        request.session["uid"] = user.id
        return _back("/")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return _back("/login")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with SessionLocal() as db:
        user = _user(request, db)
        if not user:
            return _back("/login")
        batches = db.scalars(select(Batch).order_by(Batch.id.desc())).all()
        return _render(request, "home.html", user=user, batches=batches, templates_=db.scalars(select(Template)).all())


@app.post("/batches")
def new_batch(request: Request, template_id: int = Form(...), batch_no: str = Form(...)):
    with SessionLocal() as db:
        user = _user(request, db)
        try:
            with action(db):
                batch = svc.create_batch(db, user, template_id, batch_no.strip())
        except svc.RuleViolation as e:
            _flash(request, str(e))
            return _back("/")
        return _back(f"/batches/{batch.id}")


@app.get("/batches/{batch_id}", response_class=HTMLResponse)
def batch_page(request: Request, batch_id: int):
    with SessionLocal() as db:
        user = _user(request, db)
        if not user:
            return _back("/login")
        batch = db.get(Batch, batch_id)
        current = svc.current_entries(db, batch_id)
        history = db.scalars(select(StepEntry).where(StepEntry.batch_id == batch_id).order_by(StepEntry.id)).all()
        users = {u.id: u for u in db.scalars(select(User))}
        rows = []
        for step in batch.template.steps:
            entry = current.get(step.id)
            rows.append({"step": step, "entry": entry,
                         "signatures": svc.signatures_for(db, "step_entry", entry.id) if entry else [],
                         "history": [h for h in history if h.step_id == step.id and h.superseded_by is not None],
                         "oos": entry is not None and svc._out_of_spec(step, entry.value)})
        deviations = db.scalars(select(Deviation).where(Deviation.batch_id == batch_id)).all()
        return _render(request, "batch.html", user=user, batch=batch, rows=rows, users=users, deviations=deviations,
                       blockers=svc.release_blockers(db, batch_id),
                       batch_signatures=svc.signatures_for(db, "batch", batch_id))


def _batch_action(request: Request, batch_id: int, fn, success: str):
    with SessionLocal() as db:
        user = _user(request, db)
        if not user:
            return _back("/login")
        try:
            with action(db):
                fn(db, user)
            _flash(request, success, "ok")
        except svc.RuleViolation as e:
            _flash(request, str(e))
        return _back(f"/batches/{batch_id}")


@app.post("/batches/{batch_id}/record")
def record(request: Request, batch_id: int, step_id: int = Form(...), value: float = Form(...)):
    return _batch_action(request, batch_id, lambda db, u: svc.record_value(db, u, batch_id, step_id, value), "Value recorded.")


@app.post("/batches/{batch_id}/correct")
def correct(request: Request, batch_id: int, entry_id: int = Form(...), value: float = Form(...), reason: str = Form("")):
    return _batch_action(request, batch_id, lambda db, u: svc.correct_value(db, u, entry_id, value, reason), "Correction saved; original kept.")


@app.post("/batches/{batch_id}/verify")
def verify(request: Request, batch_id: int, entry_id: int = Form(...), password: str = Form(...)):
    return _batch_action(request, batch_id, lambda db, u: svc.sign(db, u, password, "step_entry", entry_id, "verified"), "Verified (e-signature applied).")


@app.post("/batches/{batch_id}/deviations")
def add_deviation(request: Request, batch_id: int, description: str = Form(...), severity: str = Form("major")):
    return _batch_action(request, batch_id, lambda db, u: svc.raise_deviation(db, u, batch_id, description, severity), "Deviation raised.")


@app.post("/batches/{batch_id}/deviations/{dev_id}/close")
def close_dev(request: Request, batch_id: int, dev_id: int, reason: str = Form(""), password: str = Form(...)):
    return _batch_action(request, batch_id, lambda db, u: svc.close_deviation(db, u, password, dev_id, reason), "Deviation closed.")


@app.post("/batches/{batch_id}/submit")
def submit(request: Request, batch_id: int, password: str = Form(...)):
    return _batch_action(request, batch_id, lambda db, u: svc.submit_for_review(db, u, password, batch_id), "Submitted for QA review.")


@app.post("/batches/{batch_id}/release")
def release(request: Request, batch_id: int, password: str = Form(...)):
    return _batch_action(request, batch_id, lambda db, u: svc.release_batch(db, u, password, batch_id), "Batch released.")


@app.get("/batches/{batch_id}/alcoa", response_class=HTMLResponse)
def alcoa(request: Request, batch_id: int):
    with SessionLocal() as db:
        user = _user(request, db)
        if not user:
            return _back("/login")
        return _render(request, "alcoa.html", user=user, batch=db.get(Batch, batch_id), report=alcoa_report(db, batch_id))


@app.get("/audit", response_class=HTMLResponse)
def audit_trail(request: Request):
    with SessionLocal() as db:
        user = _user(request, db)
        if not user:
            return _back("/login")
        events = db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(300)).all()
        intact, broken = svc.verify_audit_chain(db)
        return _render(request, "audit.html", user=user, events=events, intact=intact, broken=broken)
