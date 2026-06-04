# Company Handbook Benchmark

This benchmark is a small but realistic RAG fixture. It contains Markdown documents, benchmark questions, expected answers, and enough ambiguity to produce useful diagnosis cases.

The fixture intentionally includes:

- a current reimbursement policy
- an archived reimbursement policy with a conflicting deadline
- an onboarding document with vague expense guidance
- a security policy with multiple sections

Generate a baseline run with the transparent keyword retriever:

```bash
PYTHONPATH=src python -m rag_doctor.cli retrieve \
  benchmarks/company_handbook/docs \
  benchmarks/company_handbook/questions.jsonl \
  benchmarks/company_handbook/expected.jsonl \
  --output outputs/company_handbook_baseline.jsonl
```

Diagnose the generated run:

```bash
PYTHONPATH=src python -m rag_doctor.cli diagnose \
  outputs/company_handbook_baseline.jsonl \
  --output outputs/company_handbook_report.md
```

This benchmark is not meant to prove production quality. It exists to make retrieval, grounding, citation, and conflict failures reproducible while the project is still small.
