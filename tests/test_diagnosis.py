from rag_doctor.diagnosis import (
    FAILURE_CITATION_MISMATCH,
    FAILURE_DOCUMENT_CONFLICT,
    FAILURE_GENERATION_MISS,
    FAILURE_PASS,
    FAILURE_RETRIEVAL_MISS,
    diagnose_case,
)
from rag_doctor.models import Chunk, EvaluationCase


def make_case(**overrides):
    data = {
        "id": "case",
        "question": "When is reimbursement due?",
        "expected_answer": "Submit within 30 days.",
        "retrieved_chunks": (Chunk(id="policy#1", text="Submit within 30 days.", source="policy.md"),),
        "actual_answer": "Submit within 30 days.",
        "citations": ("policy#1",),
    }
    data.update(overrides)
    return EvaluationCase(**data)


def test_passes_when_answer_and_citation_are_supported():
    diagnosis = diagnose_case(make_case())

    assert diagnosis.failure_type == FAILURE_PASS
    assert diagnosis.status == "passed"


def test_detects_retrieval_miss():
    diagnosis = diagnose_case(
        make_case(
            retrieved_chunks=(Chunk(id="other#1", text="Keep receipts.", source="other.md"),),
            actual_answer="Submit as soon as possible.",
            citations=("other#1",),
        )
    )

    assert diagnosis.failure_type == FAILURE_RETRIEVAL_MISS


def test_detects_generation_miss():
    diagnosis = diagnose_case(make_case(actual_answer="Submit it promptly."))

    assert diagnosis.failure_type == FAILURE_GENERATION_MISS


def test_detects_citation_mismatch():
    diagnosis = diagnose_case(
        make_case(
            retrieved_chunks=(
                Chunk(id="policy#1", text="Submit within 30 days.", source="policy.md"),
                Chunk(id="other#1", text="Keep receipts.", source="other.md"),
            ),
            citations=("other#1",),
        )
    )

    assert diagnosis.failure_type == FAILURE_CITATION_MISMATCH


def test_detects_document_conflict():
    diagnosis = diagnose_case(
        make_case(
            expected_answer="Submit reimbursement within 30 days.",
            retrieved_chunks=(
                Chunk(id="new#1", text="Reimbursement is due within 30 days.", source="new.md"),
                Chunk(id="old#1", text="Reimbursement is due within 14 days.", source="old.md"),
            )
        )
    )

    assert diagnosis.failure_type == FAILURE_DOCUMENT_CONFLICT
