from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from rag_doctor.diagnosis import Diagnosis


def render_markdown_report(diagnoses: list[Diagnosis]) -> str:
    """Render a report optimized for humans and GitHub comments."""

    counts = Counter(diagnosis.failure_type for diagnosis in diagnoses)
    failed = sum(1 for diagnosis in diagnoses if diagnosis.status == "failed")
    total = len(diagnoses)
    passed = total - failed

    lines = [
        "# RAG Doctor Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        f"- Total cases: {total}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "## Failure Breakdown",
        "",
    ]

    for failure_type, count in sorted(counts.items()):
        lines.append(f"- `{failure_type}`: {count}")

    lines.extend(["", "## Recommendation", "", recommendation(counts), "", "## Cases", ""])

    for diagnosis in diagnoses:
        lines.extend(
            [
                f"### {diagnosis.case_id}: `{diagnosis.failure_type}`",
                "",
                f"- Status: {diagnosis.status}",
                f"- Reason: {diagnosis.reason}",
                f"- Suggestion: {diagnosis.suggestion}",
                f"- Evidence terms: {', '.join(diagnosis.evidence_terms) or 'none'}",
                f"- Supporting chunks: {', '.join(diagnosis.supporting_chunks) or 'none'}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def recommendation(counts: Counter[str]) -> str:
    """Choose a top-level next action from the most common failure type."""

    if not counts:
        return "No cases were evaluated."
    most_common, _ = counts.most_common(1)[0]
    if most_common == "retrieval_miss":
        return "Main issue appears to be retrieval recall. Inspect ingestion, chunking, embedding choice, and top-k."
    if most_common == "generation_miss":
        return "Main issue appears to be answer generation. Make the model extract evidence before composing the final answer."
    if most_common == "citation_mismatch":
        return "Main issue appears to be citation quality. Add post-generation citation validation."
    if most_common == "weak_grounding":
        return "Main issue appears to be incomplete grounding. Validate required facts before accepting the answer."
    if most_common == "document_conflict":
        return "Main issue appears to be conflicting sources. Add source authority and freshness rules."
    return "Most cases passed. Track this report in CI to catch future regressions."
