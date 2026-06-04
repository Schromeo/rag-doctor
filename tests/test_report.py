from rag_doctor.diagnosis import diagnose_case
from rag_doctor.io import load_jsonl
from rag_doctor.report import render_markdown_report


def test_renders_report_for_example_cases():
    cases = load_jsonl("examples/handbook.jsonl")
    diagnoses = [diagnose_case(case) for case in cases]

    report = render_markdown_report(diagnoses)

    assert "# RAG Doctor Report" in report
    assert "Total cases: 4" in report
    assert "retrieval_miss" in report
