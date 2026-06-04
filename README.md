# RAG Doctor

RAG Doctor diagnoses why a Retrieval-Augmented Generation system failed.

It is intentionally not another chatbot, RAG dashboard, or observability platform. The first goal is smaller and sharper:

> Know why your RAG failed, not just that it failed.

## What It Does

Given JSONL records containing a question, expected answer, retrieved chunks, model answer, and citations, RAG Doctor classifies each case:

- `pass`: the answer is grounded in retrieved evidence.
- `retrieval_miss`: the retrieved chunks do not contain the expected evidence.
- `generation_miss`: the evidence was retrieved, but the answer missed it.
- `citation_mismatch`: the answer may be right, but cited sources do not support it.
- `weak_grounding`: the answer is partially supported but incomplete.
- `document_conflict`: retrieved chunks appear to contain conflicting evidence.

It then produces a Markdown report with failure counts and recommendations.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
rag-doctor diagnose examples/handbook.jsonl --output outputs/report.md
```

Open the generated report:

```bash
sed -n '1,220p' outputs/report.md
```

Run the test suite:

```bash
pytest
```

You can also run without installing the package by setting `PYTHONPATH`:

```bash
PYTHONPATH=src python -m rag_doctor.cli diagnose examples/handbook.jsonl
```

## Realistic Benchmark

The repository includes a small company handbook benchmark with Markdown docs, questions, and expected answers.

Generate a baseline run using the built-in keyword retriever:

```bash
PYTHONPATH=src python -m rag_doctor.cli retrieve \
  benchmarks/company_handbook/docs \
  benchmarks/company_handbook/questions.jsonl \
  benchmarks/company_handbook/expected.jsonl \
  --output outputs/company_handbook_baseline.jsonl
```

Diagnose that generated run:

```bash
PYTHONPATH=src python -m rag_doctor.cli diagnose \
  outputs/company_handbook_baseline.jsonl \
  --output outputs/company_handbook_report.md
```

The keyword retriever is intentionally simple and transparent. It is a baseline for learning and regression testing, not a production semantic search engine.

## Input Format

Each JSONL line is one evaluation case:

```json
{
  "id": "case-001",
  "question": "How many days after a trip can an employee submit an expense report?",
  "expected_answer": "Employees must submit expense reports within 30 days after the trip ends.",
  "retrieved_chunks": [
    {
      "id": "reimbursement.md#chunk-2",
      "source": "reimbursement.md",
      "text": "Employees must submit expense reports within 30 days after the trip ends."
    }
  ],
  "actual_answer": "Employees must submit expense reports within 30 days after the trip ends.",
  "citations": ["reimbursement.md#chunk-2"]
}
```

## Roadmap

See [docs/vision.md](docs/vision.md) for the project scope, non-goals, core concepts, and phased roadmap.

- Compare two experiment runs and highlight regressions.
- Expand the realistic benchmark and keyword retriever.
- Add adapters for Langfuse, Phoenix, DeepEval, and Ragas exports.
- Add optional LLM-as-judge scoring for semantic grounding.
- Add GitHub PR comment output for CI workflows.

## Development

This project starts with deterministic heuristics so the core can run locally and be tested reliably. LLM-based diagnosis will be added as an optional layer, not as the foundation.

## Current Limits

The current MVP uses simple deterministic checks, with special attention to numbers, percentages, citations, and obvious conflicts. It is useful for building the diagnosis workflow, but it is not yet a semantic evaluator. The next meaningful step is to add optional LLM-as-judge checks and compare them against deterministic results.
