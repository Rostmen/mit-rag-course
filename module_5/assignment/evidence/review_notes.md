# Evaluation and refinement notes

## Scope and provenance

The worksheet asks for 2–3 representative multistep cases; it does not name
LiveCodeBench, Bench-Push, CVC4SY, or adaptive concretization. These are selected
Module 4 cases, copied unchanged into `../capstone_checkpoint_5_test_inputs.json`.
The final audit checks equality with their original Module 4 records. The fixed
baseline inherits the earlier fixed hybrid pipeline through Module 4, without
Module 4's optional advanced retrieval workflow.

The twelve primary JSON files represent three questions across four conditions.
Each records its source snapshot hashes, prompts, passages, answer, actions, model
usage, and raw automated grading. The final refined source matches the current
implementation; initial and baseline source versions remain in `source_snapshots/`.
Tests use fake models only for graph/validation behavior; evaluation uses real API
calls and the existing research-paper index.

## What was refined

The initial LangGraph implementation adapts Lab 5.1's retrieve/analyze loop.
Its benchmark and self-repair traces contain queries selected after seeing
retrieved passages. Its synthesis analysis prematurely claimed CVC4SY coverage.

The refined implementation adapts Lab 5.2's plan/tool/plan workflow, including
catalogue filtering (the analogue of the lab's date filter), focused reading,
reference discovery, and interactive clarification. It retains explicit state,
conditional edges, bounded actions, and observation-driven decisions.

Recorded development stages remain separate from the primary comparison:

1. `tool_schema_pilot/`: requiring a diagnostic explanation rejected otherwise
   usable actions when the model omitted that field. It became optional, as in
   the labs.
2. `early_stop_pilot/`: unused null clarification fields rejected answer actions,
   and broad queries/premature stopping missed named works. Unused null handling
   and focused-tool instructions were introduced.
3. `focused_prompt_pilot/`: actual metadata-to-reading and further-retrieval paths
   occurred, but missing subjects and an oversized irrelevant field still caused
   failure. Final validation keeps only fields applicable to the selected action;
   unknown fields and invalid active arguments still fail. The planner now sees
   its remaining budget and guidance to use semantic retrieval for unknown titles.
4. Later `_pilot` directories record the transition to schema-constrained planner
   output, question-derived requirements, quotation-based evidence checks, bounded
   planner recovery, and finally a fixed-field coverage schema. The fixed fields
   prevent a variable-length model response from silently omitting a requirement.

There is no mandatory per-subject search schedule, reference-answer injection, or
hardcoded paper filename in the agent. Tool choices remain model decisions.
The superseded pre-LangGraph code, worksheet, and results are archived under
`../archive/pre_langgraph/` and excluded from all current summaries.

## Final outcomes, including failed refinements

The final refined agent covers all eleven reviewed criteria and completes all
three tasks. The benchmark run uses catalogue lookup and focused reads for both
works. The self-repair evidence gate detects the missing counterfeit-samples work,
after which the planner retrieves it and answers with correctly attributed caution.
The synthesis gate detects missing CVC4SY evidence after an adaptive-concretization
result; the planner then retrieves the bounded term-enumeration paper and completes
the comparison. All three stop with `coverage_complete`.

This improves reviewed coverage from 7/11 for the initial graph and 9/11 for the
wider fixed control to 11/11. It also increases cost: 29 model calls, 72,225 tokens,
and 15.55 seconds median task latency, compared with 8 calls, 17,410 tokens, and
8.84 seconds for the initial graph. The gain is completeness, not efficiency.
Twenty-one development runs in `_pilot` directories document failures and repairs;
their 143 calls and 345,308 tokens are reported separately.

One final automated judge response returned dictionaries where strings were
required. Evaluation had already saved the answer; `--resume` regraded that same
answer without regenerating it. The failed attempt is visible in the local console
log, but its tokens were not captured. Reported judge tokens cover saved successful
judgments only. Console logs are local diagnostics; per-case JSON contains the
submission evidence. Development usage is reported separately in `summary.json`.

## Passage review versus automated grades

`passage_review.json` records assistant-conducted review, not independent human
assessment. Each criterion must be complete in the answer and supported by the
actual retrieved text. A complete task additionally requires no material
unsupported claims. Honest acknowledgement of missing context is incomplete for
these supported questions, but is not a hallucination. Partial coverage is not
full credit. The inherited self-repair grading note accepts counterfeit low-repair
findings and caution about self-feedback/reranking; exact external-feedback wording
is not mandatory.

Specific automated-grading errors corrected in the separate review:

- Fixed benchmark: contamination reduction is absent from the answer; only the
  LiveCodeBench task-category criterion is complete (1/4).
- Wider fixed benchmark: baseline demonstrations are in the context but omitted
  from the answer (3/4).
- Wider fixed synthesis: the source includes datatype/brute-force strategies but
  the answer omits them (3/4).
- Initial benchmark: live/contamination design and baseline demonstrations are
  missing from the answer (2/4), despite a raw full-coverage grade.
- Final refined benchmark: the raw judge marks all four criteria complete and
  supported, then places three statements in `unsupported_claims`. Two are directly
  supported by Sources 4 and 7; the third honestly states that exact metric formulas
  are absent from the retrieved passages. The reviewed result is therefore 4/4 and
  passing, while the contradictory raw rejection remains unchanged.
- Fixed self-repair: a sentence calls easier-problem counterfeits slightly easier
  to assess, while the source says they are not easier to assess. This is flagged
  separately; the main workflow/caution criteria remain covered.

Review judgments and raw grades are retained side by side. Citation-label validity
and source-page text matching verify provenance, not semantic entailment. These
three development cases, prompt revisions on the same questions, and single runs
cannot establish broad performance claims. Cheaper incremental coverage checks,
held-out evaluation, repeated runs, and independent review remain the next
priorities.
