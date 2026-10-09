# Module 4 — Advanced retrieval for ResearchPapers

This checkpoint copies the Module 3 retrieval solution and adapts the two Module 4
labs to the existing 153-PDF research corpus. It targets incomplete evidence for
multi-paper questions, duplicate chunks, and relationships absent from a flat index.

## Deliverables

All capstone materials are under `assignment/`:

- `capstone_checkpoint_4_solution.py`: copied baseline, CLI, original chunking,
  hybrid scoring, embedding index, grounded answer prompt, and source formatting.
- `research_graph.py`: Lab 4.1 query decomposition and Lab 4.2 graph wrapper using
  the existing `ResearchPaperRetriever` as its hybrid search engine.
- `annotate_research_papers.py`: API annotation pipeline, with resumable per-PDF
  caches, bounded input, validated evidence, and schema retries.
- `annotatedResearchPapers.json`: model-generated annotations and extraction provenance.
- `capstone_checkpoint_4_evaluation_solution.py`: Module 3 evaluation adapted to
  compare hybrid, decomposition, graph, and combined retrieval.
- `capstone_checkpoint_4_test_inputs.json`: byte-for-byte copy of the fixed Module 3 cases.
- `checkpoint_4_comparison_results.csv`, `.json`, `.log`, `.manifest.json`: measurements,
  passage-level evidence and graph traces, answer/judge results, and run fingerprints.
- `capstone_checkpoint_4_worksheet_responses.md`: all worksheet prompts in order,
  completed after evaluation.
- `test_research_graph.py`: seven offline graph integrity and retrieval regression tests.
- `checkpoint_4_annotation_audit.json`: all 153 document hashes and 2,665 retained reference quotations checked against the source PDFs.
- `summarize_checkpoint_4.py`: recomputes aggregate measurements from saved evidence.

## Setup

Run commands from the repository root with the existing virtual environment:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Use `OPENROUTER_API_KEY` in the shell environment or the existing
`module_1/assignment/.env`; a Module 4 assignment `.env` is also supported.
The configured chat model is `openai/gpt-5.4-mini`, through OpenRouter, and the
embedding model is `openai/text-embedding-3-small`. Keys and caches remain ignored.
No direct OpenAI account key is required by this project configuration.

## Generate annotations

```bash
.venv/bin/python module_4/assignment/annotate_research_papers.py
```

The script makes model API calls for document annotation. A successful record is
reused when the PDF hash, model, and prompt version match. Four requests can run
concurrently; use `--workers 1` for serial processing. `--limit 2` runs a pilot and
writes a separate pilot output. Failed records are retried on the next run.

PDFs up to 100,000 extracted characters are supplied in full. Longer files use
front matter, ending pages, reference-bearing pages, and uniform samples within
that budget. Every record lists `pages_sent`, `page_count`, `sampled`, the document
hash, prompt/model versions, and successful-call usage. Some PDFs are entire
proceedings volumes despite paper-like filenames. Missing values stay null;
annotation coverage is not a claim of complete citation extraction. Usage totals
from stored records exclude failed/discarded attempts.

Reference evidence must match its stated PDF page after whitespace normalization.
The graph further requires the reference title to appear in that evidence and
resolve to an unambiguous annotated corpus title. External and ambiguous titles
are not traversable corpus links. Topic and method annotations are model-derived;
they are retrieval hints, never answer evidence.

## Retrieval architecture

```text
question → optional focused subqueries → existing hybrid chunk search
         → optional graph expansion → passage reranking and rank fusion
         → distinct-work/aspect selection within k → grounded answer
```

The graph uses paper, author, and topic nodes. Edges represent explicit work
references, shared topics/authors via their nodes, and validated same-title,
shared-author paper versions. Collections are excluded from version grouping.
Publication year is metadata; earlier publication does not imply influence.

Graph expansion uses five hybrid seed chunks, at most eight related documents per
query, and at most two candidate passages per related document. High-degree author
and topic hubs are suppressed. Related documents are ranked by query relevance;
only original PDF passages are eligible for the final context. Graph paths and
primary/context roles are logged. The answer prompt itself is unchanged from
Module 3, with the same role-label formatting across comparison modes.

