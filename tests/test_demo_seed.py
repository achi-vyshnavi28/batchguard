"""Hosted demo seed (not a validation requirement, so it is kept out of the OQ protocol)."""

from batchguard.alcoa import alcoa_report


def test_demo_batches_follow_the_same_rules(tmp_path):
    """Hosted-demo seed: built through the real services, so the rules, signatures and audit trail all hold."""
    from batchguard import services as svc
    from batchguard.models import make_session_factory
    Session = make_session_factory(f"sqlite:///{(tmp_path / 'demo.sqlite3').as_posix()}")
    with Session() as db:
        svc.seed(db)
        released, blocked, running = svc.seed_demo_batches(db)
        db.commit()
        assert (released.status, blocked.status, running.status) == ("released", "in_progress", "in_progress")
        assert any("Deviation" in b and "open" in b for b in svc.release_blockers(db, blocked.id))
        assert any("not verified" in b for b in svc.release_blockers(db, running.id))
        assert [c["status"] for c in alcoa_report(db, released.id)] == ["pass"] * 9
        assert svc.verify_audit_chain(db)[0]
    Session.kw["bind"].dispose()


def _web(tmp_path, monkeypatch, demo: bool):
    import importlib

    from fastapi.testclient import TestClient
    monkeypatch.setenv("BATCHGUARD_DB", f"sqlite:///{(tmp_path / 'web.sqlite3').as_posix()}")
    if demo:
        monkeypatch.setenv("BATCHGUARD_DEMO", "1")
    else:
        monkeypatch.delenv("BATCHGUARD_DEMO", raising=False)
    import batchguard.web as web
    client = TestClient(importlib.reload(web).app)
    client.__enter__()
    return client


def test_one_click_login_is_disabled_outside_the_demo(tmp_path, monkeypatch):
    c = _web(tmp_path, monkeypatch, demo=False)
    assert c.post("/demo-login", data={"username": "qa1"}).status_code == 404
    assert "Enter as QA reviewer" not in c.get("/login").text


def test_demo_landing_opens_the_released_batch_in_one_click(tmp_path, monkeypatch):
    c = _web(tmp_path, monkeypatch, demo=True)
    assert "Enter as QA reviewer" in c.get("/login").text
    page = c.post("/demo-login", data={"username": "qa1"}).text
    assert "B-2026-014" in page and "What you're looking at" in page and "QualityA#2026" in page
    assert c.post("/demo-login", data={"username": "admin"}).status_code == 404
    home = c.get("/").text
    assert "Start here" in home and "B-2026-015" in home
