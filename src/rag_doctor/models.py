from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chunk:
    """One retrieved evidence chunk from an upstream RAG system."""

    id: str
    text: str
    source: str | None = None

    @classmethod
    def from_raw(cls, raw: str | dict[str, Any], index: int) -> "Chunk":
        """Parse either compact string chunks or structured chunk objects."""

        if isinstance(raw, str):
            return cls(id=f"chunk-{index}", text=raw, source=None)
        return cls(
            id=str(raw.get("id") or f"chunk-{index}"),
            text=str(raw.get("text") or ""),
            source=str(raw["source"]) if raw.get("source") else None,
        )


@dataclass(frozen=True)
class EvaluationCase:
    """One RAG run result that RAG Doctor can diagnose.

    The project currently assumes retrieval and generation already happened
    upstream. `retrieved_chunks` and `actual_answer` are observations from that
    upstream run, not outputs produced by RAG Doctor.
    """

    id: str
    question: str
    expected_answer: str
    retrieved_chunks: tuple[Chunk, ...]
    actual_answer: str
    citations: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_raw(cls, raw: dict[str, Any], index: int) -> "EvaluationCase":
        """Normalize one JSONL object into the internal case model."""

        chunks = tuple(
            Chunk.from_raw(chunk, chunk_index)
            for chunk_index, chunk in enumerate(raw.get("retrieved_chunks") or [], start=1)
        )
        return cls(
            id=str(raw.get("id") or f"case-{index}"),
            question=str(raw.get("question") or ""),
            expected_answer=str(raw.get("expected_answer") or ""),
            retrieved_chunks=chunks,
            actual_answer=str(raw.get("actual_answer") or ""),
            citations=tuple(str(citation) for citation in raw.get("citations") or ()),
        )
