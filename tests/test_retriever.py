from pathlib import Path

from rag_doctor.diagnosis import FAILURE_DOCUMENT_CONFLICT, FAILURE_PASS, diagnose_case
from rag_doctor.io import load_jsonl
from rag_doctor.retriever import build_retrieval_cases, retrieve_chunks, load_document_chunks, write_jsonl


BENCHMARK = Path("benchmarks/company_handbook")


def test_keyword_baseline_surfaces_archived_policy_risk():
    chunks = load_document_chunks(BENCHMARK / "docs", max_chunk_words=120)

    retrieved = retrieve_chunks(
        "How long do employees have to submit an expense report after a business trip?",
        chunks,
        top_k=2,
    )

    assert retrieved
    assert retrieved[0][0].source == "old_reimbursement_policy.md"


def test_builds_diagnosis_ready_cases(tmp_path):
    output = tmp_path / "baseline.jsonl"
    records = build_retrieval_cases(
        BENCHMARK / "docs",
        BENCHMARK / "questions.jsonl",
        BENCHMARK / "expected.jsonl",
        top_k=3,
        max_chunk_words=120,
    )
    write_jsonl(output, records)

    cases = load_jsonl(output)
    diagnoses = [diagnose_case(case) for case in cases]
    failure_types = {diagnosis.failure_type for diagnosis in diagnoses}

    assert len(cases) == 4
    assert FAILURE_PASS in failure_types
    assert FAILURE_DOCUMENT_CONFLICT in failure_types
