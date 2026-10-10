# Research Paper Navigator

Ask questions about the included research papers and receive answers with source passages. The system combines vector search, keyword search (BM25), and a graph of paper metadata and references. A tool-using agent can gather evidence across several steps.

A small-model input check rejects unrelated requests and instruction attacks before cache lookup, retrieval, or planning. It asks for clarification when no subject is identifiable. Input filtering also helps remove persona overrides and forged paper blocks. A semantic answer cache reuses answers to similar questions, while a router chooses between a simple retrieval request and the full agent to reduce repeated work and model cost.

## Included files

| File or folder | Purpose |
| --- | --- |
| `research_paper_rag.py` | Application, retrieval tools, safeguards, caching, and measurement commands. |
| `ResearchPapers/` | Research PDF corpus. |
| `annotatedResearchPapers.json` | Paper metadata and relationships used by the graph tools. |
| `.rag_indexes/research_papers/` | Existing Chroma vector index, including its `.index_ready` marker. |
| `requirements.txt` | Pinned Python dependencies. |
| `.env` | Local OpenRouter API key. Keep this file private. |

## Install

Use Python 3.14 (the version used to verify this project), an internet connection, and an OpenRouter account with API credit. From the directory containing `capstone_project`, enter it before installing:

```bash
cd capstone_project
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate` instead. The dependencies provide Chroma storage, LangChain model and document support, LangGraph agent execution, NetworkX graphs, PyMuPDF PDF loading, and Pydantic validation.

## Configure

Set your OpenRouter API key in `.env`:

```dotenv
OPENROUTER_API_KEY=your_openrouter_key
```

An existing `OPENROUTER_API_KEY` environment variable takes precedence over `.env`. The script reads only that key from `.env`; set optional path overrides in your shell, not in `.env`.

| Environment variable | Default / purpose |
| --- | --- |
| `OPENROUTER_API_KEY` | Required for questions and experiments. Used for chat and embedding calls. |
| `OPENROUTER_ENV_FILE` | Optional location of the key file; defaults to `.env` beside the script. |
| `RESEARCH_PAPERS_DIR` | Optional PDF folder; defaults to `ResearchPapers` beside the script. |
| `RESEARCH_ANNOTATIONS` | Optional metadata file; defaults to `annotatedResearchPapers.json` beside the script. |
| `RESEARCH_INDEX_DIR` | Optional existing index folder; defaults to `.rag_indexes/research_papers` beside the script. |

No path overrides are needed for the included data. If you use them, absolute paths are easiest to manage. Relative overrides resolve from the directory where you run the command.

Requests use `https://openrouter.ai/api/v1`. The account needs access to `openai/gpt-5.4-nano` for input filtering, `openai/gpt-5-nano` for input checks, routing, and validation, `openai/gpt-5.4-mini` for regular answers, `openai/gpt-5.4` for fallback answers, and `openai/text-embedding-3-small` for embeddings. Model settings are constants in the script, not command-line options.

## Run

Run all commands below **inside `capstone_project`**, where `research_paper_rag.py` is located, with the virtual environment activated. In a new terminal, enter that folder and activate it first:

```bash
cd capstone_project
source .venv/bin/activate
```

If your terminal is already inside `capstone_project`, skip the `cd` command. Check installation and deterministic input filtering without making API calls:

```bash
python research_paper_rag.py --self-check
```

Ask one question:

```bash
python research_paper_rag.py --query "What is CVC4SY and how does it search for synthesis solutions?"
```

The script loads the corpus and index, prints the answer with source labels, then prints the route, stop reason, elapsed query time, and estimated chat cost. The first startup parses the PDFs and saves their chunks and BM25 keyword index in `.rag_indexes/research_papers/keyword_index.json`. Later starts load that data instead of parsing and tokenizing the corpus again. The vector index is reused without re-embedding.

Save an answer together with its evidence and measurements:

```bash
python research_paper_rag.py --query "What is CEGIS?" --log results/cegis.json
```

Run the full agent without the cache and router:

```bash
python research_paper_rag.py --baseline --query "What is CEGIS?" --log results/cegis-baseline.json
```

Choose a separate cache, then repeat a question to observe reuse:

```bash
python research_paper_rag.py --cache-dir caches/demo --query "What is CEGIS?"
python research_paper_rag.py --cache-dir caches/demo --query "What is CEGIS?"
```

### Interactive chat

```bash
python research_paper_rag.py --chat --log results/chat-01.json
```

Ask questions at the `You:` prompt. Follow-ups can refer to the previous subject:

```text
You: What is CEGIS?
You: How does it use counterexamples?
You: /reset
You: What is CVC4SY?
You: /exit
```

Every turn passes through the input check with recent conversation context. Only accepted, sanitized questions and their answers enter that context. Rejected turns stay in the saved transcript for review but do not enter the model's history. History helps interpret questions; answers still require paper evidence.

The first question can use the cache and router. Once there is conversation history, questions go through the full agent and skip cache reads and writes to avoid sharing context-dependent answers between conversations. `/reset` clears history but keeps the loaded corpus and persistent cache. Use `--baseline` with `--chat` to disable caching and routing throughout.

To test context poisoning, ask a research question, attempt a role change or instruction override in a later turn, then ask a legitimate follow-up. Review `input_decision`, `history_messages`, `calls`, and `evidence` in the log. A rejected attack should make no retrieval or answer-generation calls, and the next answer should retain the research context without adopting the requested role. This is a representative check, not a security guarantee.

