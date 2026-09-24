"""Parse a Markdown PRD into user stories and their acceptance criteria.

Expected shape:  ### US-101 Title  /  As a ..., I want ..., so ...  /  - criterion  - criterion
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

HEADING = re.compile(r"^###\s+(US-\d+)\s+(.*)$")


@dataclass
class Story:
    id: str
    title: str
    narrative: str = ""
    criteria: list[str] = field(default_factory=list)


def parse_prd(path: Path) -> tuple[str, list[Story]]:
    title, stories, current = "", [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif m := HEADING.match(line):
            current = Story(m.group(1), m.group(2).strip())
            stories.append(current)
        elif current and line.startswith("- "):
            current.criteria.append(line[2:].strip())
        elif current and line and not current.criteria and not line.startswith("#"):
            current.narrative = f"{current.narrative} {line}".strip()
    return title, stories