Decomposition makes at most four focused searches. Invalid planning output or API
failure falls back to the original question. The original question also supplies
backup candidates when decomposition succeeds. Advanced modes share source/version
diversity handling; consequently their comparison with baseline measures the whole
retrieval redesign. Comparison among advanced modes helps isolate graph expansion.

```bash
.venv/bin/python module_4/assignment/capstone_checkpoint_4_solution.py --mode combined --top-k 3 --with-answers --query "Compare the evaluation design of LiveCodeBench and Bench-Push."
```

Use `--mode hybrid`, `decomposition`, `graph`, `combined`, or `compare`. Keyword and
vector modes remain available. Baseline modes do not require annotations. The
existing Module 1 vector index is reused without re-embedding the corpus.

## Evaluation and tests

```bash
.venv/bin/python -m unittest discover -s module_4/assignment -p 'test_*.py' -v
.venv/bin/python module_4/assignment/capstone_checkpoint_4_evaluation_solution.py --mode compare --top-k 3 --with-answers --judge
```

Add `--resume` to continue an interrupted evaluation with matching source and
configuration fingerprints. Completed cases are saved immediately. API failures
stop the run instead of being silently counted as retrieval failures.

The main comparison uses the same 20 questions, three final chunks, answer model,
and strict Module 3 judge. Original filename-based source metrics are preserved.
Supplementary canonical-work metrics apply the same annotation-derived version map
to every mode. Neither annotation nor retrieval receives expected sources or
reference answers. Timings exclude corpus initialization and include retrieval API
latency; the combined run can reuse a decomposition plan cached earlier in the run.
Token records cover answer, judge, and uncached planner calls; embedding usage is
not included. These are operational observations, not a controlled latency benchmark.

The judge is inherited from Module 3 and sees source filenames plus reference
notes, not full passages. It is therefore not an independent claim-level grounding
check. The corpus contains mislabeled files, alternate versions, and volumes;
strict expected-filename matches can understate useful evidence or count a source
whose selected passage is irrelevant. Read the saved passages alongside the scores.

This is an exploratory comparison on the existing development test set. A partial
pilot exposed a provenance-label issue, which was corrected before the final run;
the planner instruction was also clarified to keep subqueries focused on one subject.
There is no independent held-out evaluation, and model judgments can vary across runs.

## Recorded results

All modes used the same 20 questions and three final chunks:

| Mode | Any expected source / 14 | All expected sources / 14 | All expected works, version-aware / 14 | Answer judge passes / 20 | Refusal passes / 6 |
| --- | --- | --- | --- | --- | --- |
| hybrid | 12 | 5 | 5 | 8 | 4 |
| decomposition | 14 | 8 | 12 | 12 | 5 |
| graph | 14 | 7 | 10 | 10 | 3 |
| combined | 14 | 6 | 11 | 13 | 4 |

Decomposition had the best strict source coverage; combined had the most automated
answer passes. These are exploratory results, not proof that either strategy is
universally best. Graph-only retrieval worsened refusal behavior (3/6 vs. 4/6).
The historical Module 3 answer result was 9/20; the fresh paired baseline was 8/20.
No expected-source or reference-answer labels were changed.

Manual review detected a false-positive judge pass on the fresh baseline self-repair
answer: it attributes counterfeit-sample findings to LiveCodeBench, although the
selected passages do not mention LiveCodeBench. Aggregate counts preserve the
inherited judge's output. See the worksheet and saved passages for this limitation.
Graph and combined modes each selected eight graph-only passages across 20 cases;
many gains came from reranking/diversity of existing hybrid candidates. A further
reranking-only control is needed to establish the marginal benefit of traversal.

Seven offline tests pass. The final artifact audit verified all 80 comparisons,
all 240 returned passages against the source PDFs, the unchanged test inputs, and
matching source-code/annotation fingerprints. Recompute summaries and audits with:

```bash
.venv/bin/python module_4/assignment/summarize_checkpoint_4.py
.venv/bin/python module_4/assignment/audit_checkpoint_4.py
```
