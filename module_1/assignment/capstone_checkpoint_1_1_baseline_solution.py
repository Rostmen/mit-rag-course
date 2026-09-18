"""Capstone Checkpoint 1.1 retrieval solution.
Jupytext-style cell markers (# %% / # %% [markdown]) — runnable as a
plain script AND openable as cells in VS Code / PyCharm / Jupytext.
"""

# %% [markdown]
# # Capstone Checkpoint 1.1 — Evaluating When Retrieval is Required
# **MO-LLM Module 1 / Required Capstone Checkpoint (120 minutes)**
#
# ## What this checkpoint is
#
# This is the first checkpoint of your **capstone project**, which you build across the whole program. Here you establish the **no-retrieval baseline**: you test how a plain LLM behaves on your chosen scenario *before* adding any retrieval, document where it falls short, and argue whether (and why) retrieval is needed.
#
# This mirrors **Lab 1.1** — where you probed an LLM for five failure modes — but now applied to the realistic corpus you'll build your system on. The deliverable is a **400-550-word written analysis** (see the final section); this notebook is the tool that produces the evidence for that writeup.
#
# **Learning outcomes (same as Lab 1.1):**
# 1. Implement a basic application that interacts with an LLM via an API.
# 2. Explain key limitations of LLMs that affect reliability and grounding.
# 3. Determine when external retrieval is required for a given use case.
# 4. Explain how the specificity, relevance, and accuracy of retrieved information affect output quality.
#
# **Important:** This checkpoint uses **no retrieval and no document parsing**. You are deliberately testing the LLM *without* access to your corpus, so you can see what it gets wrong. Loading and indexing your documents comes in Checkpoint 2.1.

# %% [markdown]
# ## Step 1 — Choose your scenario (keep it for the whole program)
#
# Pick **one** of the two capstone scenarios. You will use the same scenario for every checkpoint from here on.
#
# | Scenario | Corpus | What your system must eventually do |
# |---|---|---|
# | **Research Paper Navigator** | ~150 research-paper PDFs (`Labs/CapstoneDatasets/ResearchPapers/`) | Answer questions about the papers and **quote them directly**; handle single-paper and cross-paper questions (compare ideas, trace how an idea evolved); maintain conversation history. |
# | **Wikipedia Retrieval Engine** | ~2,400 Wikipedia HTML articles (`Labs/CapstoneDatasets/Wikipedia/`) | Answer questions about significant figures/places and **back answers with direct quotes** from the articles; handle single-article and cross-article questions; maintain conversation history. |
#
# Both model the same real-world pattern: a chat interface over a large body of complex documents where answers must be **grounded and quotable**, not just fluent.
#
# Set `SCENARIO` below to the one you chose.

# %% [markdown]
# ## Setup (~5 min)
#
# 1. **Python 3.11 or 3.12.**
# 2. `pip install langchain-openai langchain-core python-dotenv`
# 3. Get a free OpenRouter key at <https://openrouter.ai/keys> (this checkpoint uses the paid gpt-5.4-mini chat model — covered by your course credits — and no embeddings).
# 4. Create a `.env` file next to this script: `OPENROUTER_API_KEY=sk-or-v1-...`
#
# You do **not** need to download or parse the corpus for this checkpoint — you only need to look at a few documents to write realistic prompts (open a couple of PDFs/articles in the dataset folder by hand).

# %%
from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# %%
def assignment_dir() -> Path:
    if "__file__" in globals():
        return Path(__file__).resolve().parent

    cwd = Path.cwd()
    project_assignment_dir = cwd / "module_1" / "assignment"
    if project_assignment_dir.exists():
        return project_assignment_dir

    return cwd


ASSIGNMENT_DIR = assignment_dir()
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "openai/gpt-5.4-mini"  # latest small OpenAI model, fast; covered by course credits
TEMPERATURE = 0.2
LOG_PATH = (
    ASSIGNMENT_DIR
    / "checkpoint_1_1_responses_retrieval.log"
)

# === SET THIS to your chosen scenario ===
SCENARIO = "research_papers"   # "research_papers" or "wikipedia"

