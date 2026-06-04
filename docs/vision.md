# RAG Doctor Vision

RAG Doctor is a lightweight failure diagnosis and regression testing toolkit for Retrieval-Augmented Generation systems.

The goal is not to become another chatbot, RAG framework, prompt manager, or full observability platform. The goal is narrower:

> Help developers understand why RAG answers fail, and turn those failures into reproducible, actionable engineering reports.

## Core Questions

RAG Doctor focuses on three questions:

1. Did retrieval find the evidence needed to answer the question?
2. Did generation use the retrieved evidence correctly?
3. Do the citations actually support the final answer?

Everything in the project should serve one of those questions.

## In Scope

- Diagnose RAG run outputs.
- Explain likely failure types.
- Generate Markdown and machine-readable reports.
- Compare two runs and highlight regressions.
- Provide realistic benchmark fixtures.
- Support CI workflows for RAG regression testing.
- Import data from existing tools such as Langfuse, Phoenix, Ragas, and DeepEval.

## Out of Scope

- General-purpose chatbot UI.
- Full RAG application framework.
- Prompt management platform.
- Agent orchestration framework.
- Long-term memory product.
- Model training or fine-tuning platform.
- Large observability dashboard.

## Core Concepts

- `Case`: one RAG question-answering example.
- `Run`: a collection of cases produced by one RAG configuration.
- `Diagnosis`: the failure analysis for one case.
- `Report`: a human-readable summary of diagnoses.
- `Benchmark`: reproducible docs, questions, expected answers, and run outputs.
- `Comparison`: a diff between two runs.
- `Adapter`: an importer from an external trace or evaluation format.

## Failure Types

The first stable set of failure types is:

- `pass`: the answer is supported by retrieved evidence.
- `retrieval_miss`: retrieval did not return the required evidence.
- `generation_miss`: retrieval found the evidence, but generation ignored or omitted it.
- `weak_grounding`: the answer is partially supported, but misses required facts.
- `citation_mismatch`: the cited chunks do not support the answer.
- `document_conflict`: retrieved chunks contain conflicting evidence for the same topic.

New failure types should only be added when they have a clear definition, tests, and actionable recommendations.

## Roadmap

### Phase 0: Diagnosis Core

Status: initial version complete.

- JSONL input.
- CLI command: `diagnose`.
- Markdown report output.
- Deterministic diagnosis rules.
- Unit tests and GitHub Actions.

### Phase 1: Realistic Benchmark

Status: initial version complete.

Add a reproducible benchmark fixture that looks like a real RAG workflow:

- `benchmarks/company_handbook/docs/`
- `questions.jsonl`
- `expected.jsonl`
- generated run outputs
- a simple keyword retriever

This makes examples less artificial and gives contributors a concrete system to reason about.

### Phase 2: Run Comparison

Add a `compare` command:

```bash
rag-doctor compare runs/baseline.jsonl runs/improved.jsonl --output outputs/comparison.md
```

The report should show improved, regressed, and unchanged cases.

### Phase 3: CI Regression Testing

Make RAG quality changes visible in pull requests:

- run benchmarks in GitHub Actions
- fail on unacceptable regressions
- generate PR-friendly Markdown reports

### Phase 4: Adapters

Import traces and evaluation outputs from existing tools instead of replacing them:

- Langfuse
- Phoenix
- Ragas
- DeepEval
- custom JSONL

### Phase 5: Optional UI

Build a small report viewer only after the data model and CLI are stable. The UI should help users inspect cases and comparisons, not become a large platform.

## Development Principles

1. Diagnosis first.
2. Reproducible by default.
3. CLI before UI.
4. Deterministic baseline first.
5. Integrate, do not replace.
6. Reports should be actionable.

These principles should keep the project focused as it grows.
