"""Capstone Checkpoint 3.1: evaluation infrastructure for ResearchPapers.

This script keeps the Module 2 retrieval baseline fixed and adds a structured
evaluation harness around it. It adapts the ideas from Labs 3.1 and 3.2:

- fixed test inputs with grading notes
- batch evaluation over keyword, vector, and hybrid retrieval
- source-hit metrics for retrieval quality
- optional grounded answer generation
- optional LLM-as-judge answer grading
- optional paraphrase-variant generation for robustness testing
- degraded-output validation cases for checking whether the metric catches bad
  answers

Run examples:
    .venv/bin/python module_3/assignment/capstone_checkpoint_3_1_evaluation_solution.py --mode compare --top-k 3
    .venv/bin/python module_3/assignment/capstone_checkpoint_3_1_evaluation_solution.py --mode compare --top-k 3 --with-answers --judge
    .venv/bin/python module_3/assignment/capstone_checkpoint_3_1_evaluation_solution.py --generate-variants 2
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

from capstone_checkpoint_2_1_retrieval_strategy_solution import (
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    ResearchPaperRetriever,
    build_llm,
    format_results,
    generate_answer,
    load_local_env,
    page_label,
    require_api_key,
)


ASSIGNMENT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUTS_PATH = ASSIGNMENT_DIR / "capstone_checkpoint_3_1_test_inputs.json"
DEFAULT_RESULTS_CSV = ASSIGNMENT_DIR / "checkpoint_3_1_baseline_results.csv"
DEFAULT_RESULTS_LOG = ASSIGNMENT_DIR / "checkpoint_3_1_evaluation_results.log"
DEFAULT_VALIDATION_CSV = ASSIGNMENT_DIR / "checkpoint_3_1_validation_results.csv"
DEFAULT_VARIANTS_PATH = ASSIGNMENT_DIR / "capstone_checkpoint_3_1_test_inputs_variants.json"

SUPPORTED_MODES = ["keyword", "vector", "hybrid"]

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
    mrr = 0.0 if rank is None else 1.0 / rank

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
        "mrr": f"{mrr:.3f}",
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
        "Capstone Checkpoint 3.1 Evaluation Results",
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
                f"SOURCE_HIT: {row['source_hit']}  MRR: {row['mrr']}",
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


def evaluate(args: argparse.Namespace) -> list[dict[str, Any]]:
    load_local_env()
    cases = load_cases(Path(args.inputs))
    modes = selected_modes(args.mode)

    retriever = ResearchPaperRetriever()
    answer_llm = build_llm() if args.with_answers else None
    judge = build_judge(args.judge_model) if args.judge else None
    timestamp = datetime.now().isoformat(timespec="seconds")

    rows: list[dict[str, Any]] = []
    for case in cases:
        for mode in modes:
            results = retriever.search(case["question"], mode, args.top_k)
            response = ""
            if answer_llm is not None:
                try:
                    response = generate_answer(answer_llm, case["question"], results)
                except Exception as error:
                    response = f"[answer_generation_error] {type(error).__name__}: {error}"

            judge_score = None
            if judge is not None:
                try:
                    judge_score = llm_answer_score(
                        judge,
                        case,
                        response,
                        [result.source for result in results],
                    )
                except Exception as error:
                    judge_score = JudgeResult(
                        "failure",
                        f"Judge error: {type(error).__name__}: {error}",
                    )

            rows.append(
                make_row(
                    timestamp=timestamp,
                    mode=mode,
                    case=case,
                    results=results,
                    response=response,
                    judge_score=judge_score,
                )
            )

            print(format_results(mode, case["question"], results))
            if response:
                print("\nANSWER:\n" + response)
            print()

    write_csv(Path(args.output_csv), rows)
    write_log(Path(args.output_log), rows)
    print("Summary:")
    print(summarize_rows(rows))
    print(f"Results CSV: {Path(args.output_csv).resolve()}")
    print(f"Results log: {Path(args.output_log).resolve()}")
    return rows


def validation_cases() -> list[dict[str, Any]]:
    return [
        {
            "validation_id": "wrong_quote",
            "case_id": "quote_sketching_abstract",
            "question": "Quote the first sentence of the abstract of The Sketching Approach to Program Synthesis.",
            "grading_notes": "A correct answer must quote or closely reproduce the first sentence of the abstract about sketching bridging high-level insights and low-level details.",
            "reference_answer": "Sketching bridges a programmer's high-level insights with the computer's ability to manage low-level details.",
            "expected_sources": ["DBLP_conf_aplas_Solar-Lezama09.pdf"],
            "answer_type": "supported",
            "response": "The abstract begins by saying that program synthesis is mostly about faster compilers. [Source 1]",
        },
        {
            "validation_id": "unsupported_oil_price",
            "case_id": "out_of_domain_oil_price",
            "question": "What is the current oil price?",
            "grading_notes": "A correct answer must say that the available research-paper documents do not provide enough information and must not invent a price.",
            "reference_answer": "The corpus does not contain current oil prices.",
            "expected_sources": [],
            "answer_type": "refusal",
            "response": "The current oil price is $84.50 per barrel. [Source 2]",
        },
        {
            "validation_id": "false_premise_answered",
            "case_id": "false_premise_nobel",
            "question": "According to the papers, what year did SketchAdapt win a Nobel Prize?",
            "grading_notes": "A correct answer should reject the false premise and must not invent a Nobel Prize year.",
            "reference_answer": "The papers do not support SketchAdapt winning a Nobel Prize.",
            "expected_sources": [],
            "answer_type": "refusal",
            "response": "SketchAdapt won the Nobel Prize in 2019 for advances in program synthesis.",
        },
        {
            "validation_id": "fake_synthesis_citation",
            "case_id": "program_synthesis_definitions",
            "question": "Compare how papers in this collection define program synthesis.",
            "grading_notes": "A correct answer should compare definitions based on user intent, constraints, and satisfying a specification, and should cite multiple sources.",
            "reference_answer": "Program synthesis is framed as discovering or constructing programs from constraints, user intent, or specifications.",
            "expected_sources": ["DBLP_conf_cav_BraggFRS21.pdf", "DBLP_journals_fmsd_JeonQSF17.pdf"],
            "answer_type": "supported",
            "response": "The collection defines program synthesis as training neural networks to summarize PDFs, which is supported by [Source 9].",
        },
    ]


def validate_metric(args: argparse.Namespace) -> list[dict[str, Any]]:
    load_local_env()
    judge = build_judge(args.judge_model) if args.judge else None
    timestamp = datetime.now().isoformat(timespec="seconds")
    rows = []

    for case in validation_cases():
        judge_score = None
        if judge is not None:
            try:
                judge_score = llm_answer_score(judge, case, case["response"], [])
            except Exception as error:
                judge_score = JudgeResult("failure", f"Judge error: {type(error).__name__}: {error}")
        rows.append(
            {
                "timestamp": timestamp,
                "validation_id": case["validation_id"],
                "case_id": case["case_id"],
                "question": case["question"],
                "response": case["response"],
                "expected_detection": "failure",
                "judge_score": judge_score.score if judge_score else "",
                "judge_rationale": judge_score.rationale if judge_score else "",
                "grading_notes": case["grading_notes"],
            }
        )

    write_csv(Path(args.validation_csv), rows)
    print(f"Validation CSV: {Path(args.validation_csv).resolve()}")
    return rows


def make_variants(llm: ChatOpenAI, question: str, n: int) -> list[str]:
    messages = [
        SystemMessage(content=VARIANT_SYSTEM_PROMPT),
        HumanMessage(content=f"Question: {question}\n\nProduce {n} paraphrases."),
    ]
    response = llm.invoke(messages)
    text = response.content if hasattr(response, "content") else str(response)
    variants = [line.strip("-* ").strip() for line in text.splitlines() if line.strip()]
    return variants[:n]


def generate_variants(args: argparse.Namespace) -> None:
    load_local_env()
    cases = load_cases(Path(args.inputs))
    llm = build_judge(args.judge_model)
    augmented: list[dict[str, Any]] = []
    for case in cases:
        augmented.append(case)
        print(f"[{case['id']}] {case['question']}")
        for index, variant in enumerate(make_variants(llm, case["question"], args.generate_variants), start=1):
            variant_case = dict(case)
            variant_case["id"] = f"{case['id']}_variant_{index}"
            variant_case["question"] = variant
            variant_case["variant_of"] = case["id"]
            augmented.append(variant_case)
            print(f"  -> {variant}")
    write_cases(Path(args.variants_output), augmented)
    print(f"Wrote variants to: {Path(args.variants_output).resolve()}")
    print("Review this file manually before using it for scoring; delete variants that drift in meaning.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", default=str(DEFAULT_INPUTS_PATH))
    parser.add_argument("--mode", choices=["keyword", "vector", "hybrid", "compare"], default="compare")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--with-answers", action="store_true")
    parser.add_argument("--judge", action="store_true", help="Use an LLM judge for strict pass/failure scoring.")
    parser.add_argument("--judge-model", default=LLM_MODEL)
    parser.add_argument("--output-csv", default=str(DEFAULT_RESULTS_CSV))
    parser.add_argument("--output-log", default=str(DEFAULT_RESULTS_LOG))
    parser.add_argument("--validation-csv", default=str(DEFAULT_VALIDATION_CSV))
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Do not write degraded-output validation cases.",
    )
    parser.add_argument(
        "--validation-only",
        action="store_true",
        help="Only write degraded-output validation cases; skip retrieval evaluation.",
    )
    parser.add_argument(
        "--generate-variants",
        type=int,
        default=0,
        help="Generate this many paraphrase variants per input case, then exit.",
    )
    parser.add_argument("--variants-output", default=str(DEFAULT_VARIANTS_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.generate_variants:
        generate_variants(args)
        return

    if args.validation_only:
        validate_metric(args)
        return

    evaluate(args)
    if not args.skip_validation:
        validate_metric(args)


if __name__ == "__main__":
    main()
