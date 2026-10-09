# Module 6 — Security, reliability, and performance audit

This checkpoint audits the existing Module 5 Research Paper Navigator. No prompts,
tools, models, budgets, or previous capstone source files are changed. The worksheet
PDF governs scope; the supplied starter's hardening/demo instructions are not used
to introduce improvements or replace the research corpus with fictional emails.
Lab 6.1 supplies the run-and-document method: scripted attacks, fresh scenarios,
and retained conversation history within the staged attack.

## Deliverables

- [Completed worksheet](assignment/capstone_checkpoint_6_worksheet_responses.md)
- [Blank Markdown worksheet copy](assignment/capstone_checkpoint_6_worksheet_template.md)
- [Audit Python file](assignment/capstone_checkpoint_6_1_audit.py)
- [Inputs and observed outputs](assignment/evidence/transcript.md)
- [Raw traces and usage](assignment/evidence/runs.json)
- [Performance measurements](assignment/evidence/measurements.json)
- [Source fingerprints and run settings](assignment/evidence/manifest.json)

## Reproduce

Run from the repository root with the existing virtual environment and Module 5
module-local LangGraph dependencies:

```bash
.venv/bin/python -B module_6/assignment/capstone_checkpoint_6_1_audit.py
.venv/bin/python -B module_6/assignment/summarize_audit.py
```

The audit refuses to overwrite `evidence/runs.json`; preserve the existing evidence
before a rerun. It reads the API key from the existing environment or Module 1's
`.env` through the existing backend. Keys are never included in evidence. Research
papers remain in Module 1. The existing Module 1 vector index is copied to Module
6 before Chroma opens it, avoiding bookkeeping writes to earlier checkpoints;
no corpus re-embedding is performed. The audit sends test prompts and retrieved
passages to the existing OpenRouter service/model. No extra judge calls are used.

Token counts cover the requirement extraction, planner, coverage checker, and
answer calls. They exclude embedding usage; no billed dollar cost is claimed.
Query latency excludes initialization, which is recorded separately. One model
and one pass are sufficient for this worksheet, but do not establish general
security or production latency. Raw outputs are evidence, not instructions.
