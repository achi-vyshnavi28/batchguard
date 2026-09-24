"""SpecCheck CLI.

    python -m speccheck docs/prd/PRD-1.1_cleaning_log_and_rejection.md --version 1.1
    python -m speccheck <prd.md> --version 1.1 --no-llm      # rules only (no API key needed)
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from speccheck.export import excel_library, jira_csv, review_report
from speccheck.generate import draft
from speccheck.lint import lint
from speccheck.parse import parse_prd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("prd", type=Path)
    p.add_argument("--version", required=True)
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--out", type=Path, default=ROOT / "qa")
    args = p.parse_args()
    load_dotenv(ROOT / ".env")

    title, stories = parse_prd(args.prd)
    gaps = lint(stories)
    drafts = {}
    for s in [] if args.no_llm else stories:
        try:
            drafts[s.id] = draft(s)
        except Exception as e:  # one busy/failed story must not stop the review; it is reported instead
            print(f"{s.id}: drafting skipped ({e})")
    current = args.out / f"test_library_v{args.version}.xlsx"
    previous = sorted(p for p in args.out.glob("test_library_v*.xlsx") if p != current)
    lib = excel_library(current, args.version, title, stories, drafts, gaps,
                        previous[-1] if previous else None)
    jira = jira_csv(args.out / f"jira_import_v{args.version}.csv", stories, gaps, epic="BatchGuard-1.1")
    report = review_report(args.out / f"spec_review_v{args.version}.md", title, stories, drafts, gaps)
    total = sum(len(d.test_cases) for d in drafts.values())
    print(f"{len(stories)} stories · {total} draft test cases · {len(gaps)} rule gaps "
          f"({sum(g.severity == 'high' for g in gaps)} high)\n{lib}\n{jira}\n{report}")


if __name__ == "__main__":
    main()
