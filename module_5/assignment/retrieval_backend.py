"""Capstone Checkpoint 4.1: decomposition and graph retrieval for ResearchPapers.

Copied from the Module 3 ResearchPaperRetriever baseline. Baseline search scoring,
chunking, embeddings, and answer prompt are retained for controlled comparisons.
Advanced retrieval adapts Labs 4.1 and 4.2; see research_graph.py for the graph.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_1_ASSIGNMENT_DIR = PROJECT_ROOT / "module_1" / "assignment"
ASSIGNMENT_DIR = Path(__file__).resolve().parent
RESEARCH_PAPERS_DIR = MODULE_1_ASSIGNMENT_DIR / "ResearchPapers"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = "openai/gpt-5.4-mini"
EMBEDDING_MODEL = "openai/text-embedding-3-small"
TEMPERATURE = 0.2

# Reuse the vector index created in Module 1 unless it is missing.
VECTOR_INDEX_DIR = ASSIGNMENT_DIR / ".rag_indexes" / "research_papers"
VECTOR_READY_FILE = VECTOR_INDEX_DIR / ".index_ready"
VECTOR_COLLECTION_NAME = "capstone_research_papers"

LOG_PATH = ASSIGNMENT_DIR / "checkpoint_5_backend_results.log"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
DEFAULT_TOP_K = 4
DEFAULT_CANDIDATE_POOL = 12
DEFAULT_BM25_WEIGHT = 0.45
DEFAULT_VECTOR_WEIGHT = 0.55

STOPWORDS = {
    "a", "an", "the", "and", "but", "or", "nor", "so", "yet", "for",
    "in", "on", "at", "to", "of", "by", "with", "from", "into", "upon",
    "about", "above", "below", "between", "through", "during", "before",
    "after", "under", "over", "around", "along", "across", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "i", "we", "you", "he", "she", "it", "they", "me",
    "us", "him", "her", "them", "my", "our", "your", "his", "its",
    "their", "this", "that", "these", "those", "as", "if", "up", "out",
    "not", "no", "what", "which", "who", "how", "why", "when",
}

EXAMPLE_QUERIES = [
    "Quote the first sentence of the abstract of The Sketching Approach to Program Synthesis.",
    "What is the proof idea of the Motif Identifiability Theorem?",
    "How do code generation systems repair their own incorrect outputs?",
    "Compare how papers in this collection define program synthesis.",
    "What is the current oil price?",
]

SYSTEM_PROMPT = """
You are a grounded research assistant for a Research Paper Navigator.

Answer using only the retrieved research-paper context provided by the user.

Requirements:
- Cite supporting passages using source labels such as [Source 1].
- If the retrieved context does not contain enough information, say that the
  available documents do not provide enough information.
