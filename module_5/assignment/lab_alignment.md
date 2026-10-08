# Structural alignment with Module 5 labs

The current implementation adapts the actual lab solution files. The earlier
Python-loop implementation and its measurements are archived under
`archive/pre_langgraph/` and do not support the current submission.

| Lab component | Capstone implementation | Adaptation |
| --- | --- | --- |
| Lab 5.1 `_AgentState` | `AgentState` | Original question, pending/executed queries, accumulated evidence, iterations, done flag; paper chunk IDs replace email filenames for deduplication. |
| Lab 5.1 `retrieve_node` | `AgenticResearchRetriever.retrieve_node` | Executes pending hybrid queries, merges original PDF passages, clears pending queries, increments round count. |
| Lab 5.1 `analyze_node` | `AgenticResearchRetriever.analyze_node` | Reads actual observations and asks whether enough evidence exists; new queries are generated only after retrieval. |
| Lab 5.1 conditional edge | `should_continue` and `StateGraph.add_conditional_edges` | Loops to retrieve or ends; no preplanned subject-search schedule. |
| Lab 5.1 answer outside graph | `AgenticResearchRetriever.query` | The graph supplies context; the same grounded answer function used by the baseline generates the response. |
| Lab 5.2 `plan_node` | `ToolUsingResearchAgent.plan_node` | Chooses one next action from prior conversation, clarifications, executed actions, observations, and PDF text. |
| Lab 5.2 `retrieve` tool | `ResearchTools.retrieve` | Existing BM25/vector hybrid retrieval with three passages per search. |
| Lab 5.2 deterministic `by_date` tool | `ResearchTools.lookup_papers` | Deterministic title/author substring and exact-year filtering of the paper catalogue; no embedding call. Catalogue metadata remains a discovery hint. |
| Research-paper-specific tools | `read_paper`, `follow_references` | Focused local passage retrieval and validated in-corpus reference discovery; filenames must first be observed. |
| Lab 5.2 tool-node wrappers | Separate LangGraph nodes wrapping `StructuredTool.invoke` | Each tool has a Pydantic input schema. The model selects; Python validates and executes. Every tool node returns to `plan`. |
| Lab 5.2 `clarify_node` | `clarify_node` with injected input callback | Chat responses re-enter planning; batch runs never call input and produce an explicit response when clarification is unavailable. |
| Lab 5.2 `answer_node` | `answer_node` | Grounded answer generation occurs inside the graph and connects to `END`. |
| Refined answer gate | `coverage_node` between attempted answer and `answer_node` | A question-derived checklist is checked against quoted PDF passages. Missing evidence returns to `plan`; a fixed-field structured schema requires one assessment per checklist item. |
| Lab 5.2 `query()` and `chat()` | `query()` and `chat()` | Fresh state per evaluated question; conversation history explicitly persists across interactive turns. |
| Lab failure/budget handling | Budget check before model calls; invalid decisions route to completion | No model retry loop on malformed JSON or contradictory tool arguments. |

The source labs are:

- [Lab 5.1 solution](../Live_Guided_Virtual_Lab_5_1_solution/lab_5_1_agentic_retriever_solution.py)
- [Lab 5.2 solution](../Live_Guided_Virtual_Lab_5_2_solution/lab_5_2_tool_using_agent_solution.py)

The [Lab 5.1 graph](evidence/lab_5_1_graph.mmd) and
[Lab 5.2 graph](evidence/lab_5_2_graph.mmd) are exported from the compiled graphs,
rather than being diagrams of an intended but unimplemented design.

## Deliberate differences from the email labs

Paper passages are smaller evidence units than whole emails. The answer is capped
at twelve distinct chunks, and the controller sees all twelve. The Lab 5.1
version allows three retrieval rounds; the Lab 5.2 version allows eight tool or
clarification steps. Action signatures are tracked so duplicate calls receive
bounded planner recovery rather than repeated tool execution. Unknown filenames
and empty filters are rejected before tool execution. Planner validation errors
receive at most two corrective decisions. The explicit iteration increment on
clarification also prevents a clarification-only loop. Structured planner output
and the bounded coverage gate were refinements motivated by recorded failures;
they preserve the lab's plan/tool/plan control flow.

The original Module 1 corpus/key are read only. Module 4 retrieval and graph code,
annotations, and the vector index were copied into Module 5. LangGraph and missing
companion packages are installed under `module_5/.python_packages`, leaving the
shared virtual environment unchanged.
