from __future__ import annotations

import argparse
from pathlib import Path

from rag_doctor.diagnosis import diagnose_case
from rag_doctor.io import load_jsonl, write_text
from rag_doctor.report import render_markdown_report
from rag_doctor.retriever import build_retrieval_cases, write_jsonl


def main() -> int:
    """CLI entry point.

    Current command surface:
    - `diagnose`: read JSONL cases and render a Markdown report.

    Future commands should stay diagnosis-oriented: `retrieve`, `compare`,
    `import`, and `report` are good candidates; general chatbot commands are
    outside the project scope.
    """

    parser = argparse.ArgumentParser(prog="rag-doctor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    diagnose_parser = subparsers.add_parser("diagnose", help="Diagnose RAG evaluation cases from JSONL.")
    diagnose_parser.add_argument("input", type=Path, help="Path to JSONL evaluation cases.")
    diagnose_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional Markdown report path. Prints to stdout when omitted.",
    )

    retrieve_parser = subparsers.add_parser(
        "retrieve",
        help="Build diagnosis-ready JSONL cases with a transparent keyword retriever.",
    )
    retrieve_parser.add_argument("docs", type=Path, help="Directory containing Markdown documents.")
    retrieve_parser.add_argument("questions", type=Path, help="JSONL file containing benchmark questions.")
    retrieve_parser.add_argument("expected", type=Path, help="JSONL file containing expected answers.")
    retrieve_parser.add_argument("--output", type=Path, required=True, help="Output JSONL run path.")
    retrieve_parser.add_argument("--top-k", type=int, default=3, help="Number of chunks to retrieve per question.")
    retrieve_parser.add_argument(
        "--max-chunk-words",
        type=int,
        default=120,
        help="Maximum words per generated document chunk.",
    )

    args = parser.parse_args()

    if args.command == "diagnose":
        # Pipeline: JSONL -> EvaluationCase objects -> Diagnosis objects -> report.
        cases = load_jsonl(args.input)
        diagnoses = [diagnose_case(case) for case in cases]
        report = render_markdown_report(diagnoses)
        if args.output:
            write_text(args.output, report)
            print(f"Wrote report to {args.output}")
        else:
            print(report, end="")
        return 0

    if args.command == "retrieve":
        records = build_retrieval_cases(
            args.docs,
            args.questions,
            args.expected,
            top_k=args.top_k,
            max_chunk_words=args.max_chunk_words,
        )
        write_jsonl(args.output, records)
        print(f"Wrote {len(records)} retrieval cases to {args.output}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
