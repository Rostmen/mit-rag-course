# Required Capstone Checkpoint 5.1: Designing and Evaluating an Agent-Based RAG System

## Directions

Download this worksheet and save a copy to your device before you begin working. Use this worksheet to plan, organize, and complete your submission for Required Capstone Checkpoint 5.1. Type your responses directly into the document, save your completed work, and upload the finished file when you are ready to submit.

## Completion Checklist

- [x] Description of the agent-based system and task
- [x] Explanation of how the system coordinates retrieval, reasoning, and multistep execution
- [x] Evaluation results from 2-3 representative multistep test cases
- [x] Description of refinements made to the system
- [x] Analysis of the impact of those refinements
- [x] Reflection on system strengths, limitations, and future improvements

## Step 1. System Design

Describe the task that your agent-based system is designed to complete.

Examples may include generating reports, answering complex questions, synthesizing information across multiple documents, or completing another multistep task relevant to your capstone scenario.

### Task description

Response:

The Research Paper Navigator answers multistep research questions across the 153-paper capstone corpus. It retrieves evidence from multiple papers, compares or synthesizes the findings, and produces a cited answer.

### Agent workflow: Describe how your system works

Consider:

- How retrieval is incorporated into the workflow
- How the system performs reasoning or intermediate processing
- Any iterative or multistep behaviors
- Any prompts, tools, or workflow components used to guide agent behavior

The initial LangGraph follows Lab 5.1: `retrieve → analyze → retrieve/END`. After each search, the analyzer decides whether the evidence is sufficient or creates a focused follow-up query.

The refined graph follows Lab 5.2: `plan → tool → plan`. It can run hybrid retrieval, look up papers by metadata, search within a known paper, follow in-corpus references, or request clarification. Before answering, an evidence-check node verifies that every part of the question has supporting PDF text; missing evidence returns to planning. The workflow is limited to eight tool actions and twelve evidence chunks. Answers use only original PDF passages and include source citations.

## Step 2. Initial Evaluation

Develop and evaluate your system using 2-3 representative test cases for your capstone scenario. Each test case should require more than one retrieval step or action.

For each test case, compare the agent-based system with your fixed retrieval pipeline from Checkpoint 2.1 or 3.1. Record relevant differences in answer quality, completeness, retrieval behavior, model calls, latency, or cost.

### Evaluation results

Summarize the results of your testing:

The fixed baseline is the Checkpoint 2.1 hybrid retrieval pipeline retained in Checkpoint 3.1. It performs one search with the original question, returns the top three chunks, and makes one answer-generation call. Checkpoint 3.1 kept this retrieval pipeline fixed and added the evaluation harness.

I selected three difficult questions from the existing capstone evaluation set. LiveCodeBench appeared in Checkpoint 3.1, and all three questions were used in Module 4. These paper topics come from the capstone dataset; they were not prescribed by this worksheet.

1. Compare LiveCodeBench and Bench-Push: evaluation targets, realism/reproducibility, and metrics or categories.
2. Synthesize self-repair: repair workflow, LiveCodeBench capabilities, and counterfeit-sample cautions.
3. Compare CVC4SY and adaptive concretization: search spaces, mechanisms, and tradeoffs.

I compared the Checkpoint 2.1/3.1 fixed pipeline with the initial Lab 5.1 agent using the saved answers and retrieved passages.

| Test case | Checkpoint 2.1/3.1 baseline | Initial Lab 5.1 agent | Remaining initial gaps |
| --- | ---: | ---: | --- |
| Benchmark comparison | 1/4 criteria | 2/4 | Live/contamination design and baseline demonstrations omitted |
| Self-repair synthesis | 2/3 | 3/3 | No rubric gap |
| Synthesis strategies | 2/4 | 2/4 | CVC4SY-specific evidence missing |

The initial agent covered 7/11 criteria and completed 1/3 tasks, compared with 5/11 and 0/3 for the fixed baseline. Its follow-up retrieval improved the self-repair answer, but it stopped too early on the synthesis question and never found CVC4SY-specific evidence.

### Strengths observed

Response:

The initial agent used retrieved results to generate follow-up searches and completed the self-repair task. Its traces also made each retrieval and stopping decision inspectable.

### Weaknesses or challenges identified

Response:

Broad searches sometimes returned evidence for only one subject. The agent could then stop prematurely or omit useful facts already present in its context. Automated grading also occasionally credited facts that were not stated in the answer, so I kept a separate passage review.

## Step 3. System Refinement

Based on your evaluation results, make one or more improvements to your system. Examples may include:

