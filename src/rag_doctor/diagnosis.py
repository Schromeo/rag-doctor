from __future__ import annotations

import re
from dataclasses import dataclass

from rag_doctor.models import Chunk, EvaluationCase


FAILURE_PASS = "pass"
FAILURE_RETRIEVAL_MISS = "retrieval_miss"
FAILURE_GENERATION_MISS = "generation_miss"
FAILURE_CITATION_MISMATCH = "citation_mismatch"
FAILURE_WEAK_GROUNDING = "weak_grounding"
FAILURE_DOCUMENT_CONFLICT = "document_conflict"


@dataclass(frozen=True)
class Diagnosis:
    case_id: str
    status: str
    failure_type: str
    reason: str
    suggestion: str
    evidence_terms: tuple[str, ...]
    supporting_chunks: tuple[str, ...]


def diagnose_case(case: EvaluationCase) -> Diagnosis:
    expected_terms = extract_signal_terms(case.expected_answer)
    critical_terms = extract_critical_terms(case.expected_answer) or expected_terms
    retrieved_text = "\n".join(chunk.text for chunk in case.retrieved_chunks)
    retrieved_terms = terms_found(critical_terms, retrieved_text)
    answer_terms = terms_found(critical_terms, case.actual_answer)
    supporting_chunks = chunks_containing_terms(case.retrieved_chunks, expected_terms)

    if has_document_conflict(case):
        return Diagnosis(
            case_id=case.id,
            status="failed",
            failure_type=FAILURE_DOCUMENT_CONFLICT,
            reason="Retrieved chunks contain conflicting numeric or policy-like evidence.",
            suggestion="Inspect source freshness and ranking. Prefer authoritative or newer sources before generation.",
            evidence_terms=tuple(sorted(expected_terms)),
            supporting_chunks=supporting_chunks,
        )

    if critical_terms and not retrieved_terms:
        return Diagnosis(
            case_id=case.id,
            status="failed",
            failure_type=FAILURE_RETRIEVAL_MISS,
            reason="Retrieved chunks do not contain the key terms from the expected answer.",
            suggestion="Check indexing, chunking, top-k, embedding model, and whether the source document was ingested.",
            evidence_terms=tuple(sorted(expected_terms)),
            supporting_chunks=supporting_chunks,
        )

    if critical_terms and retrieved_terms and not answer_terms:
        return Diagnosis(
            case_id=case.id,
            status="failed",
            failure_type=FAILURE_GENERATION_MISS,
            reason="Relevant evidence was retrieved, but the generated answer missed the key terms.",
            suggestion="Improve the answer prompt, require evidence extraction before final answer, or reduce distracting context.",
            evidence_terms=tuple(sorted(expected_terms)),
            supporting_chunks=supporting_chunks,
        )

    if critical_terms and answer_terms != critical_terms:
        return Diagnosis(
            case_id=case.id,
            status="failed",
            failure_type=FAILURE_WEAK_GROUNDING,
            reason="The answer contains some expected evidence, but misses important key terms.",
            suggestion="Ask the model to answer all required constraints and validate answers against retrieved evidence.",
            evidence_terms=tuple(sorted(expected_terms)),
            supporting_chunks=supporting_chunks,
        )

    if case.citations and not citations_support_answer(case):
        return Diagnosis(
            case_id=case.id,
            status="failed",
            failure_type=FAILURE_CITATION_MISMATCH,
            reason="The cited chunks do not contain the key terms needed to support the answer.",
            suggestion="Validate citations after generation and only cite chunks that contain supporting evidence.",
            evidence_terms=tuple(sorted(expected_terms)),
            supporting_chunks=supporting_chunks,
        )

    return Diagnosis(
        case_id=case.id,
        status="passed",
        failure_type=FAILURE_PASS,
        reason="The answer is supported by retrieved evidence.",
        suggestion="No action needed.",
        evidence_terms=tuple(sorted(expected_terms)),
        supporting_chunks=supporting_chunks,
    )


def extract_signal_terms(text: str) -> set[str]:
    normalized = normalize(text)
    terms = set(re.findall(r"\d+(?:\.\d+)?%?", normalized))
    terms.update(token for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", normalized))
    terms.update(token for token in re.findall(r"[\u4e00-\u9fff]{2,}", normalized))
    return {term for term in terms if term not in STOP_TERMS}


def extract_critical_terms(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?%?", normalize(text)))


def normalize(text: str) -> str:
    return text.lower().replace("，", ",").replace("。", ".").replace("：", ":")


def terms_found(terms: set[str], text: str) -> set[str]:
    normalized = normalize(text)
    return {term for term in terms if term in normalized}


def chunks_containing_terms(chunks: tuple[Chunk, ...], terms: set[str]) -> tuple[str, ...]:
    supporting = []
    for chunk in chunks:
        if terms_found(terms, chunk.text):
            supporting.append(chunk.id)
    return tuple(supporting)


def citations_support_answer(case: EvaluationCase) -> bool:
    expected_terms = extract_critical_terms(case.expected_answer) or extract_signal_terms(case.expected_answer)
    cited_text = "\n".join(
        chunk.text for chunk in case.retrieved_chunks if chunk.id in case.citations or chunk.source in case.citations
    )
    if not expected_terms:
        return bool(cited_text.strip())
    return terms_found(expected_terms, cited_text) == expected_terms


def has_document_conflict(case: EvaluationCase) -> bool:
    expected_numbers = extract_critical_terms(case.expected_answer)
    if not expected_numbers:
        return False

    anchors = extract_anchor_terms(case.expected_answer)
    if not anchors:
        return False

    for chunk in case.retrieved_chunks:
        chunk_numbers = extract_critical_terms(chunk.text)
        if not chunk_numbers or chunk_numbers <= expected_numbers:
            continue
        if terms_found(anchors, chunk.text):
            return True
    return False


def extract_anchor_terms(text: str) -> set[str]:
    terms = extract_signal_terms(text) - extract_critical_terms(text) - STOP_TERMS
    normalized = normalize(text)
    for sequence in re.findall(r"[\u4e00-\u9fff]{4,}", normalized):
        for index in range(0, len(sequence) - 3):
            terms.add(sequence[index : index + 4])
    return {term for term in terms if len(term) >= 3}


STOP_TERMS = {
    "the",
    "and",
    "for",
    "with",
    "within",
    "after",
    "before",
    "需要",
    "员工",
    "提交",
    "申请",
    "完成",
}