SYSTEM_PROMPT = """
You are a grounded research assistant.

Answer using only the retrieved context below.

Requirements:
- Do not use unsupported facts from your general knowledge.
- Cite supporting passages using labels such as [Source 1] and location of the file.
- When the user requests a quote, copy the wording exactly from the context.
- If the retrieved context does not contain enough information, say that the
  available documents do not provide enough information.
- Do not invent quotations, document names, authors, page numbers, or citations.

Retrieved context:
{context}
"""
# %%
def load_local_env() -> None:
    """Load OPENROUTER_API_KEY from a nearby .env file without extra packages."""

    env_paths = [
        ASSIGNMENT_DIR / ".env",
        Path.cwd() / ".env",
    ]

    for env_path in env_paths:
        if not env_path.exists():
            continue

        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip().strip('"').strip("'")

            if name == "OPENROUTER_API_KEY" and name not in os.environ:
                os.environ[name] = value


def check_api_key() -> str:
    load_local_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Grab a free key at "
            "https://openrouter.ai/keys, put it in a .env file next to this "
            "script, and rerun."
        )
    return key


def build_chain() -> Any:
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        api_key=check_api_key(),
        base_url=OPENROUTER_BASE_URL,
    )

    vector_store = get_vector_store(SCENARIO)

    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,
            "fetch_k": 20,
        },
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])

    get_question = RunnableLambda(
        lambda input_value: input_value["question"]
    )

    chain = (
        {
            "question": get_question,
            "context": (
                get_question
                | retriever
                | RunnableLambda(format_retrieved_documents)
            ),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def ask(chain: Any, question: str) -> str:
    return chain.invoke({"question": question})


def log_response(scenario: str, prompt: str, response: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    entry = (
        f"[{ts}]  SCENARIO={scenario}  MODEL={LLM_MODEL}\n"
        f"PROMPT:   {prompt}\n"
        f"RESPONSE: {response}\n"
        f"{'-' * 72}\n"
    )
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(entry)

# %% [markdown]
# ## Step 2 — Baseline probe prompts (provided examples)
#
# Below are example prompts for each scenario. They deliberately ask about **specific content in your corpus** and demand **direct quotes** — exactly what a grounded system must do, and exactly what a plain LLM struggles with. A no-retrieval model will tend to:
#
# - **hallucinate** specifics (fabricate a paper's results, a date, a quote),
# - **hedge** ("I don't have access to that document"),
# - or give a **generic** answer that doesn't actually quote the source.
#
# These three behaviors are your evidence that retrieval is required. Read the responses critically — a fluent answer is not necessarily a correct one.

# %%
# Example baseline prompts per scenario. These reference REAL documents in the
# capstone datasets so you can check the model's answers against the source.
EXAMPLE_PROMPTS = {
    "research_papers": [
        # Asks for a specific finding from a specific paper in the collection.
        "In the paper 'The Counterfeit Conundrum: Can Code Language Models "
        "Grasp the Nuances of Their Incorrect Generations?' (Gu et al., ACL "
        "2024), what is the main finding about how code models perceive their "
        "own incorrect generations? Quote the relevant sentence.",
        # Asks to compare across papers — impossible without the corpus.
        "Compare how Solar-Lezama's 'The Sketching Approach to Program "
        "Synthesis' and other program-synthesis papers in this collection "
        "define the synthesis problem. Cite each paper.",
        # Asks for a verbatim quote — a no-retrieval model cannot reliably do this.
        "Quote, word for word, the first sentence of the abstract of "
        "'The Sketching Approach to Program Synthesis'.",
    ],
    "wikipedia": [
        # Asks for a current fact that may be stale in the model's training.
        "According to the Wikipedia article on the 100 meters, what is the "
        "current men's world record, who holds it, and when was it set? "
        "Quote the article.",
        # Asks for a verbatim quote from a specific article.
        "Quote the opening sentence of the Wikipedia article titled "
        "'13 (2010 film)'.",
        # Asks for an aggregated answer across articles.
        "List three significant events recorded in the Wikipedia article for "
        "the year 1580, quoting the article for each.",
    ],
}

BASE_DIR = ASSIGNMENT_DIR

# Use this if ResearchPapers and Wikipedia are next to the script.
DATA_DIRS = {
    "research_papers": BASE_DIR / "ResearchPapers",
    "wikipedia": BASE_DIR / "Wikipedia",
}

INDEX_ROOT = BASE_DIR / ".rag_indexes"
EMBEDDING_MODEL = "openai/text-embedding-3-small"


def load_corpus(scenario: str) -> list[Document]:
    """Load PDFs or HTML files for the selected scenario."""

    if scenario not in DATA_DIRS:
        raise ValueError(f"Unknown scenario: {scenario}")

    corpus_dir = DATA_DIRS[scenario]

    if not corpus_dir.exists():
        raise FileNotFoundError(
            f"Dataset folder does not exist: {corpus_dir}\n"
            "Update DATA_DIRS so it points to your dataset."
        )

    documents: list[Document] = []

    import time

    if scenario == "research_papers":
        paths = sorted(corpus_dir.rglob("*.pdf"))
        total = len(paths)

        print(f"Found {total} PDF files", flush=True)

        for index, path in enumerate(paths, start=1):
            started = time.perf_counter()

            print(
                f"[{index}/{total}] Loading {path.name}...",
                flush=True,
            )

            try:
                pages = PyMuPDFLoader(str(path)).load()

                pages = [
                    page
                    for page in pages
                    if page.page_content.strip()
                ]

                for page in pages:
                    page.metadata["source"] = str(path)
                    page.metadata["file_name"] = path.name

                documents.extend(pages)

                elapsed = time.perf_counter() - started
                print(
                    f"    Loaded {len(pages)} pages in "
                    f"{elapsed:.1f} seconds",
                    flush=True,
                )

            except Exception as error:
                print(
                    f"    Could not load {path.name}: {error}",
                    flush=True,
                )

    elif scenario == "wikipedia":
        paths = sorted(corpus_dir.rglob("*.html"))

        for path in paths:
            try:
                html = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
                soup = BeautifulSoup(html, "html.parser")

                for element in soup(
                    ["script", "style", "noscript", "nav", "footer"]
                ):
                    element.decompose()

                title = (
                    soup.title.get_text(" ", strip=True)
                    if soup.title
                    else path.stem
                )

                text = soup.get_text("\n", strip=True)

                if text:
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": str(path),
                                "file_name": path.name,
                                "title": title,
                            },
                        )
                    )

            except Exception as error:
                print(f"Could not load {path.name}: {error}")

    if not documents:
        raise RuntimeError(
            f"No documents were loaded from {corpus_dir}"
        )

    print(
        f"Loaded {len(documents)} document/page objects "
        f"from {corpus_dir}"
    )
    return documents


