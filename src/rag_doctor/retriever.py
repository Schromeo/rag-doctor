from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag_doctor.diagnosis import STOP_TERMS, normalize


@dataclass(frozen=True)
class DocumentChunk:
    """A chunk created from source documents for the baseline retriever."""

    id: str
    source: str
    text: str


@dataclass(frozen=True)
class ExpectedAnswer:
    """Expected answer metadata for one benchmark question."""

    id: str
    expected_answer: str
    required_sources: tuple[str, ...]

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "ExpectedAnswer":
        return cls(
            id=str(raw["id"]),
            expected_answer=str(raw.get("expected_answer") or ""),
            required_sources=tuple(str(source) for source in raw.get("required_sources") or ()),
        )


def build_retrieval_cases(
    docs_dir: Path,
    questions_path: Path,
    expected_path: Path,
    *,
    top_k: int = 3,
    max_chunk_words: int = 120,
) -> list[dict[str, Any]]:
    """Build diagnosis-ready JSON records from docs and benchmark questions.

    Tunable parameters:
    - `top_k`: how many chunks to return per question.
    - `max_chunk_words`: rough chunk size for long sections.

    This is intentionally a transparent keyword retriever, not a production
    semantic search engine. Its job is to produce realistic baseline runs that
    make retrieval failures easy to inspect.
    """

    chunks = load_document_chunks(docs_dir, max_chunk_words=max_chunk_words)
    expected_by_id = load_expected_answers(expected_path)
    records = []

    for raw_question in load_jsonl_records(questions_path):
        question_id = str(raw_question["id"])
        expected = expected_by_id[question_id]
        retrieved = retrieve_chunks(str(raw_question["question"]), chunks, top_k=top_k)
        records.append(
            {
                "id": question_id,
                "question": str(raw_question["question"]),
                "expected_answer": expected.expected_answer,
                "retrieved_chunks": [
                    {"id": chunk.id, "source": chunk.source, "text": chunk.text} for chunk, _score in retrieved
                ],
                # A real RAG run would contain the model answer. For benchmark
                # generation we leave a deterministic placeholder so diagnosis
                # can still distinguish retrieval misses from generation misses.
                "actual_answer": baseline_answer(str(raw_question["question"]), retrieved),
                "citations": [retrieved[0][0].id] if retrieved else [],
                "required_sources": list(expected.required_sources),
            }
        )

    return records


def load_document_chunks(docs_dir: Path, *, max_chunk_words: int) -> list[DocumentChunk]:
    """Read Markdown documents and split them into inspectable chunks."""

    chunks: list[DocumentChunk] = []
    for path in sorted(docs_dir.glob("*.md")):
        sections = split_markdown_sections(path.read_text(encoding="utf-8"))
        for section_index, section in enumerate(sections, start=1):
            for part_index, text in enumerate(split_by_word_count(section, max_chunk_words), start=1):
                chunk_id = f"{path.name}#section-{section_index}-part-{part_index}"
                chunks.append(DocumentChunk(id=chunk_id, source=path.name, text=text))
    return chunks


def split_markdown_sections(markdown: str) -> list[str]:
    """Split Markdown on headings while preserving heading text in each chunk."""

    sections: list[str] = []
    current: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("#") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    return [section for section in sections if section]


def split_by_word_count(text: str, max_words: int) -> list[str]:
    """Split long sections into word-count chunks."""

    words = text.split()
    if len(words) <= max_words:
        return [text]
    return [" ".join(words[index : index + max_words]) for index in range(0, len(words), max_words)]


def retrieve_chunks(
    question: str, chunks: list[DocumentChunk], *, top_k: int
) -> list[tuple[DocumentChunk, float]]:
    """Rank chunks by keyword overlap with the question."""

    query_terms = tokenize(question)
    scored = []
    for chunk in chunks:
        chunk_terms = tokenize(chunk.text)
        overlap = query_terms & chunk_terms
        if not overlap:
            continue
        score = len(overlap) / max(len(query_terms), 1)
        scored.append((chunk, score))
    return sorted(scored, key=lambda item: (-item[1], item[0].source, item[0].id))[:top_k]


def baseline_answer(question: str, retrieved: list[tuple[DocumentChunk, float]]) -> str:
    """Create a deterministic extractive pseudo-answer from the top chunk."""

    if not retrieved:
        return "No relevant evidence was retrieved."
    text = re.sub(r"\s+", " ", retrieved[0][0].text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if not sentences:
        return text
    query_terms = tokenize(question)
    return max(sentences, key=lambda sentence: len(tokenize(sentence) & query_terms))


def tokenize(text: str) -> set[str]:
    """Tokenize text for keyword overlap scoring."""

    return {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}|\d+(?:\.\d+)?%?", normalize(text))
        if token not in STOP_TERMS
    }


def load_expected_answers(path: Path) -> dict[str, ExpectedAnswer]:
    return {answer.id: answer for answer in (ExpectedAnswer.from_raw(raw) for raw in load_jsonl_records(path))}


def load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
