from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from rag_doctor.models import EvaluationCase


def load_jsonl(path: str | Path) -> list[EvaluationCase]:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def iter_jsonl_records(path: Path) -> Iterable[dict]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)
