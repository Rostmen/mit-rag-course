# Required Capstone Checkpoint 4.1: Advanced Retrieval Implementation

## Directions

Download this worksheet and save a copy to your device before you begin working. Use this worksheet to plan, organize, and complete your submission for Required Capstone Checkpoint 4.1. Type your responses directly into the document, save your completed work, and upload the finished file when you are ready to submit.

## Completion Checklist

- [x] Identification of a meaningful retrieval failure or limitation supported by evaluation evidence
- [x] Analysis of the likely cause of the retrieval failure
- [x] Selection and justification of an advanced retrieval strategy
- [x] Evidence of implementation of the updated retrieval architecture
- [x] Evaluation results comparing the updated system against the baseline system
- [x] Reflection on the effectiveness of the architectural changes and any remaining limitations

## Step 1. Retrieval Failure Identification

Identify a meaningful retrieval limitation in your current retrieval system.

• Describe the failure or limitation.
• Explain how the limitation affects retrieval performance.
• Reference evaluation evidence, test results, queries, or outputs that demonstrate the issue.

### Retrieval failure or limitation

Response:

The baseline often retrieves only part of the evidence needed for multi-paper synthesis. Several top-ranked chunks can come from the same document, leaving another requested subject unsupported.

### Evidence supporting the identified limitation

Response:

Module 3 hybrid retrieval found at least one expected source for 12/14 supported questions but every expected source for only 5/14. Strict answer evaluation passed 9/20 cases. The self-repair synthesis case covered two of three expected files and omitted required LiveCodeBench capabilities. The LiveCodeBench/Bench-Push comparison returned three chunks from DBLP_journals_corr_abs-2403-07974.pdf and failed the answer judge.

## Step 2. Failure Analysis

Analyze why the retrieval failure occurs. Consider questions such as:

• Does the query require multiple retrieval steps?
• Is relevant information distributed across multiple documents, conversations, or entities?
• Is excessive irrelevant information being retrieved?
• Are important relationships within the data not represented effectively?
• Are there other factors contributing to the failure?

### Likely cause(s) of the retrieval failure

Response:

A single combined query lets one subject dominate similarity and keyword rankings. The baseline has no per-subject coverage mechanism, source-diversity selection, or document-relationship traversal. Alternate versions and proceedings volumes complicate both retrieval and expected-filename grading.

### Why the current retrieval architecture struggles

Response:

The baseline ranks independent 1,200-character chunks using normalized BM25 and vector scores, then takes the first three. It neither separates information needs nor follows explicit paper relationships, so strong local matches can crowd out complementary evidence.

## Step 3. Retrieval Strategy Selection

Select an advanced retrieval strategy designed to address the identified limitation. Examples may include:

• Query rewriting
• Query decomposition
• Retrieval fusion
• Multi-hop retrieval
• Relationship-aware retrieval
• Graph-based retrieval
• Another advanced retrieval approach

### Selected retrieval strategy

Response:

I implemented query decomposition, rank fusion, and relationship-aware graph retrieval. The four evaluated modes are the unchanged hybrid search, decomposition with source diversity, graph expansion with source diversity, and decomposition plus graph expansion.

### Justification for the selected strategy

Response:

Decomposition gives each requested subject its own retrieval opportunity. Graph expansion can discover related documents through explicit references, shared topics/authors, or alternate versions. A bounded final context and distinct-work selection reduce duplicate crowding. Comparing the two techniques separately and together tests whether graph expansion contributes beyond decomposition; improvement is not assumed.

## Step 4. Updated Retrieval Architecture

Describe the modifications made to your retrieval system.

• Summarize the architectural changes.
• Explain how the updated approach differs from the baseline system.
• Include implementation evidence where appropriate.

### Description of architectural changes

Response:

I copied the Module 3 solution to capstone_checkpoint_4_solution.py and retained its ResearchPaperRetriever, 1,200-character chunks, 200-character overlap, BM25/vector weighting, embedding model, vector index, and answer system prompt. A new wrapper adapts the Lab 4.1 planner and Lab 4.2 seed-and-expand graph. The planner produces at most four focused queries with original-query fallback. The graph starts from five seed chunks, proposes at most eight neighboring documents per query, and selects at most two candidate passages per neighbor. Rank fusion and aspect/source selection produce the same three final chunks used by the baseline. Answer context contains original PDF passages, labeled primary or graph context; generated annotations are not answer evidence.

The annotation script called the configured OpenAI model through the existing OpenRouter account for all 153 PDFs. The NetworkX graph contains 1,221 nodes and 1,960 edges, including 54 resolved reference edges, 56 directed alternate-version edges, 1,223 topic edges, and 627 author edges. Of 153 documents, 134 were annotated as papers, 15 as collections, and four as other documents. Thirty-nine long PDFs were sampled within a 100,000-character limit, with exact page coverage recorded. Publication dates are metadata, not inferred influence edges.

