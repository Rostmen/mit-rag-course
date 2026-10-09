# Audit source review

These are design observations, not observed attack successes.

- `ToolUsingResearchAgent.query` extracts a checklist before checking scope or
  ambiguity. Every request therefore starts with an external model dependency.
- `model_context` and `answer_text` include the last six history messages. History
  is a potential persistence channel; retained text alone does not prove an attack.
- `REFINED_PROMPT` tells the planner not to obey passage instructions. The answer
  prompt requires grounded citations, but has no explicit persona restriction.
- `plan_node` permits only four read/discovery tools and requires previously
  observed filenames. No file-writing, shell, email, or arbitrary URL tool exists.
- Eight actions and twelve evidence chunks bound one query, but do not cap total
  input size, conversation storage, API latency, or total session spending.
- `coverage_node` validates coverage before normal completion; action-budget and
  invalid-plan exits proceed to answer generation with a stop reason. A budget
  limits work but cannot guarantee that an answer is complete.
- `clarify` requires a prior tool attempt. Completely ambiguous inputs can incur
  retrieval work before the system asks for necessary information.
- Model/API failures during requirement extraction or tool execution are not
  caught by the normal CLI query path. The audit harness records exception types
  so a failed case cannot be mistaken for a successful refusal.

Source: unchanged `module_5/assignment/capstone_checkpoint_5_1_agent_rag_starter.py`,
`retrieval_backend.py`, and `research_tools.py`. Fingerprints are in the run manifest.
No mitigations were implemented for this checkpoint.
