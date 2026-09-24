import json
import os

import pytest

from batchguard.models import make_session_factory
from batchguard.services import create_batch, seed


_RESULTS: list[dict] = []


def pytest_configure(config):
    config.addinivalue_line("markers", "frs(id): functional requirement verified by this test (traceability)")


def pytest_runtest_makereport(item, call):
    """Collect evidence for the executed validation report (tools/run_validation.py)."""
    if call.when == "call" or (call.when == "setup" and call.excinfo is not None):
        marker = item.get_closest_marker("frs")
        _RESULTS.append({
            "test": item.nodeid, "frs": marker.args[0] if marker else None,
            "doc": (item.function.__doc__ or "").strip(),
            "outcome": "pass" if call.excinfo is None else "fail",
            "error": str(call.excinfo.value)[:500] if call.excinfo else None,
            "duration_s": round(call.duration, 3),
        })


def pytest_sessionfinish(session, exitstatus):
    out = os.getenv("VALIDATION_RESULTS")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(_RESULTS, f, indent=2)


@pytest.fixture
def db():
    session = make_session_factory("sqlite://")()
    yield session
    session.close()


@pytest.fixture
def world(db):
    data = seed(db)
    users = data["users"]
    batch = create_batch(db, users["sup1"], data["template"].id, "B-001")
    steps = {s.seq: s for s in data["template"].steps}
    return {"db": db, "users": users, "batch": batch, "steps": steps}