- Do not invent quotations, document names, authors, page numbers, or citations.
- When the user requests a quote, copy only wording that appears in the context.
- Answer directly without adding follow-up offers.
"""


@dataclass(frozen=True)
class RetrievalResult:
    document: Document
    score: float
    source: str

    @property
    def result_id(self) -> str:
        page = self.document.metadata.get("page", "")
        identity = f"{self.source}|{page}|{self.document.page_content}"
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def load_local_env() -> None:
    """Load OPENROUTER_API_KEY from local .env files without printing secrets."""

    env_paths = [
        ASSIGNMENT_DIR / ".env",
        MODULE_1_ASSIGNMENT_DIR / ".env",
        PROJECT_ROOT / ".env",
    ]
    for env_path in env_paths:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip().strip('"').strip("'")
            if name == "OPENROUTER_API_KEY" and name not in os.environ:
                os.environ[name] = value


def require_api_key() -> str:
    load_local_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required for vector or hybrid retrieval. "
            "Add it to module_1/assignment/.env, module_4/assignment/.env, "
            "or the shell environment."
        )
    return key


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOPWORDS
    ]


def load_research_paper_pages() -> list[Document]:
    if not RESEARCH_PAPERS_DIR.exists():
        raise FileNotFoundError(f"Missing corpus directory: {RESEARCH_PAPERS_DIR}")

    documents: list[Document] = []
    paths = sorted(RESEARCH_PAPERS_DIR.glob("*.pdf"))
    print(f"Found {len(paths)} research paper PDFs.")

    for index, path in enumerate(paths, start=1):
        print(f"[{index}/{len(paths)}] Loading {path.name}...", flush=True)
        try:
            pages = PyMuPDFLoader(str(path)).load()
        except Exception as error:
            print(f"    Skipping {path.name}: {error}")
            continue

        for page in pages:
            if not page.page_content.strip():
                continue
            page.metadata["source"] = str(path)
            page.metadata["file_name"] = path.name
            documents.append(page)

    if not documents:
        raise RuntimeError(f"No PDF pages were loaded from {RESEARCH_PAPERS_DIR}")

    print(f"Loaded {len(documents)} PDF pages.")
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"Prepared {len(chunks)} retrieval chunks.")
    return chunks


def embedding_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=require_api_key(),
        base_url=OPENROUTER_BASE_URL,
        check_embedding_ctx_length=False,
        chunk_size=64,
        request_timeout=60,
        max_retries=2,
    )


def chunk_id(document: Document, chunk_index: int) -> str:
    identity = (
        f"research_papers|{chunk_index}|"
        f"{document.metadata.get('source', '')}|"
        f"{document.metadata.get('page', '')}|"
        f"{document.page_content}"
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def build_or_load_vector_store(chunks: list[Document] | None = None) -> Chroma:
    vector_store = Chroma(
        collection_name=VECTOR_COLLECTION_NAME,
        embedding_function=embedding_model(),
        persist_directory=str(VECTOR_INDEX_DIR),
    )

    if VECTOR_READY_FILE.exists():
        print(f"Reusing existing vector index: {VECTOR_INDEX_DIR}")
        return vector_store

    raise RuntimeError("Module 5 requires a copied ready index; run prepare_checkpoint_5.py first. No re-embedding is performed.")


class BM25Index:
    """Small BM25 implementation to avoid adding a dependency for the checkpoint."""

    def __init__(self, documents: list[Document], k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.term_counts = [Counter(tokenize(doc.page_content)) for doc in documents]
        self.lengths = [sum(counts.values()) for counts in self.term_counts]
        self.avgdl = sum(self.lengths) / max(len(self.lengths), 1)
        self.doc_freqs: Counter[str] = Counter()

        for counts in self.term_counts:
            self.doc_freqs.update(counts.keys())

        self.doc_count = len(documents)

    def score(self, query: str, index: int) -> float:
        query_tokens = tokenize(query)
        if not query_tokens:
            return 0.0

        score = 0.0
        counts = self.term_counts[index]
        doc_len = self.lengths[index] or 1

        for term in query_tokens:
            freq = counts.get(term, 0)
            if freq == 0:
                continue
            df = self.doc_freqs.get(term, 0)
            idf = math.log(1 + ((self.doc_count - df + 0.5) / (df + 0.5)))
            denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * ((freq * (self.k1 + 1)) / denominator)

        return score

    def top_k(self, query: str, k: int) -> list[RetrievalResult]:
        scored = [
            RetrievalResult(
                document=document,
                score=self.score(query, index),
                source=document.metadata.get("file_name", "unknown"),
            )
            for index, document in enumerate(self.documents)
        ]
        scored.sort(key=lambda result: result.score, reverse=True)
        return [result for result in scored[:k] if result.score > 0]


class ResearchPaperRetriever:
    def __init__(
        self,
        bm25_weight: float = DEFAULT_BM25_WEIGHT,
        vector_weight: float = DEFAULT_VECTOR_WEIGHT,
    ):
        chunks = split_documents(load_research_paper_pages())
        self.bm25 = BM25Index(chunks)
        self.vector_store = build_or_load_vector_store(chunks)
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

    def keyword_search(self, query: str, k: int) -> list[RetrievalResult]:
        return self.bm25.top_k(query, k)

    def vector_search(self, query: str, k: int) -> list[RetrievalResult]:
        raw_results = self.vector_store.similarity_search_with_score(query, k=k)
        return [
            RetrievalResult(
                document=document,
                score=float(distance),
                source=document.metadata.get("file_name", "unknown"),
            )
            for document, distance in raw_results
        ]

    def hybrid_search(
        self,
        query: str,
        k: int,
        candidate_pool: int = DEFAULT_CANDIDATE_POOL,
    ) -> list[RetrievalResult]:
        keyword_results = self.keyword_search(query, candidate_pool)
        vector_results = self.vector_search(query, candidate_pool)

        keyword_norm = normalize([result.score for result in keyword_results])
        vector_norm = normalize([result.score for result in vector_results], invert=True)

        candidates: dict[str, Document] = {}
        sources: dict[str, str] = {}
        scores: dict[str, float] = {}

        for result, normalized_score in zip(keyword_results, keyword_norm):
            candidates[result.result_id] = result.document
            sources[result.result_id] = result.source
            scores[result.result_id] = (
                scores.get(result.result_id, 0.0)
                + self.bm25_weight * normalized_score
            )

        for result, normalized_score in zip(vector_results, vector_norm):
            candidates[result.result_id] = result.document
            sources[result.result_id] = result.source
            scores[result.result_id] = (
                scores.get(result.result_id, 0.0)
                + self.vector_weight * normalized_score
            )

        fused = [
            RetrievalResult(
                document=candidates[result_id],
                score=score,
                source=sources[result_id],
            )
            for result_id, score in scores.items()
        ]
        fused.sort(key=lambda result: result.score, reverse=True)
        return fused[:k]

    def search(self, query: str, mode: str, k: int) -> list[RetrievalResult]:
        if mode == "keyword":
            return self.keyword_search(query, k)
        if mode == "vector":
            return self.vector_search(query, k)
        if mode == "hybrid":
            return self.hybrid_search(query, k)
        raise ValueError(f"Unsupported mode: {mode}")


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        api_key=require_api_key(),
        base_url=OPENROUTER_BASE_URL,
        timeout=90, max_retries=2,
    )


def normalize(scores: list[float], invert: bool = False) -> list[float]:
    if not scores:
        return []
    low = min(scores)
    high = max(scores)
    if high == low:
        values = [0.5 for _ in scores]
    else:
        values = [(score - low) / (high - low) for score in scores]
    return [1.0 - value for value in values] if invert else values


def page_label(document: Document) -> str:
    page = document.metadata.get("page_label")
    if page is not None:
        return str(page)

    page_number = document.metadata.get("page")
    if isinstance(page_number, int):
        return str(page_number + 1)

    return "unknown"


def excerpt(text: str, limit: int = 420) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[:limit].rsplit(" ", 1)[0] + "..."


def format_results(mode: str, query: str, results: list[RetrievalResult]) -> str:
    lines = [
        f"MODE: {mode}",
        f"QUERY: {query}",
        f"RESULT_COUNT: {len(results)}",
    ]

    for index, result in enumerate(results, start=1):
        lines.extend(
            [
                f"{index}. {result.source}, page {page_label(result.document)}",
                f"   score={result.score:.4f}",
                f"   excerpt={excerpt(result.document.page_content)}",
            ]
        )

    return "\n".join(lines)


def format_context(results: list[RetrievalResult]) -> str:
    blocks = []
    for index, result in enumerate(results, start=1):
        blocks.append(
            f"[Source {index}: {result.source}, page {page_label(result.document)}]\n"
            f"Retrieval role: {result.document.metadata.get('retrieval_role', 'primary')}\n"
            f"{result.document.page_content}"
        )
    return "\n\n---\n\n".join(blocks)


def generate_answer(llm: ChatOpenAI, query: str, results: list[RetrievalResult]) -> str:
    context = format_context(results)
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Retrieved context:\n{context}\n\nQuestion: {query}"),
        ]
    )
    return response.content if hasattr(response, "content") else str(response)


def append_log(text: str) -> None:
    ASSIGNMENT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}]\n{text}\n{'-' * 72}\n")


def run_query(
    retriever: ResearchPaperRetriever,
    query: str,
    mode: str,
    k: int,
    llm: ChatOpenAI | None = None,
) -> None:
    modes = ["hybrid", "decomposition", "graph", "combined"] if mode == "compare" else [mode]
    for selected_mode in modes:
        results = retriever.search(query, selected_mode, k)
        output = format_results(selected_mode, query, results)
        if llm is not None:
            answer = generate_answer(llm, query, results)
            output = f"{output}\n\nLLM_RESPONSE:\n{answer}"
        print(output)
        print()
        append_log(output)
        if hasattr(retriever, 'last_trace'):
            import json
            with (ASSIGNMENT_DIR / 'checkpoint_4_retrieval_traces.jsonl').open('a') as handle:
                handle.write(json.dumps(retriever.last_trace) + '\n')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Single retrieval query to run.")
    parser.add_argument(
        "--mode",
        choices=["keyword", "vector", "hybrid", "decomposition", "graph", "combined", "compare"],
        default="hybrid",
        help="Retrieval strategy; compare runs baseline and three advanced modes.",
    )
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--run-examples",
        action="store_true",
        help="Run the representative worksheet queries.",
    )
    parser.add_argument(
        "--reset-log",
        action="store_true",
        help="Clear the retrieval evidence log before writing this run.",
    )
    parser.add_argument(
        "--with-answers",
        action="store_true",
        help="After retrieval, call the chat model and log grounded answers.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.run_examples and not args.query:
        raise SystemExit("Provide --query or --run-examples.")

    if args.reset_log and LOG_PATH.exists():
        LOG_PATH.unlink()

    if args.top_k < 1:
        raise SystemExit('--top-k must be positive')
    if args.mode in {'keyword', 'vector', 'hybrid'}:
        retriever = ResearchPaperRetriever()
    else:
        from research_graph import AdvancedResearchPaperRetriever
        retriever = AdvancedResearchPaperRetriever()
    llm = build_llm() if args.with_answers else None
    queries = EXAMPLE_QUERIES if args.run_examples else [args.query]

    for query in queries:
        run_query(retriever, query, args.mode, args.top_k, llm=llm)

    print(f"Logged retrieval evidence to: {LOG_PATH}")


if __name__ == "__main__":
    main()