### Implementation evidence (e.g., screenshots, code snippets, retrieval outputs, notebook excerpts)

Response:

The implementation is in capstone_checkpoint_4_solution.py, research_graph.py, and annotate_research_papers.py. The integration preserves the existing search engine:

```python
class AdvancedResearchPaperRetriever(ResearchPaperRetriever):
    # Existing keyword/vector/hybrid methods supply seed chunks.
    ...

results = self.hybrid_search(sq, 12)
results, origins, paths = self.graph_retriever.expand(sq, results)
```

annotatedResearchPapers.json records the model, prompt, document hashes, selected pages, validated reference quotations, and successful-call usage. checkpoint_4_comparison_results.json records every selected passage, subquery, graph path, answer, and judge rationale. Its manifest records input and implementation hashes. Seven offline regression tests passed for grounded/unambiguous links, version grouping, query fallback, aspect diversity, direct-source provenance priority, and the final retrieval budget.

## Step 5. Evaluation Results

Evaluate the updated system using the evaluation framework developed in previous modules.

• Present evaluation results.
• Compare performance against the baseline system.
• Include representative examples.

| Evaluation Metric | Baseline Result | Updated Result |
| --- | --- | --- |
| At least one expected filename / 14 supported | 12/14 | Decomposition: 14/14; Graph: 14/14; Combined: 14/14 |
| All expected filenames / 14 supported | 5/14 | Decomposition: 8/14; Graph: 7/14; Combined: 6/14 |
| Mean expected-source coverage | 61.9% | Decomposition: 76.2%; Graph: 71.4%; Combined: 69.0% |
| All expected works, version-aware / 14 | 5/14 | Decomposition: 12/14; Graph: 10/14; Combined: 11/14 |
| Strict answer passes / 20 | 8/20 | Decomposition: 12/20; Graph: 10/20; Combined: 13/20 |
| Refusal passes / 6 | 4/6 | Decomposition: 5/6; Graph: 3/6; Combined: 4/6 |
| Median retrieval latency (seconds) | 0.36 | Decomposition: 2.04; Graph: 0.38; Combined: 1.05 |
| Mean final context characters | 3321 | Decomposition: 3255; Graph: 3460; Combined: 3315 |

All four modes used the unchanged 20-case Module 3 test set (14 supported and six refusal cases), the same answer model/system prompt, and three final PDF chunks. The original filename-based metric is retained; the supplementary work-level metric collapses exact-title/shared-author paper versions equally for every mode. The archived Module 3 result was 9/20 answer passes; the fresh baseline here passed 8/20. Answer/judge variability means the paired current run is the appropriate comparison, not a guaranteed reproduction of the historical answer score. Baseline retrieval coverage remained 5/14 complete-source hits.

Latency excludes initialization. Combined mode reuses cached decomposition plans from decomposition mode; token and latency comparisons therefore do not represent equal cold-cache conditions. The same final chunk count also does not imply identical passages or token counts. This is an exploratory development-set comparison, not held-out validation.

### Example 1: Query, retrieved information, and result

Response:

**Query:** Synthesize what the corpus says about self-repair in code generation: describe the repair workflow, explain how LiveCodeBench evaluates related capabilities, and explain why counterfeit-samples work recommends caution with self-repair or model-based reranking.

**Retrieved information:** Baseline retrieved two counterfeit-samples versions and the self-repair workflow paper. Graph mode selected the counterfeit-samples paper (page 2), self-repair paper (page 1), and LiveCodeBench (page 4), bringing the benchmark's four evaluation scenarios into the context.

**Result:** Expected-filename coverage increased from 2/3 to 3/3. The fresh baseline answer was graded pass; graph mode was graded pass. The historical Module 3 answer failed this case. Manual inspection found that the fresh baseline answer wrongly attributes counterfeit-sample findings to LiveCodeBench, even though none of its passages mentions LiveCodeBench. Its automated pass is therefore a detected false positive; I retain the original judge count rather than silently changing the metric. All three final graph-mode passages were already hybrid candidates, so this example supports the value of reranking and version diversity, not a claim that a citation edge alone caused the gain.

### Example 2: Query, retrieved information, and result

Response:

**Query:** Across the database and data-management papers, compare how program synthesis or program analysis is used in StatusQuo, social recommendations, and entity matching. What is the task in each case, and what practical benefit is claimed?

