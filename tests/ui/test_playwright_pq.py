"""PQ through a real browser (Playwright). Each step saves a screenshot as objective evidence.

Screenshots go to $EVIDENCE_DIR (set by tools/run_validation.py) or a temp folder.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import Page, expect

PW = {"op1": "Operator#2026", "sup1": "Supervisor#2026", "qa1": "QualityA#2026"}


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    db = tmp_path_factory.mktemp("db") / "ui.sqlite3"
    env = {**os.environ, "BATCHGUARD_DB": f"sqlite:///{db.as_posix()}"}
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "batchguard.web:app", "--port", str(port)],
                            cwd=Path(__file__).resolve().parents[2], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    for _ in range(60):
        try:
            if httpx.get(f"{url}/login").status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.25)
    yield url
    proc.terminate()
    proc.wait()


@pytest.fixture
def evidence(tmp_path, request):
    folder = Path(os.getenv("EVIDENCE_DIR", tmp_path))
    folder.mkdir(parents=True, exist_ok=True)
    prefix = request.node.name.removeprefix("test_pq_ui_").split("[")[0]
    counter = {"n": 0}

    def shot(page: Page, name: str) -> None:
        counter["n"] += 1
        page.screenshot(path=folder / f"{prefix}__{counter['n']:02d}_{name}.png", full_page=True)

    return shot


def login(page: Page, url: str, user: str) -> None:
    page.goto(f"{url}/logout")
    page.get_by_label("Username").fill(user)
    page.get_by_label("Password").fill(PW[user])
    page.get_by_role("button", name="Log in").click()
    expect(page.get_by_text("Log out")).to_be_visible()


@pytest.mark.frs("FRS-08")
def test_pq_ui_batch_lifecycle_with_screenshots(page: Page, server: str, evidence):
    # Supervisor creates the batch
    login(page, server, "sup1")
    page.get_by_label("batch number").fill("B-UI-001")
    page.get_by_role("button", name="Create").click()
    expect(page.get_by_role("heading", name="B-UI-001")).to_be_visible()
    evidence(page, "batch_created")
    batch_url = page.url

    # Operator records 5 steps; hardness out of spec
    login(page, server, "op1")
    page.goto(batch_url)
    for seq, value in [(1, "50.0"), (2, "17"), (3, "22"), (4, "13"), (5, "600")]:
        page.get_by_label(f"value for step {seq}").fill(value)
        page.get_by_role("button", name="Record").first.click()
        expect(page.get_by_role("alert")).to_contain_text("Value recorded")
    expect(page.get_by_text("out of spec").first).to_be_visible()
    evidence(page, "values_recorded_oos_flagged")

    # Supervisor verifies critical steps (e-signature) and submits
    login(page, server, "sup1")
    page.goto(batch_url)
    for seq in (1, 4, 5):
        page.get_by_label(f"password to verify step {seq}").fill(PW["sup1"])
        page.get_by_label(f"password to verify step {seq}").press("Enter")
        expect(page.get_by_role("alert")).to_contain_text("Verified")
    evidence(page, "critical_steps_verified")
    page.get_by_label("password to submit for review").fill(PW["sup1"])
    page.get_by_role("button", name="Submit for QA review").click()
    expect(page.get_by_role("alert")).to_contain_text("Submitted for QA review")

    # QA: release blocked by the open deviation
    login(page, server, "qa1")
    page.goto(batch_url)
    page.get_by_label("password to release").fill(PW["qa1"])
    page.get_by_role("button", name="Release batch").click()
    expect(page.get_by_role("alert")).to_contain_text("Release blocked")
    evidence(page, "release_blocked_by_deviation")

    # QA closes the deviation with an e-signature, then releases
    page.get_by_label("closure summary for deviation 1").fill("Tester recalibrated; retest of 10 tablets mean 11.4 kP, within spec")
    page.get_by_label("password to close deviation 1").fill(PW["qa1"])
    page.get_by_role("button", name="Close").click()
    expect(page.get_by_role("alert")).to_contain_text("Deviation closed")
    page.get_by_label("password to release").fill(PW["qa1"])
    page.get_by_role("button", name="Release batch").click()
    expect(page.get_by_role("alert")).to_contain_text("Batch released")
    evidence(page, "batch_released")

    # Data-integrity views
    page.get_by_role("link", name="ALCOA+ report").click()
    expect(page.locator(".pill.pass")).to_have_count(9)
    evidence(page, "alcoa_report_9_of_9")
    page.get_by_role("link", name="Audit trail").click()
    expect(page.get_by_text("intact")).to_be_visible()
    evidence(page, "audit_trail_intact")


@pytest.mark.frs("FRS-01")
def test_pq_ui_lockout_after_three_failed_logins(page: Page, server: str, evidence):
    for _ in range(3):
        page.goto(f"{server}/login")
        page.get_by_label("Username").fill("op2")
        page.get_by_label("Password").fill("wrong-password")
        page.get_by_role("button", name="Log in").click()
    page.get_by_label("Username").fill("op2")
    page.get_by_label("Password").fill(PW["op1"])  # op2 shares the demo password with op1
    page.get_by_role("button", name="Log in").click()
    expect(page.get_by_role("alert")).to_contain_text("locked")
    evidence(page, "account_locked")