def embedding_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=check_api_key(),
        base_url=OPENROUTER_BASE_URL,
        check_embedding_ctx_length=False,
        chunk_size=64,
        request_timeout=60,
        max_retries=2,
    )


def get_vector_store(scenario: str) -> Chroma:
    """Load an existing index or create it on the first run."""

    index_dir = INDEX_ROOT / scenario
    ready_file = index_dir / ".index_ready"
    collection_name = f"capstone_{scenario}"

    embeddings = embedding_model()

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(index_dir),
    )

    if ready_file.exists():
        print(f"Using existing vector index: {index_dir}")
        return vector_store

    print(f"Creating vector index for {scenario}...")

    documents = load_corpus(scenario)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks")

    import hashlib
    import time

    chroma_batch_size = 1000
    total_chunks = len(chunks)
    total_batches = (
        total_chunks + chroma_batch_size - 1
    ) // chroma_batch_size

    print(
        f"Adding {total_chunks} chunks to Chroma "
        f"in {total_batches} batches...",
        flush=True,
    )

    for batch_number, start in enumerate(
        range(0, total_chunks, chroma_batch_size),
        start=1,
    ):
        batch = chunks[start:start + chroma_batch_size]

        ids = []

        for offset, document in enumerate(batch):
            chunk_index = start + offset

            identity = (
                f"{scenario}|"
                f"{chunk_index}|"
                f"{document.metadata.get('source', '')}|"
                f"{document.metadata.get('page', '')}|"
                f"{document.page_content}"
            )

            ids.append(
                hashlib.sha256(
                    identity.encode("utf-8")
                ).hexdigest()
            )

        started = time.perf_counter()

        print(
            f"[{batch_number}/{total_batches}] "
            f"Processing chunks {start + 1}-"
            f"{start + len(batch)}...",
            end="",
            flush=True,
        )

        vector_store.add_documents(
            documents=batch,
            ids=ids,
        )

        elapsed = time.perf_counter() - started

        print(
            f" completed in {elapsed:.1f}s",
            flush=True,
        )

    index_dir.mkdir(parents=True, exist_ok=True)
    ready_file.write_text(
        f"scenario={scenario}\nchunks={len(chunks)}\n",
        encoding="utf-8",
    )

    print(f"Saved vector index to: {index_dir}")
    return vector_store