**Retrieved information:** The combined planner produced one query each for StatusQuo, social recommendations, and entity matching. Final passages came from page 1 of DBLP_conf_cidr_CheungAMSM13.pdf, DBLP_conf_cikm_CheungSM12.pdf, and DBLP_journals_pvldb_SinghMEMPQST17.pdf. The answer compared database/application placement, learning user-preference programs, and synthesizing matching rules.

**Result:** Filename coverage improved from 2/3 to 3/3, and the strict judge changed from failure to pass. These were direct retrieval candidates after decomposition; graph-mode reranking influenced selection, but this example does not isolate the effect of graph-only neighbors.

### Example 3 (optional)

Response:

**Query:** Compare the evaluation design of LiveCodeBench and Bench-Push. For each benchmark, state what is being evaluated, what makes the test setting realistic or reproducible, and what metrics or task categories are used.

**Retrieved information:** Baseline returned three chunks from the same LiveCodeBench preprint. Advanced retrieval broadened the evidence, but three selected passages were still insufficient for the required benchmark details.

**Result:** Baseline strict filename coverage was 0/2; combined coverage was 1/2. Both answers failed the judge. Alternate LiveCodeBench versions also make strict filename counts pessimistic; the supplementary metric addresses identity, not passage sufficiency. This remains a regression/diagnostic case.

## Step 6. Architectural Impact Analysis

Analyze the impact of the retrieval strategy.

• What improved?
• What remained challenging?
• Did the strategy address the original failure?

### Improvements observed

Response:

Complete filename coverage was 5/14 for hybrid, 8/14 for decomposition, 7/14 for graph, and 6/14 for combined retrieval. Strict answer passes were 8, 12, 10, and 13 out of 20 respectively. The database comparison demonstrates a concrete improvement at the same context budget. The exact-quotation task still passed in all four modes. Saving passages, subqueries, graph paths, and hashes also made failures easier to diagnose.

### Remaining limitations or challenges

Response:

The changes do not reliably solve every multi-paper question. Decomposition can omit or blur an aspect; graph neighbors can be broadly related yet unhelpful, and correct documents can yield insufficient chunks. Graph mode selected 8 graph-only context chunks across its 20 cases; combined selected 8. Much of the measured gain can come from reranking/diversity rather than new graph evidence. A reranking-only control would be needed to isolate traversal's marginal benefit.

Metadata extraction sampled 39 long PDFs and rejected 1,503 reference quotations that did not match their claimed pages. There are only 54 resolved reference edges, and many topics have inconsistent wording. Proceedings volumes need article-level segmentation. Version-aware scoring can credit a different edition without proving its passage contains the required claim. The inherited judge sees filenames and reference notes, not the full passages, so its pass score is not a claim-level grounding guarantee. Example 1 demonstrates a false positive. Annotation metadata also remains model-generated despite successful quotation checks.

### Did the strategy address the original failure?

Response:

Partially. The redesign can improve multi-source coverage and recover complete answers, as the self-repair retrieval and database comparison show. It also leaves difficult cases unresolved and sometimes worsens selection. The results support using the advanced modes selectively and inspecting their evidence; they do not support assuming that combining more retrieval mechanisms always improves an answer.

## Step 7. Reflection and Next Steps

Reflect on the effectiveness of the architectural redesign.

• What did you learn from implementing this strategy?
• What would you improve next?
• Are there additional retrieval failures that still need to be addressed?

### Reflection on the architectural redesign

Response:

I learned that preserving distinct information needs and selecting useful passages matter as much as adding relationships. The email lab's seed-and-expand pattern transferred well, but research PDFs required explicit reference matching, version handling, and treatment of collections. Graph edges are useful retrieval hints, not evidence of an answer or proof of influence.

The implementation incurred about $3.14 in recorded successful annotation calls, excluding failed attempts. Retrieval also adds planner calls and graph/reranking work. These costs should be justified against observable gains. A partial pilot led to a provenance-label correction and clearer single-subject planner instructions before the final comparison; no independent held-out test was used.

### Specific improvements or next steps

Response:

First, split proceedings into logical papers and extract complete bibliographies with normalized identifiers and better author/topic disambiguation. Next, add a reranking/diversity-only control and a held-out multi-paper test set, then repeat answer grading to quantify variability. Improve passage selection for each requested detail, evaluate larger but matched context budgets, and add a passage-aware citation/grounding check. Keep unsupported-question cases and observed regressions in the test set. Select a default strategy only after these additional controls establish a dependable benefit.

## End of Required Capstone Checkpoint 4.1

Return to the assignment page in the learning platform to upload and submit your completed capstone checkpoint and complete any remaining items in this module.

© MIT xPRO® 2026. All rights reserved.
