"""PQ-style end-to-end test: the full batch lifecycle through the web UI, as real users would do it."""

import importlib
import re

import pytest
from fastapi.testclient import TestClient

PW = {"op1": "Operator#2026", "sup1": "Supervisor#2026", "qa1": "QualityA#2026"}


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("BATCHGUARD_DB", f"sqlite:///{(tmp_path / 'bg.sqlite3').as_posix()}")
    import batchguard.web as web
    return importlib.reload(web).app


def login(app, username):
    c = TestClient(app)
    c.__enter__()  # run startup (seed)
    r = c.post("/login", data={"username": username, "password": PW[username]})
    assert r.status_code == 200 and "Log out" in r.text
    return c


def flash(r) -> str:
    m = re.search(r'role="alert">(.*?)</div>', r.text, re.S)
    return m.group(1).strip() if m else ""


@pytest.mark.frs("FRS-08")
def test_pq_full_batch_lifecycle(app):
    sup, op, qa = login(app, "sup1"), login(app, "op1"), login(app, "qa1")
    r = sup.post("/batches", data={"template_id": 1, "batch_no": "B-PQ-001"})
    assert "B-PQ-001" in r.text
    bid = int(re.search(r"/batches/(\d+)/alcoa", r.text).group(1))
    for step_id, value in {1: 50.1, 2: 18, 3: 23, 4: 12.5, 5: 601}.items():  # step 4 hardness out of spec
        op.post(f"/batches/{bid}/record", data={"step_id": step_id, "value": value})
    page = op.get(f"/batches/{bid}").text
    assert "out of spec" in page and "Hardness = 12.5" in page

    for entry_id in (1, 4, 5):  # critical steps: API weight, hardness, tablet weight
        r = sup.post(f"/batches/{bid}/verify", data={"entry_id": entry_id, "password": PW["sup1"]})
        assert flash(r).startswith("Verified")
    r = sup.post(f"/batches/{bid}/submit", data={"password": PW["sup1"]})
    assert flash(r) == "Submitted for QA review."
    r = qa.post(f"/batches/{bid}/release", data={"password": PW["qa1"]})
    assert "Release blocked" in flash(r) and "Deviation" in flash(r)
    r = qa.post(f"/batches/{bid}/deviations/1/close",
                data={"reason": "Hardness tester re-calibrated; retest of 10 tablets 11.2 kP mean", "password": PW["qa1"]})
    assert flash(r) == "Deviation closed."
    r = qa.post(f"/batches/{bid}/release", data={"password": PW["qa1"]})
    assert flash(r) == "Batch released." and "released" in r.text

    alcoa = qa.get(f"/batches/{bid}/alcoa").text
    assert alcoa.count("pill pass") == 9
    audit = qa.get("/audit").text
    assert "intact" in audit and "release_batch" in audit


@pytest.mark.frs("FRS-02")
def test_ui_blocks_actions_outside_role(app):
    sup, op = login(app, "sup1"), login(app, "op1")
    sup.post("/batches", data={"template_id": 1, "batch_no": "B-ROLE"})
    r = sup.post("/batches/1/record", data={"step_id": 1, "value": 50})
    assert "not allowed" in flash(r)
    r = op.post("/batches", data={"template_id": 1, "batch_no": "B-X"}, follow_redirects=True)
    assert "not allowed" in flash(r)


@pytest.mark.frs("FRS-01")
def test_unauthenticated_users_are_redirected(app):
    c = TestClient(app)
    with c:
        assert c.get("/", follow_redirects=False).headers["location"] == "/login"
        assert c.get("/audit", follow_redirects=False).headers["location"] == "/login"