- Improving system prompts
- Adjusting workflow structure
- Modifying retrieval behavior
- Improving how the agent uses retrieved information

### Changes implemented

Response:

I replaced the initial retrieval loop with the Lab 5.2 tool-selection graph. I added metadata lookup, focused within-paper search, reference discovery, schema-constrained planner output, and bounded recovery from invalid tool arguments.

I also added a question-derived evidence checklist. Before answering, the system checks every requested subject and dimension against quoted PDF passages. If evidence is missing, it returns the gap to the planner for another tool action. Twenty-three offline tests verify graph routing, tool validation, evidence recovery, clarification, and state isolation.

### Justification

Response:

These changes directly address the initial failures. Focused tools help locate named papers, and the evidence check prevents the agent from answering while part of the question is unsupported. The checklist is derived from the user question, so it does not inject reference answers or hardcoded paper facts.

## Step 4. Impact of Refinement

Evaluate the updated system. Describe any changes in task completion, accuracy, relevance, or overall system behavior. Compare the refined agent-based system with both its initial version and the fixed baseline. Explain whether the refinement improved performance and identify any trade-offs.

### Impact on system performance

Response:

For the benchmark comparison, the fixed baseline covered 1 of 4 criteria, the initial agent covered 2 of 4, and the refined agent covered all 4. For self-repair synthesis, the systems covered 2 of 3, 3 of 3, and 3 of 3 criteria, respectively. For synthesis strategies, they covered 2 of 4, 2 of 4, and 4 of 4. Overall, the fixed baseline completed 0 of 3 tasks, the initial agent completed 1 of 3, and the refined agent completed all 3.

The refined agent covered all 11 criteria. Its evidence check triggered additional retrieval for the missing counterfeit-samples and CVC4SY evidence. The raw judge passed 2 of 3 tasks but marked all criteria supported; passage review corrected the contradictory benchmark rejection.

### Comparison of initial and refined systems

Response:

Across the three cases, the fixed baseline covered 5 of 11 criteria and completed no tasks. It used 3 model calls, 4,153 chat tokens, 3 retrieval calls, and had a median latency of 3.65 seconds per task.

The initial agent covered 7 of 11 criteria and completed 1 task. It used 8 model calls, 17,410 chat tokens, 8 tool calls, and had a median latency of 8.84 seconds.

The refined agent covered all 11 criteria and completed all 3 tasks. It used 29 model calls, 72,225 chat tokens, 12 tool calls, and had a median latency of 15.55 seconds. The refinement improved completeness at a substantial cost in latency and model usage. Development runs are reported separately and are not included in this comparison.

## Step 5. Reflection

Reflect on your experience designing and evaluating an agent-based RAG system.

### What contributed most to successful task completion?

Response:

The evidence-completeness check contributed most. It prevented premature answers and gave the planner a specific missing-evidence target, which led to successful follow-up retrieval in the self-repair and synthesis cases.

### What limitations remain?

Response:

The evaluation uses only three development questions and one final run per condition. Passage review was not independently validated, and quotation matching proves provenance rather than semantic correctness. Metadata lookup can also miss papers embedded in proceedings, and the context limit may discard useful later evidence.

### What improvements would you prioritize next?

Response:

I would reduce cost by rechecking only requirements affected by new evidence and improving passage replacement within the context limit. I would then evaluate repeated runs on held-out, ambiguous, and unsupported questions with independent reviewers.

## Supporting Materials

Use this section to list, describe, or link to any supporting materials included with your submission.

| Supporting material | Location, link, or note |
| --- | --- |
| System prompts: | [Completed starter](capstone_checkpoint_5_1_agent_rag_starter.py) and [evidence guard](evidence_guard.py). |
| Evaluation results: | [Evaluation report](evidence/evaluation_report.md), [summary](evidence/summary.json), and [passage review](evidence/passage_review.json). |
| Screenshots or diagrams: | [Lab 5.1 graph](evidence/lab_5_1_graph.mmd), [Lab 5.2 graph](evidence/lab_5_2_graph.mmd), and [lab mapping](lab_alignment.md). |
| Code, notebook, or repository link: | [Completed starter](capstone_checkpoint_5_1_agent_rag_starter.py), [evaluator](evaluate_checkpoint_5.py), and [README](../README.md). |
| Other supporting evidence: | [Offline tests](test_agent_rag.py) and [final audit](evidence/final_audit.json). |

## End of Required Capstone Checkpoint 5.1

Return to the assignment page in the learning platform to upload and submit your completed capstone checkpoint worksheet and complete any remaining items in this module.
