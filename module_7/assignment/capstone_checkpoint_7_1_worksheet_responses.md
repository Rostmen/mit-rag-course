# Required Capstone Checkpoint 7.1: Production Readiness – Security and Performance Optimization

## Directions

Download this worksheet and save a copy to your device before you begin working. Use this worksheet to document the security safeguards and performance optimizations you implement for your capstone system. Type your responses directly into the document, save your completed work, and upload the finished file when you are ready to submit.

## Completion Checklist

☑ Implemented one or more safeguards that improve system security and/or reliability  
☑ Implemented one or more strategies that improve system performance or efficiency  
☑ Provided evidence demonstrating the impact of the implemented changes  
☑ Evaluated trade-offs among security, performance, cost, latency, and output quality  
☑ Reflected on remaining limitations and future improvements

## Step 1. System Overview

- Briefly describe your current capstone system.
- Summarize the task your system is designed to complete.

| Current system overview |
| --- |
| Response: The Research Paper Navigator answers questions about a corpus of 153 research PDFs. It combines vector search, BM25 keyword search, and a graph of paper metadata and references. A LangGraph agent selects research tools, gathers passages, and checks whether the evidence supports the requested answer. Security checks screen user input, while caching and query routing reduce repeated processing. |

| Intended task or use case |
| --- |
| Response: The system helps users find papers, understand methods, compare approaches, and investigate limitations using cited PDF passages. It supports individual questions and conversational follow-ups. It should reject unrelated requests, distinguish user instructions from source evidence, and acknowledge when the corpus does not support an answer. |

© MIT xPRO® 2026. All rights reserved.  
Page 1 of 5

<div style="page-break-after: always;"></div>

## Step 2. Security and Reliability Improvements

- Identify the safeguard(s) you implemented.
- Explain what risk or failure each safeguard addresses.
- Briefly justify your design decisions.

| Implemented safeguard(s) |
| --- |
| Response: An initial small-model check screens each request for relevance and instruction attacks before cache lookup, retrieval, or planning. It stops the request if the check fails or returns an invalid decision. Allowed input then passes through angle-bracket escaping, forged-paper-block removal, and a persona filter using openai/gpt-5.4-nano. Tagged prompt sections distinguish user text, retrieved passages, and operational context. Tool argument validation, observed-filename checks, execution budgets, and evidence checks constrain agent actions. In chat, only accepted, sanitized questions and their answers enter recent conversation history; rejected turns remain in the review log. |

| Risk(s) addressed |
| --- |
| Response: These safeguards address irrelevant retrieval, persona overrides, forged-source injection, attempts to insert prompt tags, and instructions embedded in user text or retrieved passages. Screening each conversational turn reduces the opportunity for a role-play attack to affect later answers. Cache validation checks whether a stored answer addresses the question, while bypassing the shared answer cache for conversational follow-ups avoids reusing answers whose meaning depends on another conversation. |

| Design rationale |
| --- |
| Response: Early rejection avoids spending retrieval and answer-generation resources on requests the system should not answer. A small model performs the initial check and persona filtering to limit their cost. Deterministic text filtering and explicit source boundaries complement model-based checks. The initial check stops processing on failure, favoring security over availability; the later persona filter retains a fail-open policy, which leaves residual risk. Conversation history is used to interpret follow-ups rather than treated as source evidence or authority to change system instructions. |

## Step 3. Performance and Efficiency Improvements

- Describe the optimization strategy or strategies you implemented.
- Explain why you selected these optimizations.

| Optimization(s) implemented |
| --- |
| Response: A persistent Chroma semantic answer cache uses cosine similarity threshold 0.85, capacity 400, and oldest-entry eviction. Each candidate hit is validated by openai/gpt-5-nano and retains its source passages. For independent questions, a small-model router chooses one hybrid retrieval with a gpt-5.4-mini answer or the full research agent. A satisfaction check can escalate an inadequate direct answer to gpt-5.4. Conversational follow-ups use the full agent without shared answer-cache reads or writes. |

© MIT xPRO® 2026. All rights reserved.  
Page 2 of 5

<div style="page-break-after: always;"></div>

| Rationale |
| --- |
| Response: Semantic caching targets repeated and paraphrased questions, while routing reduces work for straightforward factual requests. Validation adds overhead but helps detect unsuitable cached answers. The full agent remains available for comparisons, reference exploration, and exact metadata filters. The evaluation compares an empty semantic cache with a populated cache to measure the difference between first-time and repeated questions. |

## Step 4. Evidence of Improvement

- Compare system behavior before and after your changes.
- Include representative examples, measurements, screenshots, logs, or outputs.

| Before vs. after comparison                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Response: In the four-question cache comparison, baseline totals were 46.382 query seconds, 59,005 chat tokens, and \$0.058006 estimated chat cost. Cold optimized totals were 96.409 seconds, 90,307 tokens, and \$0.148410, so optimization initially increased cost and latency. Warm totals were 26.382 seconds, 6,124 tokens, and $0.001573 with 4/4 cache hits: 97.3% lower estimated chat cost and 43.1% lower summed latency than baseline. A paraphrase also hit at similarity 0.950. Input-screening checks rejected the oil-price request and an instruction attack in both normal and baseline modes, with no retrieval or embedding calls. These checks were performed separately; the cache comparison predates the initial input check and should not be read as its current end-to-end timing. |

