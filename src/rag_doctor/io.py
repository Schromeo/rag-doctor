from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from rag_doctor.models import EvaluationCase


def load_jsonl(path: str | Path) -> list[EvaluationCase]:
    """Load evaluation cases from newline-delimited JSON.

    Blank lines are ignored so users can keep small hand-written fixtures
    readable while learning the format.
    """

    input_path = Path(path)
    cases: list[EvaluationCase] = []
    with input_path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            raw = json.loads(stripped)
            cases.append(EvaluationCase.from_raw(raw, index))
    return cases


def write_text(path: Path, text: str) -> None:
    """Write text output and create the parent directory when needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def iter_jsonl_records(path: Path) -> Iterable[dict]:
    """Yield raw JSONL records for future import/compare workflows."""

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)
