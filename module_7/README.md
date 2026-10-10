# Module 7 — Research Paper Navigator

Use [research_paper_rag.py](assignment/research_paper_rag.py)
for research-paper retrieval. Retrieval, graph tools, evidence validation,
security, caching, routing, and measurement logic live in this one file.
Third-party dependencies are installed in the normal Python environment;
there are no imports from earlier assignment scripts.
The earlier `capstone_checkpoint_7_1_safe_agent.py` is the security-only checkpoint
retained so its recorded evidence remains reproducible.

## Run

Install dependencies from `assignment/requirements.txt` into `.venv`. The script
reads the corpus, annotations, and existing vector index from its directory.
Override these locations with `RESEARCH_PAPERS_DIR`, `RESEARCH_ANNOTATIONS`, and
`RESEARCH_INDEX_DIR`. Set `OPENROUTER_API_KEY` in the environment or the local
`.env` file (optionally selected by `OPENROUTER_ENV_FILE`). The local corpus and
`.env` links reuse the existing project data and credentials.

From the repository root:

```bash
# One question, using the persistent cache and router.
.venv/bin/python -B module_7/assignment/research_paper_rag.py --query 'What is CVC4SY?'

# The same full agent with cache and router disabled; security remains enabled.
.venv/bin/python -B module_7/assignment/research_paper_rag.py --baseline --query 'What is CVC4SY?'

# Optionally save a single answer and its measurements.
.venv/bin/python -B module_7/assignment/research_paper_rag.py --query 'What is CVC4SY?' --log /tmp/cvc4sy-result.json

# Worksheet experiment; output directory must be new.
.venv/bin/python -B module_7/assignment/research_paper_rag.py --experiment module_7/assignment/evidence/lab_7_2_repeat
```

The experiment runs four fixed questions through baseline, cold, and warm phases,
then a paraphrase and two security examples. It also checks rejection of a
context-dependent cached-answer request. It writes **one `results.json`** containing
answers, supporting passages, selected route, elapsed time, per-model tokens,
estimated chat cost, and cache decisions. API failures are recorded as skipped
questions, not successful answers. The cache directory is local runtime data,
excluded from Git. A new experiment directory ensures a cold cache; the warm
phase reopens the same persisted collection. Ordinary queries use
`assignment/.semantic_cache`; `--cache-dir PATH` selects another cache.

## Lab mapping

1. **Security (7.1):** XML compartments and trust hierarchy; escape angle brackets,
   strip explicit forged-paper blocks, then apply the plain-text
   `openai/gpt-5.4-nano` filter at temperature zero. Filtering fails open as in the
   lab and runs before cache lookup. Clarification sanitization remains in the
   full agent. The CLI uses independent questions; it has no interactive chat loop.
2. **Semantic cache (7.2):** persistent Chroma cosine collection, threshold 0.85,
   maximum 400 entries, oldest-first eviction, and a small-model validation on
   every candidate hit. Cached answers retain their source passages for citations.
3. **Router (7.2):** `openai/gpt-5-nano` selects direct versus full agent. Direct
   uses one hybrid retrieval and `openai/gpt-5.4-mini`; a satisfaction check sees
   both answer and evidence. Unsatisfactory direct answers escalate to the full
   agent using `openai/gpt-5.4`. Questions routed directly to the full agent use
   mini, as in the lab. Exact paper metadata and reference tasks replace the
   email lab's exact-date routing rule.
4. **Measurement (7.2):** compare full answers as well as per-model tokens, latency,
   and estimated cost. Current public OpenRouter rates are recorded in the script
   and results; the lab's illustrative prices are not used as actual rates.
   Estimates charge all input at full rate, exclude embeddings and initialization,
   and are not invoices.

The Module 1 vector index is reused without re-embedding. A Module 7 copy avoids
Chroma bookkeeping writes to earlier checkpoints. The existing full-agent
coverage checks and known `invalid_plan` fallback behavior are retained; cost
optimization does not silently change those rules. As in the cache lab, completed
answers are stored even when imperfect, so validation is not a guarantee of
correctness, completeness, freshness, or freedom from prompt injection.

## Worksheet and evidence

- [Completed worksheet](assignment/capstone_checkpoint_7_1_worksheet_responses.md)
- [Performance/cost results and answers](assignment/evidence/lab_7_2/results.json)
- [Performance/cost evidence report](assignment/evidence/lab_7_2/report.md)
- [Earlier paired security evaluation](assignment/evidence/security_7_1_live/report.md)

The blank worksheet and earlier module files are preserved.
