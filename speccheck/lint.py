"""Deterministic requirement checks: "if a spec can't be turned into a test case, it isn't finished".

Each rule returns a gap with the exact text, why it can't be tested, and the question to send back to product.
Runs without any AI, so the result is repeatable and auditable.
"""

import re
from dataclasses import dataclass

from speccheck.parse import Story


@dataclass
class Gap:
    story: str
    text: str
    rule: str
    severity: str  # high | medium | low
    why: str
    question: str


VAGUE = {
    "quickly": "What response time, measured how (e.g. p95 < 2 s)?",
    "fast": "What response time, measured how?",
    "user-friendly": "Which usability criterion (e.g. task done in <= 3 clicks, no training)?",
    "easy": "Which measurable usability criterion?",
    "as needed": "Under which exact conditions, and who decides?",
    "when needed": "Under which exact conditions?",
    "appropriate": "What is appropriate, specifically?",
    "etc": "List all items explicitly.",
    "and so on": "List all items explicitly.",
    "robust": "Which failure scenarios must be handled, and how?",
}
PLACEHOLDERS = re.compile(r"\b(TBD|TBC|TODO|to be decided)\b", re.I)
WEAK_MODAL = re.compile(r"\b(should|may|could|might)\b", re.I)
GXP_ACTIONS = re.compile(r"\b(override|delete|remove|change|edit|bypass|reject)\b", re.I)
GXP_CONTROLS = re.compile(r"\b(reason|signature|e-signature|audit)\b", re.I)


def lint_story(story: Story) -> list[Gap]:
    gaps: list[Gap] = []
    if len(story.criteria) < 2:
        gaps.append(Gap(story.id, story.title, "thin_acceptance_criteria", "medium",
                        f"Only {len(story.criteria)} acceptance criterion; negative and boundary behaviour are undefined.",
                        "What should happen on invalid input, wrong role, and at the limits?"))
    for c in story.criteria:
        low = c.lower()
        for word, question in VAGUE.items():
            if re.search(rf"\b{re.escape(word)}\b", low):
                gaps.append(Gap(story.id, c, "vague_term", "high" if word in ("as needed", "when needed") else "medium",
                                f"'{word}' has no pass/fail criterion.", question))
        if PLACEHOLDERS.search(c):
            gaps.append(Gap(story.id, c, "placeholder", "high", "Requirement is not decided yet.",
                            "Please decide and specify before development starts."))
        if WEAK_MODAL.search(c):
            gaps.append(Gap(story.id, c, "weak_modal", "low", "'should/may' makes it unclear whether this is mandatory.",
                            "Is this mandatory ('must') or optional?"))
        if GXP_ACTIONS.search(c) and not GXP_CONTROLS.search(" ".join(story.criteria)):
            gaps.append(Gap(story.id, c, "gxp_control_missing", "high",
                            "A GMP-relevant action (override/delete/change/reject) without a required reason, "
                            "e-signature or audit-trail entry (21 CFR 11.10(e), 11.50).",
                            "Must this action require a reason, an e-signature and an audit-trail entry? Who may perform it?"))
    return gaps


def lint(stories: list[Story]) -> list[Gap]:
    return [g for s in stories for g in lint_story(s)]