def format_retrieved_documents(
    documents: list[Document],
) -> str:
    blocks: list[str] = []

    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        source = metadata.get(
            "file_name",
            metadata.get("source", "Unknown source"),
        )

        page = metadata.get("page_label")

        if page is None:
            page_number = metadata.get("page")
            if isinstance(page_number, int):
                page = page_number + 1

        location = source
        if page is not None:
            location += f", page {page}"

        blocks.append(
            f"[Source {index}: {location}]\n"
            f"{document.page_content}"
        )

    return "\n\n".join(blocks)

# %% [markdown]
# ## Step 3 — Add your own probe prompts (TODO)
#
# The examples are a starting point. **Your turn:** write three of your own prompts for the scenario you chose. Good probes for this checkpoint:
#
# - Ask about a **specific fact** that lives in exactly one document in your corpus (open a paper/article and pick something concrete).
# - Ask for a **verbatim quote** from a named source — watch whether the model fabricates one.
# - Ask a **cross-document** question (compare two papers, or aggregate across articles).
# - Ask something **outside** the corpus to see whether the model admits it doesn't know.
#
# Return a list of prompt strings. Look at a few real documents in `Labs/CapstoneDatasets/` first so you can check the answers against ground truth.

# %%
def my_probe_prompts() -> list[str]:
    """Return 3-5 of YOUR OWN baseline prompts for your chosen scenario.

    TODO — your turn. See the guidance above. Each item is a prompt string.
    Open a few real documents in Labs/CapstoneDatasets/ so you can judge
    whether the model's answers are accurate.

    Delete the raise NotImplementedError line once your code works.
    """
    my_probes_list = [
        "What leads neural network to get stuck in a local minimum, and what helps resolve it?",
        "What is the proof of Motif Identifiability Theorem?",
        "What's self-repair for code generation?",
        "What's the oil price now?"
    ]

    return my_probes_list

# %% [markdown]
# ## Step 4 — Run the baseline probes and capture the evidence
#
# This runs the example prompts plus your own through the retrieval-backed LLM
# and logs every prompt/response to `checkpoint_1_1_responses.log`.

# %%
def run_probes() -> None:
    check_api_key()
    chain = build_chain()
    prompts = EXAMPLE_PROMPTS.get(SCENARIO, []) + my_probe_prompts()

    print(f"Capstone Checkpoint 1.1 — retrieval mode")
    print(f"Scenario: {SCENARIO}  |  Model: {LLM_MODEL}")
    print(f"Logging to: {LOG_PATH.name}\n")

    for i, prompt in enumerate(prompts, start=1):
        print("=" * 72)
        print(f"PROMPT {i}/{len(prompts)}: {prompt[:90]}...")
        try:
            answer = ask(chain, prompt)
        except Exception as e:
            print(f"  API error: {e}")
            continue
        print(f"\nRESPONSE:\n{answer}\n")
        log_response(SCENARIO, prompt, answer)

    print("=" * 72)
    print(
        "Done. Now READ each response against the real document. For each, "
        "note: did the model hallucinate, hedge, give a generic unsourced "
        "answer, or get it right? This is the evidence for your write-up."
    )


run_probes()

# %% [markdown]
# ## Step 5 — Your written analysis (the graded deliverable)
#
# The checkpoint deliverable is a **500-750 word written submission**, not code. Using the evidence in `checkpoint_1_1_responses.log`, address each of these (this is the required structure from the assignment):
#
# 1. **Describe your scenario** and the types of questions/tasks the system must support.
# 2. **Provide examples** of prompts and the model's outputs (paste 2-3 telling ones from your log).
# 3. **Identify key limitations** in the responses (hallucination, missing information, inconsistency, inability to quote).
# 4. **Describe patterns** you observed in model behavior.
# 5. **Explain whether retrieval is required** for this scenario and why.
# 6. **Describe what information** would need to be retrieved.
# 7. **Explain why precision and relevance** of retrieved information matter — and how these choices affect reliability and user trust.
#
# Focus on clear reasoning supported by specific examples. You'll revisit and refine this as you build the system in later checkpoints.
