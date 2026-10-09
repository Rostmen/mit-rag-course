"""Checkpoint 4.1: controlled evaluation adapted from the Module 3 harness.

Runs the identical 20 cases with three final chunks across hybrid, decomposition,
graph, and combined retrieval. Preserves Module 3 strict judge and source metrics;
adds version-aware coverage, passage evidence, traces, timing, and resumable output.
Run with --mode compare --top-k 3 --with-answers --judge.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from capstone_checkpoint_4_solution import (
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    ResearchPaperRetriever,
    build_llm,
    format_results,
    generate_answer,
    format_context,
    SYSTEM_PROMPT,
    load_local_env,
    page_label,
    require_api_key,
)


ASSIGNMENT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUTS_PATH = ASSIGNMENT_DIR / "capstone_checkpoint_4_test_inputs.json"
DEFAULT_RESULTS_CSV = ASSIGNMENT_DIR / "checkpoint_4_baseline_results.csv"
DEFAULT_RESULTS_LOG = ASSIGNMENT_DIR / "checkpoint_4_evaluation_results.log"
DEFAULT_VALIDATION_CSV = ASSIGNMENT_DIR / "checkpoint_4_validation_results.csv"
DEFAULT_VARIANTS_PATH = ASSIGNMENT_DIR / "capstone_checkpoint_4_test_inputs_variants.json"

SUPPORTED_MODES = ["hybrid", "decomposition", "graph", "combined"]

VARIANT_SYSTEM_PROMPT = (
    "You rephrase questions for an evaluation set. Given a question, produce "
    "alternative phrasings a real user might type while preserving the meaning "
    "so the SAME answer and grading notes still apply. Return one paraphrase "
    "per line, with no numbering or bullets."
)

JUDGE_SYSTEM_PROMPT = (
    "You are grading a retrieval-augmented answer for a research-paper navigator. "
    "Return exactly one label from pass or failure, followed by a short reason. "
    "Grade against the reference notes, not against outside knowledge. Use pass "
    "only when the answer is factually consistent, grounded in the retrieved "
    "sources, and satisfies all major required points. Use failure when the "
    "answer is incomplete, vague, unsupported, overclaims, contradicts the "
    "notes, hallucinates, invents citations, misses any major required point, "
    "or answers an out-of-scope question instead of refusing."
)


@dataclass(frozen=True)
class JudgeResult:
    score: str
    rationale: str


def load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    if not isinstance(cases, list):
        raise ValueError(f"Expected a JSON list in {path}")
    for case in cases:
        for key in ("id", "question", "grading_notes", "expected_sources"):
            if key not in case:
                raise ValueError(f"Missing required key {key!r} in case: {case}")
    return cases


def write_cases(path: Path, cases: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")


def selected_modes(mode: str) -> list[str]:
    return SUPPORTED_MODES if mode == "compare" else [mode]


def source_rank(retrieved_sources: list[str], expected_sources: list[str]) -> int | None:
    expected = set(expected_sources)
    for index, source in enumerate(retrieved_sources, start=1):
        if source in expected:
            return index
    return None


def build_judge(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        temperature=0,
        api_key=require_api_key(),
        base_url=OPENROUTER_BASE_URL,
        timeout=90, max_retries=2,
    )


def parse_judge_text(text: str) -> JudgeResult:
    cleaned = text.strip()
    match = re.match(r"(?is)^\s*(pass|failure|fail)\b[:\-\s]*(.*)$", cleaned)
    if not match:
        return JudgeResult("failure", f"Judge returned an unparsable result: {cleaned[:180]}")
    score = match.group(1).lower()
    if score == "fail":
        score = "failure"
    return JudgeResult(score, match.group(2).strip())


def llm_answer_score(
    judge: ChatOpenAI,
    case: dict[str, Any],
    response: str,
    retrieved_sources: list[str] | None = None,
) -> JudgeResult:
    retrieved_sources = retrieved_sources or []
    message = (
        f"Question:\n{case['question']}\n\n"
        f"Reference answer:\n{case.get('reference_answer', '')}\n\n"
        f"Grading notes:\n{case['grading_notes']}\n\n"
        f"Expected source files:\n{', '.join(case.get('expected_sources', [])) or 'none'}\n\n"
        f"Retrieved source files:\n{', '.join(retrieved_sources) or 'none'}\n\n"
        f"Response to grade:\n{response}\n\n"
        "Return pass or failure with one short reason."
    )
    result = judge.invoke(
        [
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=message),
        ]
    )
    text = result.content if hasattr(result, "content") else str(result)
    llm_answer_score.last_usage = result.usage_metadata or {}
    return parse_judge_text(text)


def make_row(
    *,
    timestamp: str,
    mode: str,
    case: dict[str, Any],
    results: list[Any],
    response: str,
    judge_score: JudgeResult | None,
) -> dict[str, Any]:
    retrieved_sources = [result.source for result in results]
    expected_sources = case.get("expected_sources", [])
    rank = source_rank(retrieved_sources, expected_sources)
    source_hit = "n/a" if not expected_sources else str(rank is not None).lower()
    matched_expected_sources = sorted(set(expected_sources).intersection(retrieved_sources))
    expected_source_coverage = (
        "n/a"
        if not expected_sources
        else f"{len(matched_expected_sources)}/{len(set(expected_sources))}"
    )
    all_expected_sources_hit = (
        "n/a"
        if not expected_sources
        else str(len(matched_expected_sources) == len(set(expected_sources))).lower()
    )
    return {
        "timestamp": timestamp,
        "case_id": case["id"],
        "category": case.get("category", ""),
        "mode": mode,
        "question": case["question"],
        "answer_type": case.get("answer_type", "supported"),
        "expected_sources": "; ".join(expected_sources),
        "retrieved_sources": "; ".join(retrieved_sources),
        "matched_expected_sources": "; ".join(matched_expected_sources),
        "expected_source_coverage": expected_source_coverage,
        "all_expected_sources_hit": all_expected_sources_hit,
        "top_source": retrieved_sources[0] if retrieved_sources else "",
        "expected_source_rank": rank if rank is not None else "",
        "source_hit": source_hit,
        "judge_score": judge_score.score if judge_score else "",
        "judge_rationale": judge_score.rationale if judge_score else "",
        "reference_answer": case.get("reference_answer", ""),
        "response": response,
        "grading_notes": case["grading_notes"],
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("No rows to write.")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_log(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "Capstone Checkpoint 4.1 Evaluation Results",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                "-" * 80,
                f"CASE: {row['case_id']} ({row['category']})",
                f"MODE: {row['mode']}",
                f"QUESTION: {row['question']}",
                f"EXPECTED_SOURCES: {row['expected_sources'] or 'none'}",
                f"RETRIEVED_SOURCES: {row['retrieved_sources'] or 'none'}",
                f"MATCHED_EXPECTED_SOURCES: {row['matched_expected_sources'] or 'none'}",
                f"EXPECTED_SOURCE_COVERAGE: {row['expected_source_coverage']}",
                f"ALL_EXPECTED_SOURCES_HIT: {row['all_expected_sources_hit']}",
                f"SOURCE_HIT: {row['source_hit']}",
            ]
        )
        if row["judge_score"]:
            lines.append(f"JUDGE_SCORE: {row['judge_score']} - {row['judge_rationale']}")
        if row["response"]:
            lines.extend(["", "RESPONSE:", row["response"]])
        lines.extend(["", "REFERENCE:", row["reference_answer"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize_rows(rows: list[dict[str, Any]]) -> str:
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_mode.setdefault(row["mode"], []).append(row)

    lines = []
    for mode in sorted(by_mode):
        mode_rows = by_mode[mode]
        evaluable_source_rows = [row for row in mode_rows if row["source_hit"] != "n/a"]
        source_hits = sum(1 for row in evaluable_source_rows if row["source_hit"] == "true")
        all_source_hits = sum(1 for row in evaluable_source_rows if row["all_expected_sources_hit"] == "true")
        judge_pass = sum(1 for row in mode_rows if row["judge_score"] == "pass")
        lines.append(
            f"{mode}: source_hit={source_hits}/{len(evaluable_source_rows)}, "
            f"all_sources={all_source_hits}/{len(evaluable_source_rows)}, "
            f"judge_pass={judge_pass}/{len(mode_rows) if any(row['judge_score'] for row in mode_rows) else 'not_run'}"
        )
    return "\n".join(lines)


def evaluate(args):
    """Same cases and Module 3 judge; write every completed case for resumption."""
    import hashlib
    import time
    import platform
    from research_graph import AdvancedResearchPaperRetriever, ANNOTATIONS
    retriever = AdvancedResearchPaperRetriever()
    cases = load_cases(Path(args.inputs))
    answer_llm = build_llm() if args.with_answers else None
    judge = build_judge(args.judge_model) if args.judge else None
    rows = []
    details = []
    csv_path = Path(args.output_csv)
    detail_path = csv_path.with_suffix('.json')
    manifest = {
        'inputs_sha256': hashlib.sha256(Path(args.inputs).read_bytes()).hexdigest(),
        'annotations_sha256': hashlib.sha256(ANNOTATIONS.read_bytes()).hexdigest(),
        'solution_sha256': hashlib.sha256((ASSIGNMENT_DIR/'capstone_checkpoint_4_solution.py').read_bytes()).hexdigest(),
        'graph_code_sha256': hashlib.sha256((ASSIGNMENT_DIR/'research_graph.py').read_bytes()).hexdigest(),
        'judge_model': args.judge_model, 'answer_model': LLM_MODEL, 'top_k': args.top_k,
        'with_answers': args.with_answers, 'judge': args.judge, 'python': platform.python_version(),
        'graph_nodes': retriever.graph_retriever.graph.number_of_nodes(),
        'graph_edges': retriever.graph_retriever.graph.number_of_edges(),
    }
    manifest_path = csv_path.with_suffix('.manifest.json')
    if args.resume and csv_path.exists():
        if json.loads(manifest_path.read_text()) != manifest:
            raise ValueError('Resume settings or source files changed; choose a new output.')
        with csv_path.open() as f: rows = list(csv.DictReader(f))
        details = json.loads(detail_path.read_text())
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    done = {(r['case_id'],r['mode']) for r in rows}
    for case in cases:
        for mode in selected_modes(args.mode):
            if (case['id'],mode) in done: continue
            started=time.monotonic()
            results=retriever.search(case['question'],mode,args.top_k)
            retrieval_seconds=time.monotonic()-started
            response=''
            answer_usage={}
            if answer_llm:
                reply=answer_llm.invoke([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"Retrieved context:\n{format_context(results)}\n\nQuestion: {case['question']}")])
                response=reply.content
                answer_usage=reply.usage_metadata or {}
            score=llm_answer_score(judge,case,response,[r.source for r in results]) if judge else None
            row=make_row(timestamp=datetime.now().isoformat(timespec='seconds'), mode=mode,
                         case=case,results=results,response=response,judge_score=score)
            canonical=retriever.graph_retriever.canonical
            expected={canonical.get(s,s) for s in case['expected_sources']}
            retrieved={canonical.get(r.source,r.source) for r in results}
            row.update(retrieval_seconds=round(retrieval_seconds,3),
                       total_seconds=round(time.monotonic()-started,3),
                       context_characters=sum(len(r.document.page_content) for r in results),
                       unique_sources=len({r.source for r in results}),
                       canonical_expected_source_coverage=(len(expected & retrieved)/len(expected) if expected else ''),
                       canonical_all_sources_hit=(str(expected<=retrieved).lower() if expected else 'n/a'))
            rows.append(row)
            details.append({'case_id':case['id'],'mode':mode,'trace':retriever.last_trace,
                            'results':[{'source':r.source,'page':page_label(r.document),'score':r.score,
                                        'role':r.document.metadata.get('retrieval_role','primary'),
                                        'text':r.document.page_content} for r in results],
                            'answer_usage':answer_usage,
                            'judge_usage':getattr(llm_answer_score,'last_usage',{}) if judge else {},
                            'response':response,'judge_score':score.score if score else '',
                            'judge_rationale':score.rationale if score else ''})
            write_csv(csv_path,rows)
            write_log(Path(args.output_log),rows)
            detail_path.write_text(json.dumps(details,indent=2,ensure_ascii=False)+'\n')
            print(f"{case['id']} {mode}: coverage={row['expected_source_coverage']} judge={row['judge_score']} ({row['total_seconds']}s)",flush=True)
    print(summarize_rows(rows),flush=True)
    return rows


def parse_args():
    parser=argparse.ArgumentParser(description='Checkpoint 4: matched-budget advanced retrieval comparison')
    parser.add_argument('--inputs',default=str(DEFAULT_INPUTS_PATH))
    parser.add_argument('--mode',choices=SUPPORTED_MODES+['compare'],default='compare')
    parser.add_argument('--top-k',type=int,default=3)
    parser.add_argument('--with-answers',action='store_true')
    parser.add_argument('--judge',action='store_true')
    parser.add_argument('--judge-model',default=LLM_MODEL)
    parser.add_argument('--output-csv',default=str(ASSIGNMENT_DIR/'checkpoint_4_comparison_results.csv'))
    parser.add_argument('--output-log',default=str(ASSIGNMENT_DIR/'checkpoint_4_comparison_results.log'))
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.judge and not args.with_answers: parser.error('--judge requires --with-answers')
    if args.top_k<1: parser.error('--top-k must be positive')
    return args


if __name__=='__main__': evaluate(parse_args())
