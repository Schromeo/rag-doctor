from __future__ import annotations

import argparse
from pathlib import Path

from rag_doctor.diagnosis import diagnose_case
from rag_doctor.io import load_jsonl, write_text
from rag_doctor.report import render_markdown_report


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

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
