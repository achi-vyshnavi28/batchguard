"""Execute IQ, OQ and PQ and write the executed validation package.

    python -m tools.run_validation

Outputs validation/executed/<timestamp>/:
  executed_validation_report.md  - IQ/OQ/PQ results, traceability matrix, summary and conclusion
  test_log.txt                   - raw pytest output (objective evidence)
  results.json                   - machine-readable results
"""

import importlib.metadata as md
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQ = yaml.safe_load((ROOT / "validation" / "requirements.yaml").read_text(encoding="utf-8"))


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "n/a"


def installation_qualification() -> list[dict]:
    """IQ: is the system installed as specified?"""
    checks = []

    def check(cid: str, description: str, expected: str, actual: str, ok: bool):
        checks.append({"id": cid, "description": description, "expected": expected, "actual": actual,
                       "result": "pass" if ok else "fail", "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})

    py = platform.python_version()
    check("IQ-01", "Python runtime version", "3.12.x", py, py.startswith("3.12."))
    for line in (ROOT / "requirements.txt").read_text().split():
        name, version = line.split("==")
        base = name.split("[")[0]
        try:
            installed = md.version(base)
        except md.PackageNotFoundError:
            installed = "not installed"
        check(f"IQ-02.{base}", f"Package {base} installed at pinned version", version, installed, installed == version)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        from sqlalchemy import inspect

        from batchguard.models import make_session_factory
        from batchguard.services import seed

        factory = make_session_factory(f"sqlite:///{Path(tmp, 'iq.sqlite3').as_posix()}")
        with factory() as db:
            tables = set(inspect(db.get_bind()).get_table_names())
            expected = {"users", "templates", "template_steps", "batches", "step_entries", "signatures", "deviations", "audit_trail"}
            check("IQ-03", "Database schema created", ", ".join(sorted(expected)), ", ".join(sorted(tables)), expected <= tables)
            data = seed(db)
            db.commit()
            check("IQ-04", "Master batch record and demo users load", "5 steps, 4 users",
                  f"{len(data['template'].steps)} steps, {len(data['users'])} users",
                  len(data["template"].steps) == 5 and len(data["users"]) == 4)
        factory.kw["bind"].dispose()  # release the SQLite file (Windows locks open files)
    templates = {p.name for p in (ROOT / "batchguard" / "templates").glob("*.html")}
    need = {"base.html", "login.html", "home.html", "batch.html", "alcoa.html", "audit.html"}
    check("IQ-05", "UI templates present", ", ".join(sorted(need)), ", ".join(sorted(templates)), need <= templates)
    return checks


def run_tests(out_dir: Path) -> list[dict]:
    """OQ (tests/test_oq.py) and PQ (tests/test_web.py) with raw log kept as evidence."""
    results_file = out_dir / "results_raw.json"
    env = {**os.environ, "VALIDATION_RESULTS": str(results_file)}
    proc = subprocess.run([sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider"], cwd=ROOT, env=env,
                          capture_output=True, text=True)
    (out_dir / "test_log.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    results = json.loads(results_file.read_text(encoding="utf-8"))
    results_file.unlink()
    return results


def _table(rows: list[list[str]], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |" for r in rows]
    return "\n".join(lines)


def main() -> None:
    started = datetime.now(timezone.utc)
    out_dir = ROOT / "validation" / "executed" / started.strftime("%Y%m%dT%H%M%SZ")
    out_dir.mkdir(parents=True)
    iq = installation_qualification()
    tests = run_tests(out_dir)
    oq = [t for t in tests if "test_oq" in t["test"]]
    pq = [t for t in tests if "test_web" in t["test"]]

    by_frs: dict[str, list[dict]] = {}
    for t in tests:
        if t["frs"]:
            by_frs.setdefault(t["frs"], []).append(t)
    rtm_rows, uncovered = [], []
    for f in REQ["frs"]:
        linked = by_frs.get(f["id"], [])
        status = "pass" if linked and all(t["outcome"] == "pass" for t in linked) else ("NOT TESTED" if not linked else "fail")
        if not linked:
            uncovered.append(f["id"])
        urs = next(u for u in REQ["urs"] if u["id"] == f["urs"])
        rtm_rows.append([urs["id"], urs["risk"], f["id"], ", ".join(t["test"].split("::")[-1] for t in linked) or "—", status])

    all_pass = all(c["result"] == "pass" for c in iq) and all(t["outcome"] == "pass" for t in tests) and not uncovered
    commit = _git("rev-parse", "--short", "HEAD")
    report = f"""# Executed validation report: {REQ['system']} v{REQ['version']}

| Item | Value |
|---|---|
| Executed (UTC) | {started.isoformat(timespec='seconds')} |
| Executed by | {_git('config', 'user.name')} |
| Code version | git commit `{commit}` |
| Environment | {platform.platform()}, Python {platform.python_version()} |
| GAMP 5 category | {REQ['gamp_category']} (custom application) |
| Intended use | {REQ['intended_use'].strip()} |

## 1. Installation Qualification (IQ)
{_table([[c['id'], c['description'], c['expected'], c['actual'], c['result'].upper(), c['at']] for c in iq],
        ['ID', 'Check', 'Expected', 'Actual', 'Result', 'Executed (UTC)'])}

## 2. Operational Qualification (OQ)
Each test exercises one functional requirement, including negative cases (wrong role, wrong password, missing reason, tampering).

{_table([[t['test'].split('::')[-1], t['frs'] or '—', t['outcome'].upper(), t['duration_s'], t['error'] or ''] for t in oq],
        ['Test', 'FRS', 'Result', 'Duration (s)', 'Error'])}

## 3. Performance Qualification (PQ)
End-to-end batch lifecycle through the web UI by three users (operator, supervisor, QA).

{_table([[t['test'].split('::')[-1], t['frs'] or '—', t['outcome'].upper(), t['duration_s'], t['error'] or ''] for t in pq],
        ['Test', 'FRS', 'Result', 'Duration (s)', 'Error'])}

## 4. Requirements traceability matrix (URS → FRS → test → result)
{_table(rtm_rows, ['URS', 'Risk', 'FRS', 'Verified by', 'Result'])}

## 5. Summary
- IQ: {sum(c['result'] == 'pass' for c in iq)}/{len(iq)} passed
- OQ: {sum(t['outcome'] == 'pass' for t in oq)}/{len(oq)} passed
- PQ: {sum(t['outcome'] == 'pass' for t in pq)}/{len(pq)} passed
- Requirements without a test: {', '.join(uncovered) or 'none'}
- Deviations raised during validation: see `validation/07_deviation_log.md`

## 6. Conclusion
{'All acceptance criteria met. The system is fit for its intended (demonstration) use.' if all_pass else 'Acceptance criteria NOT met. Raise deviations for each failure before release.'}

Raw evidence: `test_log.txt` (full pytest output), `results.json`.
"""
    (out_dir / "executed_validation_report.md").write_text(report, encoding="utf-8")
    (out_dir / "results.json").write_text(json.dumps({"iq": iq, "tests": tests}, indent=2), encoding="utf-8")
    print(f"{'PASS' if all_pass else 'FAIL'}: {out_dir / 'executed_validation_report.md'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
