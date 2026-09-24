"""Draft test cases (and extra gaps a rule can't see) from user stories with an LLM.

The LLM drafts; a person reviews. Every drafted case is marked status "draft" in the test library,
and the deterministic lint in lint.py always runs regardless of the LLM.
"""

import json
import os
import re
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from speccheck.parse import Story

MODELS = [m.strip() for m in os.getenv("SPECCHECK_MODELS", "gemini-3.6-flash,gemini-flash-lite-latest").split(",")]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class TestCase(BaseModel):
    title: str
    type: Literal["positive", "negative", "boundary", "permission", "audit"]
    preconditions: str
    steps: list[str] = Field(min_length=1)
    expected: str
    priority: Literal["high", "medium", "low"]


class Drafted(BaseModel):
    test_cases: list[TestCase]
    ambiguities: list[str] = Field(default_factory=list, description="Anything that stopped you writing an exact expected result")


PROMPT = """You write test cases for a GxP-regulated pharmaceutical manufacturing system (21 CFR Part 11).
User story {id}: {title}
{narrative}
Acceptance criteria:
{criteria}

Write 4-8 test cases covering the happy path, negative cases, boundaries (limits such as time windows),
permissions (wrong role), and audit-trail/e-signature expectations. Expected results must be exact and checkable.
If a criterion is too vague to write an exact expected result, do not invent one: add it to "ambiguities".
Reply with ONE JSON object: {{"test_cases": [...], "ambiguities": [...]}} matching this schema:
{schema}"""


class LLM(Protocol):
    def __call__(self, prompt: str) -> str: ...


def gemini(prompt: str, attempts: int = 3) -> str:
    """Direct REST call (no SDK). Retries busy responses with backoff, then falls back to the next model."""
    import time

    import httpx

    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
    last = None
    for model in MODELS:
        for attempt in range(attempts):
            r = httpx.post(GEMINI_URL.format(model=model), json=body, timeout=180,
                           headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            last = f"{model}: HTTP {r.status_code}"
            if r.status_code not in (429, 500, 502, 503, 504):
                break
            time.sleep(5 * 2 ** attempt)
    raise RuntimeError(f"All Gemini models busy or failing ({last})")


def _json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in reply")
    return json.loads(m.group(0))


def draft(story: Story, llm: LLM = gemini) -> Drafted:
    prompt = PROMPT.format(id=story.id, title=story.title, narrative=story.narrative,
                           criteria="\n".join(f"- {c}" for c in story.criteria),
                           schema=json.dumps(Drafted.model_json_schema()))
    return Drafted.model_validate(_json(llm(prompt)))
