"""Write SpecCheck results: versioned Excel test library, Jira CSV import, and a review report."""

import csv
from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from speccheck.generate import Drafted
from speccheck.lint import Gap
from speccheck.parse import Story

HEAD = PatternFill("solid", fgColor="D9E1F2")


def _sheet(wb: Workbook, title: str, header: list[str], rows: list[list], widths: list[int]):
    ws = wb.create_sheet(title)
    ws.append(header)
    for cell in ws[1]:
        cell.font, cell.fill = Font(bold=True), HEAD
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    return ws


def excel_library(path: Path, version: str, prd_title: str, stories: list[Story], drafts: dict[str, Drafted],
                  gaps: list[Gap], previous: Path | None = None) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    cases = []
    for s in stories:
        for n, tc in enumerate(drafts.get(s.id, Drafted(test_cases=[])).test_cases, start=1):
            cases.append([f"TC-{s.id[3:]}-{n:02d}", s.id, tc.title, tc.type, tc.priority, tc.preconditions,
                          "\n".join(f"{i}. {st}" for i, st in enumerate(tc.steps, start=1)), tc.expected,
                          version, "draft", "", ""])
    _sheet(wb, "Test cases", ["ID", "Story", "Title", "Type", "Priority", "Preconditions", "Steps", "Expected result",
                              "Added in", "Status", "Executed by / date", "Actual result"],
           cases, [11, 8, 40, 11, 9, 30, 55, 45, 9, 9, 18, 30])
    gap_rows = [[f"GAP-{i:02d}", g.story, g.severity, g.rule, g.text, g.why, g.question, "open"]
                for i, g in enumerate(gaps, start=1)]
    gap_rows += [[f"GAP-L{i:02d}", sid, "medium", "llm_ambiguity", a, "Drafting could not state an exact expected result.",
                  "Please clarify.", "open"]
                 for i, (sid, a) in enumerate(((sid, a) for sid, d in drafts.items() for a in d.ambiguities), start=1)]
    _sheet(wb, "Requirement gaps", ["ID", "Story", "Severity", "Rule", "Requirement text", "Why it can't be tested",
                                    "Question for product", "Status"], gap_rows, [9, 8, 9, 22, 45, 45, 45, 8])
    history = []
    if previous and previous.exists():
        history = [list(r) for r in load_workbook(previous)["Change log"].iter_rows(min_row=2, values_only=True)]
    history.append([version, date.today().isoformat(), prd_title,
                    f"{len(cases)} test cases drafted, {len(gap_rows)} requirement gaps raised"])
    _sheet(wb, "Change log", ["Version", "Date", "Source", "Change"], history, [9, 12, 45, 60])
    wb.move_sheet("Change log", offset=-2)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def jira_csv(path: Path, stories: list[Story], gaps: list[Gap], epic: str) -> Path:
    """Columns match Jira Cloud's CSV importer (map Summary, Issue Type, Description, Priority, Labels)."""
    prio = {"high": "High", "medium": "Medium", "low": "Low"}
    rows = [["Summary", "Issue Type", "Description", "Priority", "Labels"]]
    for s in stories:
        rows.append([f"{s.id} {s.title}", "Story",
                     s.narrative + "\n\nAcceptance criteria:\n" + "\n".join(f"* {c}" for c in s.criteria), "Medium", epic])
    for g in gaps:
        rows.append([f"[Spec gap] {g.story}: {g.text[:70]}", "Task",
                     f"Rule: {g.rule}\nWhy: {g.why}\nQuestion: {g.question}", prio[g.severity], f"{epic} requirement-gap"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    return path


def review_report(path: Path, prd_title: str, stories: list[Story], drafts: dict[str, Drafted], gaps: list[Gap]) -> Path:
    blocking = [g for g in gaps if g.severity == "high"]
    lines = [f"# Spec review: {prd_title}", "",
             f"**Verdict:** {'NOT ready for development' if blocking else 'Ready for development'}: "
             f"{len(blocking)} blocking (high) gap(s), {len(gaps) - len(blocking)} other.", "",
             "| Story | Criteria | Draft test cases | Gaps (high) |", "|---|---|---|---|"]
    for s in stories:
        sg = [g for g in gaps if g.story == s.id]
        n = len(drafts[s.id].test_cases) if s.id in drafts else 0
        lines.append(f"| {s.id} {s.title} | {len(s.criteria)} | {n} | {len(sg)} ({sum(g.severity == 'high' for g in sg)}) |")
    lines += ["", "## Questions for product (blocking first)", ""]
    for g in sorted(gaps, key=lambda g: {"high": 0, "medium": 1, "low": 2}[g.severity]):
        lines.append(f"- **{g.story} [{g.severity}]** \"{g.text}\": {g.why} → *{g.question}*")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