### All command-line options

Choose exactly one action: `--query`, `--chat`, `--experiment`, or `--self-check`.

| Option | What it does |
| --- | --- |
| `-h`, `--help` | Shows command usage and exits. |
| `--query "QUESTION"` | Answers one independent question. By default, input filtering, caching, and routing are enabled. Use `--chat` for a conversation. |
| `--chat` | Starts a conversation and keeps the corpus and agent loaded. Uses the last three accepted question/answer pairs as context. `/reset` clears that context; `/exit`, `exit`, `quit`, Ctrl+C, or end-of-input ends the session. |
| `--baseline` | With `--query` or `--chat`, disables both the answer cache and router and uses the full agent. The input check and security filters remain enabled. It does not select the stronger fallback model. |
| `--cache-dir PATH` | With `--query` or `--chat`, chooses persistent answer-cache storage. Defaults to `.semantic_cache` beside the script. A new path starts an empty cache. Has no effect with `--baseline`. |
| `--log PATH` | With `--query`, saves one JSON result; with `--chat`, saves a JSON list updated after each turn, including rejections, errors, and reset events. Results contain the question, answer, source evidence, model calls, token usage, routing and cache decisions, latency, and estimated chat cost. Creates parent folders but refuses to overwrite an existing file. |
| `--experiment PATH` | Runs the fixed comparison described below and saves its results in a **new** directory. Refuses an existing output directory. Uses its own cache and phase settings; `--baseline`, `--cache-dir`, and `--log` do not customize the experiment. |
| `--self-check` | Checks angle-bracket escaping and forged-paper-block removal, then exits. Requires installed dependencies but no API key or corpus. Other options have no effect on these checks. This is not a complete security evaluation. |

Saved query results include `input_decision`: `allow`, `out_of_scope`, `malicious`, `clarify`, or `unavailable`. Blocked requests use route `rejected`, have no source evidence, and make no embedding or answer-generation calls. The input check itself is a paid model call.

Relative command-line paths resolve from the current working directory. Default data and cache paths resolve from the script's directory.

### Collect comparison evidence

```bash
python research_paper_rag.py --experiment results/comparison-01
```

This makes paid API calls for a fixed set of questions:

1. Four questions with the cache and router disabled (baseline).
2. The same four questions with routing and an initially empty cache (cold).
3. Those four again using the saved cache (warm).
4. One paraphrased question and two security examples.
5. A separate check of whether the cache validator accepts a question with a missing subject.

The output directory contains `results.json` and its `.semantic_cache/`.

The JSON includes full answers, supporting passages, token counts by model, elapsed time, estimated cost, cache decisions, stop reasons, and the script's SHA-256 hash. It is updated after each question. Failed question calls are recorded as errors rather than successful answers. Use a different output directory for each comparison.

Review answer quality and supporting passages alongside the cost and latency figures. A cache hit alone does not demonstrate a correct answer.

### Startup data

Parsed chunks and BM25 statistics are saved automatically beside the vector index. The script rebuilds them when PDF filenames, sizes, or modification times change, or when parsing, chunking, tokenizer settings, or relevant library versions change. Missing or unreadable saved data is rebuilt. To force a rebuild, delete only `keyword_index.json` before starting the script.

The paper graph is built from its small annotation file at startup. The saved keyword data does not update the vector index: if you change the corpus, keep the vector index and annotations aligned with it. File-change detection uses metadata, so a change that preserves both file size and modification time requires a manual rebuild.

## Limitations and reviewer notes

- **Safeguards are incomplete.** The initial input check can misclassify requests. If that check fails or returns an invalid decision, the request stops without a search. The later persona filter can miss instructions and fails open if its model call fails. The context validator can accept an ambiguous question. These checks reduce some attacks but do not guarantee security.
- **Incomplete answers can be cached.** Candidate cache hits are validated, but the cache can still reuse an incomplete or incorrect answer. Its similarity threshold is 0.85, capacity is 400 entries, and the oldest entries are evicted. It has no automatic expiry; use a fresh cache after changing the corpus or answer behavior.
- **The agent can stop with `invalid_plan`.** Some plans conflict with evidence-coverage rules or request an answer before new evidence is gathered. The resulting answer may be guarded or incomplete; inspect the stop reason and evidence in the saved result.
- **Cold requests may cost more or take longer.** Routing, validation, and fallback add model calls. The strongest savings are expected for reusable cached answers, not every question.
- **Costs are estimates.** The script uses recorded model rates dated October 10, 2026, charges input at full rates, and excludes embedding costs. Query timing excludes initial corpus/index loading. Experiment results use one run per question and phase, so they are not stable latency benchmarks or billing totals.
- **The corpus and index must stay aligned.** This script does not build or refresh the vector index. Keep the included PDFs, annotations, and index together. Replacing PDFs alone will not update vector search. Missing index data or `.index_ready` prevents startup.
- **API access is required.** Questions and experiments send questions and selected paper passages to OpenRouter-hosted models. Network failures, unavailable models, or insufficient credit can prevent answers. Keep `.env` out of shared submissions and supply a reviewer's own key when distributing the folder.

If startup reports a missing key, check `.env` or the environment variable. If it reports a missing index, confirm the hidden `.rag_indexes` directory was copied. If an output path already exists, choose a new filename or experiment directory.
