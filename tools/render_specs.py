"""Render the URS and FRS documents from validation/requirements.yaml (single source of truth).

    python -m tools.render_specs
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "validation"


def main() -> None:
    req = yaml.safe_load((V / "requirements.yaml").read_text(encoding="utf-8"))
    head = f"System: {req['system']} v{req['version']} · GAMP 5 category {req['gamp_category']}\n\nIntended use: {req['intended_use'].strip()}\n"
    urs = ["# 01 User Requirements Specification (URS)", "", head,
           "Risk: high = direct impact on product quality, patient safety or data integrity.", "",
           "| ID | Requirement | Risk |", "|---|---|---|"]
    urs += [f"| {u['id']} | {u['text']} | {u['risk']} |" for u in req["urs"]]
    frs = ["# 02 Functional Requirements Specification (FRS)", "", head, "| ID | Traces to | Function |", "|---|---|---|"]
    frs += [f"| {f['id']} | {f['urs']} | {f['text']} |" for f in req["frs"]]
    (V / "01_URS.md").write_text("\n".join(urs) + "\n", encoding="utf-8")
    (V / "02_FRS.md").write_text("\n".join(frs) + "\n", encoding="utf-8")
    print("Wrote 01_URS.md and 02_FRS.md")


if __name__ == "__main__":
    main()