| Supporting evidence |
| --- |
| Response: The linked cache report and results contain exact questions, full answers, supporting passages, routes, stop reasons, model token usage, latency, and estimated cost. The paired security evaluation records a staged persona attack before and after input filtering. Additional input-check logs record rejection decisions and simulated failure handling. The chat transcript shows a role-play attack rejected between a valid CEGIS question and a contextual follow-up; the follow-up retained the research subject without adopting the requested persona. |

## Step 5. Trade-off Analysis

- Evaluate the impact of your design decisions.
- Consider security, performance, cost, latency, output quality, usability, or other relevant trade-offs.

| Trade-off analysis |
| --- |
| Response: Caching reduced repeated-query cost and latency, but routing, validation, and stronger-model fallback increased work on some first-time questions. Cached answers can preserve incomplete outputs, so reuse is not evidence of correctness. Input screening adds a paid model call even to cache hits and can reject legitimate requests by mistake; stopping on screening failure also reduces availability. Excluding rejected turns from history limits poisoning but prevents them from supplying later conversational context. Follow-ups bypass the shared cache to avoid context mismatches, sacrificing potential savings. Reported chat costs use recorded rates, charge input at full price, exclude embeddings, and are estimates rather than invoices. |

© MIT xPRO® 2026. All rights reserved.  
Page 3 of 5

<div style="page-break-after: always;"></div>

## Step 6. Reflection and Next Steps

- Reflect on the effectiveness of your improvements.
- Identify remaining limitations and describe what you would improve next.

| Effectiveness of improvements |
| --- |
| Response: The results show that semantic caching reduced cost and latency for repeated questions: all four warm questions and the paraphrase reused answers. The cold-cache run was slower and more expensive than the baseline, so these savings depend on reuse. The initial input check and chat check rejected the tested attacks without retrieval. Earlier persona-filter-only tests showed partial mitigation: the attack influenced 3/3 baseline staged turns and 1/3 filtered turns. The cache validator also incorrectly accepted a question with a missing subject. The stronger-model limitations answer remained incomplete, and the conversational follow-up still ended with invalid_plan despite retaining the intended subject. These outcomes demonstrate specific improvements, not comprehensive security or uniformly better answer quality. |

| Remaining limitations |
| --- |
| Response: The small test set and one run per question and phase do not establish general performance or security rates. The semantic answer cache has no expiry or automatic source-change invalidation and can retain imperfect answers. Model-based screening and validation can miss attacks or misclassify benign questions; the later persona filter can fail open. The agent still has coverage and clarification conflicts that can produce invalid_plan, and proceedings PDFs complicate evidence attribution. Recent chat context is limited to three accepted exchanges. No concurrent-load benchmark or complete embedding-cost measurement was performed. |

| Future improvements |
| --- |
| Response: Repeat the workload across more research topics and report variability in quality, latency, and total cost. Re-run the full cache comparison with input screening enabled to measure its added overhead. Add semantic-cache freshness checks and evaluate whether incomplete answers should be stored. Resolve the invalid_plan control-flow conflicts and improve passage selection within proceedings. Expand security evaluation to longer staged conversations, paraphrased attacks, malicious PDF passages, and benign questions that resemble attacks. Measure false rejections as well as missed attacks. |

## Supporting Materials

Use this section to list or link to any supporting materials included with your submission.

| Supporting material | Location, link, or note |
| --- | --- |
| Test cases | Cache-comparison questions in [results](evidence/lab_7_2/results.json); [input-screening cases](../../capstone_project/results/input_guardrails.json) and [chat sequence](../../capstone_project/results/chat-security.json) |
| Performance measurements | [Cache comparison report](evidence/lab_7_2/report.md) and [per-model measurements](evidence/lab_7_2/results.json) |

© MIT xPRO® 2026. All rights reserved.  
Page 4 of 5

<div style="page-break-after: always;"></div>

| Supporting material | Location, link, or note |
| --- | --- |
| Example queries and outputs | Full answers and source passages in [results.json](evidence/lab_7_2/results.json) |
| Screenshots or logs | [Cache experiment log](evidence/lab_7_2/results.json); [paired security transcript](evidence/security_7_1_live/transcript.md); [interactive security log](../../capstone_project/results/chat-security.json) |
| Code/notebook/repository | [Research Paper Navigator](../../capstone_project/research_paper_rag.py) and [setup instructions](../../capstone_project/README.md) |
| Other supporting evidence | [Paired security comparison and limitations](evidence/security_7_1_live/report.md); [answer-quality review](evidence/lab_7_2/report.md) |

**End of Required Capstone Checkpoint 7.1**

Return to the assignment page in the learning platform to upload and submit your completed capstone checkpoint and complete any remaining items in this module.

© MIT xPRO® 2026. All rights reserved.  
Page 5 of 5
