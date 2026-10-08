# Checkpoint 5.1 evaluation evidence

Generated from the saved per-case JSON. Passes require every rubric criterion to be both complete and supported, with no material unsupported claims flagged by the judge.

| System | Task passes | Supported criteria | Chat calls | Chat tokens | Embedding requests | Median seconds | Mean context characters |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 0/3 | 6/11 | 3 | 4,153 | 3 | 3.65 | 3,520 |
| baseline_wide | 2/3 | 11/11 | 3 | 12,112 | 3 | 4.89 | 14,013 |
| initial | 2/3 | 9/11 | 8 | 17,410 | 8 | 8.84 | 7,289 |
| refined | 2/3 | 11/11 | 29 | 72,225 | 3 | 15.55 | 7,226 |

Chat calls and tokens exclude judging and embeddings. Elapsed time excludes corpus initialization and judging. Each successful hybrid search makes one embedding request. Counts do not include transparent provider retries. One malformed judge response required regrading a saved answer; that failed attempt’s tokens were not captured. No dollar cost was measured. This is one development-set run per case and mode, not a repeated or held-out benchmark.

## Passage-reviewed results

These are assistant-conducted inspections of the saved answers and passages, not independent human grades. They correct specific automated-grader errors described in [review notes](review_notes.md) and [per-criterion reviews](passage_review.json). The table above preserves raw automated results.

| System | Reviewed task passes | Reviewed supported criteria |
| --- | ---: | ---: |
| baseline | 0/3 | 5/11 |
| baseline_wide | 1/3 | 9/11 |
| initial | 1/3 | 7/11 |
| refined | 3/3 | 11/11 |

The selected questions are reused Module 4 evaluation cases, not topics prescribed by the worksheet. The pre-LangGraph implementation is excluded and archived under ../archive/pre_langgraph/. LangGraph development runs remain in the directories ending in `_pilot`; their usage is separate from the final comparison. Tool decisions in the current graphs occur after observations; this small development set does not establish general superiority over fixed retrieval.

## benchmark_design_code_and_robotics

Compare the evaluation design of LiveCodeBench and Bench-Push. For each benchmark, state what is being evaluated, what makes the test setting realistic or reproducible, and what metrics or task categories are used.

| System | Supported criteria | Pass | Seconds | Chat calls | Chunks | Stop |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| baseline | 2/4 | False | 3.645 | 1 | 3 | fixed_single_pass |
| baseline_wide | 4/4 | False | 4.886 | 1 | 12 | fixed_single_pass |
| initial | 4/4 | True | 8.883 | 3 | 10 | retrieval_budget |
| refined | 4/4 | False | 15.555 | 9 | 7 | coverage_complete |

Reviewed coverage: baseline 1/4, baseline_wide 3/4, initial 2/4, refined 4/4.

### baseline

Full passages, answer, prompt, usage, and provenance: [baseline JSON](baseline__benchmark_design_code_and_robotics.json).

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [1, 2, 3]. This states the code-LLM setting, and the passages support live competition problems from reputable sites with quality-validated tests and reduced contamination by using competition platforms.
- Criterion 2: complete=True, supported=True; evidence [3]. The passage explicitly lists code generation, self-repair, and code execution; at least two of the required task categories are present.
- Criterion 3: complete=False, supported=False; evidence []. The answer provides no Bench-Push description; it explicitly says there is not enough information to compare Bench-Push.
- Criterion 4: complete=False, supported=False; evidence []. The answer does not mention Bench-Push metrics, partial completion, interaction effort, simulated environments, or baseline demonstrations.
- Unsupported claim: The answer's claim that the provided context does not provide enough information about Bench-Push is a refusal, not a factual error; it is simply incomplete for the task.
- Unsupported claim: The answer's claim that LiveCodeBench focuses on competition problems sourced from three platforms is supported by the passages, but the statement that this provides reduced contamination is not directly stated in the cited text.

### baseline_wide

Full passages, answer, prompt, usage, and provenance: [baseline_wide JSON](baseline_wide__benchmark_design_code_and_robotics.json).

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [1, 6, 9, 11]. The answer states LiveCodeBench is for code LLMs and cites self-repair and code execution; the passages support code-capability evaluation, live/contamination-free design, and competition-sourced problems.
- Criterion 2: complete=True, supported=True; evidence [3]. The passage explicitly lists code generation, self-repair, and code execution as LiveCodeBench scenarios, so the answer’s inclusion of at least two of these is supported.
- Criterion 3: complete=True, supported=True; evidence [4, 5, 8]. The passages describe Bench-Push as a benchmark for pushing-based navigation and manipulation tasks in mobile robots, with simulated environments and sim-to-real deployment support.
- Criterion 4: complete=True, supported=True; evidence [5, 7, 8, 12]. The answer covers efficiency, interaction effort/trade-offs, and partial completion; the passages support these metrics and note baseline implementations for reproducibility/support.
- Unsupported claim: The answer’s statement that the context does not provide the exact metric names/formulas for LiveCodeBench and Bench-Push is not directly established by the passages, though it is presented as a summary of the retrieved context rather than a benchmark fact.

### initial

Full passages, answer, prompt, usage, and provenance: [initial JSON](initial__benchmark_design_code_and_robotics.json).

Action trace:

1. **retrieve** — {"query": "Compare the evaluation design of LiveCodeBench and Bench-Push. For each benchmark, state what is being evaluated, what makes the test setting realistic or reproducible, and what metrics or task categories are used."}.  Added 3 passages.
2. **retrieve** — . Passages provide strong LiveCodeBench details, but there is no evidence for Bench-Push’s evaluation setup, realism/reproducibility, or metrics/task categories. Added 0 passages.
3. **retrieve** — {"query": "Bench-Push evaluation design realistic reproducible metrics task categories what is evaluated"}.  Added 3 passages.
4. **retrieve** — . We have some LiveCodeBench and Bench-Push details, but not enough to fully compare both on what exactly is evaluated and the specific metrics/task categories; targeted retrieval should fill those missing points. Added 0 passages.
5. **retrieve** — {"query": "LiveCodeBench evaluation scenarios metrics what is evaluated reproducible realistic competition programming code generation self-repair code execution"}.  Added 3 passages.
6. **retrieve** — {"query": "Bench-Push metrics task categories navigation manipulation efficiency interaction trade-offs partial task completions"}.  Added 1 passages.
7. **stop** — . budget checked before model call Added 0 passages.
8. **answer** — .  Added 0 passages.

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [1, 7]. The answer states LiveCodeBench evaluates code LLMs on live competition problems and notes reduced contamination via reputable competition websites and validated quality; passages support both the code-LLM scenario set and the contamination-reducing source of problems.
- Criterion 2: complete=True, supported=True; evidence [7, 3]. The answer includes self-repair, code execution, and test output prediction, which are explicitly listed in the passage.
- Criterion 3: complete=True, supported=True; evidence [5, 6]. The answer correctly describes Bench-Push as a benchmark for pushing-based navigation and manipulation tasks in mobile robots, matching the passages.
- Criterion 4: complete=True, supported=True; evidence [5, 6, 10]. The answer mentions efficiency, interaction effort/trade-offs, partial task completion, and baseline implementations for extensibility/reproducibility, all supported by the passages.

### refined

Full passages, answer, prompt, usage, and provenance: [refined JSON](refined__benchmark_design_code_and_robotics.json).

Action trace:

1. **lookup_papers** — . Need the specific LiveCodeBench paper first; title lookup is the direct path to obtain a filename and evidence for its evaluation design. Added 0 passages.
2. **lookup_papers** — {"title": "LiveCodeBench", "author": "", "year": null}.  Added 0 passages.
3. **lookup_papers** — . Need to discover the exact Bench-Push paper before reading evidence; LiveCodeBench is already identified but Bench-Push has no catalogue hit yet. Added 0 passages.
4. **lookup_papers** — {"title": "Bench-Push", "author": "", "year": null}.  Added 0 passages.
5. **read_paper** — Find the sections describing the evaluation design, task categories, metrics, and test setting realism/reproducibility in LiveCodeBench.; file `DBLP_journals_corr_abs-2403-07974.pdf`. LiveCodeBench has been identified; I need original PDF passages on its evaluation setup before I can compare it to Bench-Push. Added 0 passages.
6. **read_paper** — {"filename": "DBLP_journals_corr_abs-2403-07974.pdf", "query": "Find the sections describing the evaluation design, task categories, metrics, and test setting realism/reproducibility in LiveCodeBench."}.  Added 3 passages.
7. **read_paper** — Locate the evaluation design details for LiveCodeBench: what is evaluated, the task categories, and any reproducibility/realism aspects such as time-segmented or contamination-free setup, plus metrics used.; file `DBLP_journals_corr_abs-2403-07974.pdf`. LiveCodeBench still needs a focused passage for the specific task categories, metrics, and the realism/reproducibility properties. Added 0 passages.
8. **read_paper** — {"filename": "DBLP_journals_corr_abs-2403-07974.pdf", "query": "Locate the evaluation design details for LiveCodeBench: what is evaluated, the task categories, and any reproducibility/realism aspects such as time-segmented or contamination-free setup, plus metrics used."}.  Added 1 passages.
9. **read_paper** — Find the Bench-Push sections describing what is evaluated, the task categories, the evaluation metrics, and what makes the test setting realistic or reproducible.; file `DBLP_conf_icra_CamposISK19.pdf`. LiveCodeBench evidence is sufficient; Bench-Push still lacks direct PDF passages for evaluation design, task categories, metrics, and realism/reproducibility. Added 0 passages.
10. **read_paper** — {"filename": "DBLP_conf_icra_CamposISK19.pdf", "query": "Find the Bench-Push sections describing what is evaluated, the task categories, the evaluation metrics, and what makes the test setting realistic or reproducible."}.  Added 3 passages.
11. **answer** — . The retrieved PDF passages cover both benchmarks’ evaluation design, task categories, realism/reproducibility, and metrics sufficiently to answer. Added 0 passages.
12. **answer** — .  Added 0 passages.
13. **answer** — .  Added 0 passages.

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [1, 4]. The answer identifies LiveCodeBench as evaluating code LLMs and says it uses live, time-stamped new contest problems to avoid contamination, matching the criterion.
- Criterion 2: complete=True, supported=True; evidence [1, 3, 4]. The answer includes all three listed task categories, which satisfies the requirement for at least two, and the passages explicitly name these scenarios.
- Criterion 3: complete=True, supported=True; evidence [5, 7]. The answer correctly states Bench-Push is for pushing-based mobile-robot navigation and manipulation in simulated environments, supported by the benchmark description.
- Criterion 4: complete=True, supported=True; evidence [5, 6, 7]. The answer covers efficiency and interaction effort, and also mentions reproducibility via ad hoc setups being replaced by a unified benchmark and baseline implementations, which the passages support.
- Unsupported claim: For newer models, it only uses problems released after the model’s cutoff date, so the model likely has not seen the exact problem during training.
- Unsupported claim: The benchmark also includes simulations with varying complexity and shows that relative performance transfers consistently to a physical testbed, suggesting the setup is meaningful beyond simulation.
- Unsupported claim: The available context does not give the exact formulas for those metrics, only their intended roles.

Final answer:

Here is a direct comparison of the two benchmarks based on the retrieved context.

## LiveCodeBench
**What is being evaluated:**  
LiveCodeBench evaluates large language models for code, with a broader focus than standard code generation. It covers “a broader range of code-related capabilities, such as self-repair, code execution, and test output prediction” in addition to code generation [Source 1]. The paper also says it evaluates code LLMs on “three additional scenarios,” including **self-repair** and other tasks beyond generation [Source 4].

**What makes the setting realistic or reproducible:**  
LiveCodeBench is designed to be **contamination-free** by using **live updates**: it collects **new problems over time** from weekly contests on **LeetCode, AtCoder, and CodeForces** and tags them with a **release date** [Source 1, Source 4]. For newer models, it only uses problems **released after the model’s cutoff date**, so the model likely has not seen the exact problem during training. The paper says this **time-segmented evaluation** helps ensure fair comparisons [Source 4].  

**Metrics or task categories used:**  
The retrieved context explicitly names task categories such as **self-repair**, **code execution**, and **test output prediction**, along with code generation [Source 1, Source 4]. However, the available documents do **not provide enough information** on the exact scoring metrics used for LiveCodeBench.

## Bench-Push
**What is being evaluated:**  
Bench-Push evaluates **pushing-based navigation and manipulation tasks for mobile robots** [Source 5]. It is a benchmark for robots that must use **pushing or nudging strategies** to accomplish goals in cluttered environments [Source 5].

**What makes the setting realistic or reproducible:**  
Bench-Push addresses the problem that prior evaluations used **ad hoc setups**, which limited reproducibility and cross-comparison [Source 5]. It responds by providing a **unified benchmark** with a structured set of simulated environments and evaluation metrics [Source 5, Source 6]. The benchmark also includes simulations with varying complexity and shows that relative performance transfers consistently to a physical testbed, suggesting the setup is meaningful beyond simulation [Source 7].

**Metrics or task categories used:**  
Bench-Push includes several task categories:  
- navigating a maze with movable obstacles  
- autonomous ship navigation in ice-covered waters  
- box delivery  
- area clearing  
all “with varying levels of complexity” [Source 5].  

It also introduces **novel evaluation metrics** to capture **efficiency, interaction quality, and interaction effort** [Source 5, Source 6]. The available context does not give the exact formulas for those metrics, only their intended roles [Source 5, Source 6].

## Bottom line
- **LiveCodeBench** focuses on **code LLM capability evaluation**, especially broader coding behaviors beyond generation, and improves realism/reproducibility through **time-stamped, newly released contest problems** to avoid contamination [Source 1, Source 4].  
- **Bench-Push** focuses on **mobile robot pushing-based navigation/manipulation**, improving reproducibility by replacing ad hoc evaluations with a **standardized benchmark suite** and metrics across **multiple simulated task types** [Source 5, Source 6].

Source map:

- Source 1: `DBLP_journals_corr_abs-2403-07974.pdf`, page 1.
- Source 2: `DBLP_journals_corr_abs-2403-07974.pdf`, page 4.
- Source 3: `DBLP_journals_corr_abs-2403-07974.pdf`, page 4.
- Source 4: `DBLP_journals_corr_abs-2403-07974.pdf`, page 3.
- Source 5: `DBLP_conf_icra_CamposISK19.pdf`, page 1.
- Source 6: `DBLP_conf_icra_CamposISK19.pdf`, page 2.
- Source 7: `DBLP_conf_icra_CamposISK19.pdf`, page 8.
## self_repair_benchmark_and_risk

Synthesize what the corpus says about self-repair in code generation: describe the repair workflow, explain how LiveCodeBench evaluates related capabilities, and explain why counterfeit-samples work recommends caution with self-repair or model-based reranking.

| System | Supported criteria | Pass | Seconds | Chat calls | Chunks | Stop |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| baseline | 2/3 | False | 3.65 | 1 | 3 | fixed_single_pass |
| baseline_wide | 3/3 | True | 4.957 | 1 | 12 | fixed_single_pass |
| initial | 3/3 | True | 8.835 | 3 | 7 | sufficient_evidence |
| refined | 3/3 | True | 16.035 | 12 | 7 | coverage_complete |

Reviewed coverage: baseline 2/3, baseline_wide 3/3, initial 3/3, refined 3/3.

### baseline

Full passages, answer, prompt, usage, and provenance: [baseline JSON](baseline__self_repair_benchmark_and_risk.json).

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [3]. This matches the described generate-run-test-feedback-repair workflow in the Olausson paper passage.
- Criterion 2: complete=False, supported=False; evidence [1]. The passage supports self-repair as a probe of code understanding, but the answer does not identify LiveCodeBench specifically or mention its evaluation of self-repair, code execution, and test-output prediction.
- Criterion 3: complete=True, supported=True; evidence [2]. This is directly supported by the counterfeit-samples passage and grounds the caution about self-repair and model-based reranking without external feedback.
- Unsupported claim: The answer attributes LiveCodeBench-related evaluation claims to source 1, but the provided passage from source 1 does not mention LiveCodeBench or test-output prediction.

### baseline_wide

Full passages, answer, prompt, usage, and provenance: [baseline_wide JSON](baseline_wide__self_repair_benchmark_and_risk.json).

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [3, 7]. The answer explicitly names the workflow stages and describes the sequence from generation to execution, feedback, and repair; passages 3 and 7 state this same workflow.
- Criterion 2: complete=True, supported=True; evidence [12]. The answer identifies the three requested LiveCodeBench-related capabilities and the broader holistic evaluation framing, which is directly supported by passage 12.
- Criterion 3: complete=True, supported=True; evidence [2, 4, 8, 9]. The answer accurately summarizes the counterfeit-samples warning, including low repair rates, reliance on self-generated feedback, and caution about self-repair/model-based reranking without external feedback; passages 2 and 4 support the warning, and 8-9 support the self-repair limitations.

### initial

Full passages, answer, prompt, usage, and provenance: [initial JSON](initial__self_repair_benchmark_and_risk.json).

Action trace:

1. **retrieve** — {"query": "Synthesize what the corpus says about self-repair in code generation: describe the repair workflow, explain how LiveCodeBench evaluates related capabilities, and explain why counterfeit-samples work recommends caution with self-repair or model-based reranking."}.  Added 3 passages.
2. **retrieve** — . We have the general self-repair workflow and the cautionary note, but no source yet describing LiveCodeBench’s evaluation of related capabilities, so the answer is incomplete. Added 0 passages.
3. **retrieve** — {"query": "What does LiveCodeBench say about evaluating self-repair or repair-related capabilities in code generation, including its metrics or setup?"}.  Added 3 passages.
4. **retrieve** — {"query": "What additional passages in the corpus explain the self-repair workflow and the cautionary conclusion about counterfeit samples, self-repair, or model-based reranking?"}.  Added 1 passages.
5. **answer** — . Enough evidence is present for all three requested parts: the repair workflow, LiveCodeBench’s self-repair setup/metrics, and the counterfeit-samples paper’s caution about self-repair/model-based reranking. Added 0 passages.
6. **answer** — .  Added 0 passages.

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [3]. This directly states the generation, execution/testing, feedback, and repair workflow.
- Criterion 2: complete=True, supported=True; evidence [4]. This matches the paper’s listed scenarios and explicitly identifies self-repair, code execution, and test output prediction.
- Criterion 3: complete=True, supported=True; evidence [2, 7]. The answer explains counterfeit samples are adversarial, hard to assess/execute/repair, and that this motivates caution with self-repair and model-based reranking; the passages support these claims.

### refined

Full passages, answer, prompt, usage, and provenance: [refined JSON](refined__self_repair_benchmark_and_risk.json).

Action trace:

1. **lookup_papers** — . Named work first; need the LiveCodeBench paper to inspect its evaluation of related capabilities before answering. Added 0 passages.
2. **lookup_papers** — {"title": "LiveCodeBench", "author": "", "year": null}.  Added 0 passages.
3. **read_paper** — self-repair repair workflow evaluation self-correction reranking counterfeit samples caution; file `DBLP_conf_iclr_JainHGLYZWSSS25.pdf`. Need direct passages from LiveCodeBench PDF on evaluation of related capabilities; self-repair and counterfeit-samples still need evidence from their source papers. Added 0 passages.
4. **read_paper** — {"filename": "DBLP_conf_iclr_JainHGLYZWSSS25.pdf", "query": "self-repair repair workflow evaluation self-correction reranking counterfeit samples caution"}.  Added 3 passages.
5. **read_paper** — counterfeit samples self-repair reranking caution model-based reranking why recommend caution; file `DBLP_conf_iclr_JainHGLYZWSSS25.pdf`. LiveCodeBench evidence is present; the remaining gap is the counterfeit-samples paper and its caution about self-repair/reranking, so I need to locate that specific work next. Added 0 passages.
6. **read_paper** — {"filename": "DBLP_conf_iclr_JainHGLYZWSSS25.pdf", "query": "counterfeit samples self-repair reranking caution model-based reranking why recommend caution"}.  Added 1 passages.
7. **answer** — . The LiveCodeBench paper provides evidence for the self-repair workflow and its evaluation setup, but the current corpus evidence does not yet include the counterfeit-samples paper that would justify the caution claim, so I cannot fully synthesize that part without a new source. Added 0 passages.
8. **plan** — .  Added 0 passages.
9. **lookup_papers** — . LiveCodeBench evidence is present, but the counterfeit-samples paper is still missing; need to identify the exact work before reading its caution about self-repair/reranking. Added 0 passages.
10. **lookup_papers** — {"title": "counterfeit samples", "author": "", "year": null}.  Added 0 passages.
11. **retry** — .  Added 0 passages. Error: The evidence audit still lists gaps. Gather new PDF evidence with retrieve or read_paper before attempting answer again.
12. **retrieve** — counterfeit samples self-repair model-based reranking caution code generation evaluation. Need new corpus evidence for the missing counterfeit-samples work and its cautionary claim before answering. Added 0 passages.
13. **retrieve** — {"query": "counterfeit samples self-repair model-based reranking caution code generation evaluation"}.  Added 3 passages.
14. **answer** — . The corpus now has direct passages for LiveCodeBench self-repair and the counterfeit-samples caution, so I can synthesize the requested points from the PDF evidence. Added 0 passages.
15. **answer** — .  Added 0 passages.
16. **answer** — .  Added 0 passages.

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [2]. This matches the self-repair workflow: problem statement -> candidate program -> error feedback (exception or failing test) -> repaired program. The passage explicitly describes this pipeline.
- Criterion 2: complete=True, supported=True; evidence [3, 2]. The answer identifies LiveCodeBench’s evaluation scenarios and includes all three requested related capabilities: self-repair, code execution, and test output prediction, supported by the benchmark description.
- Criterion 3: complete=True, supported=True; evidence [5, 6]. The cited passages directly support the cautionary conclusion: counterfeit samples are adversarial to model-only judgment/repair, repair rates are low, and the recommendation specifically warns about self-repair and model-based reranking without external feedback.

Final answer:

The corpus describes self-repair in code generation as a workflow where the model first produces a candidate program from a problem statement, then receives error feedback if that program is wrong, and is asked to generate a corrected version. In the LiveCodeBench paper, this is explicitly framed as a “self-repair” scenario based on prior work: the model generates code, and if there is a mistake it is additionally given feedback such as an exception message or a failing test case, then tasked with repairing the program [Source 2]. The same paper also notes that self-repair is one of the broader code capabilities they evaluate because it reflects an important component in real coding workflows, alongside code generation, code execution, and test output prediction [Source 3].

LiveCodeBench evaluates related capabilities by using a suite of scenarios rather than only direct code generation. It says the benchmark is a “holistic” evaluation of code LLMs and includes four scenarios: code generation, self-repair, code execution, and test output prediction [Source 3]. For code generation, evaluation is by functional correctness on unseen test cases, using PASS@1 as the fraction of problems for which the model produces a program that passes all tests [Source 2]. The benchmark’s motivation is that standard code-generation benchmarks are not enough because they mainly cover one dimension of code ability; LiveCodeBench instead measures broader capabilities that are useful components in coding pipelines and can be assessed automatically [Source 1][Source 3].

The counterfeit-samples work recommends caution with self-repair and model-based reranking because it finds that counterfeit samples behave somewhat adversarially: models often struggle to judge whether such samples are correct, to reason about their execution as if they were correct programs, and to repair them effectively [Source 5]. It also says counterfeit samples from easier problems are not necessarily easier to assess and are only slightly easier to execute and repair, showing an inconsistency between generation and understanding abilities [Source 5]. Based on this, the paper recommends caution in schemes like self-repair and model-based reranking, especially when no external feedback is incorporated [Source 5][Source 6]. The available documents do not provide more detail on the exact reranking procedure beyond that warning.

Source map:

- Source 1: `DBLP_conf_iclr_JainHGLYZWSSS25.pdf`, page 1.
- Source 2: `DBLP_conf_iclr_JainHGLYZWSSS25.pdf`, page 4.
- Source 3: `DBLP_conf_iclr_JainHGLYZWSSS25.pdf`, page 4.
- Source 4: `DBLP_conf_iclr_JainHGLYZWSSS25.pdf`, page 41.
- Source 5: `DBLP_conf_acl_GuLJOLSS24.pdf`, page 2.
- Source 6: `DBLP_journals_corr_abs-2402-19475.pdf`, page 3.
- Source 7: `DBLP_journals_corr_abs-2402-19475.pdf`, page 6.
## synthesis_search_strategies

Compare CVC4SY and adaptive concretization as search strategies for syntax-guided synthesis. What search space does each address, what mechanism does each use, and what tradeoff or benefit is each trying to achieve?

| System | Supported criteria | Pass | Seconds | Chat calls | Chunks | Stop |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| baseline | 2/4 | False | 2.969 | 1 | 3 | fixed_single_pass |
| baseline_wide | 4/4 | True | 3.387 | 1 | 12 | fixed_single_pass |
| initial | 2/4 | False | 4.453 | 2 | 3 | sufficient_evidence |
| refined | 4/4 | True | 13.42 | 8 | 5 | coverage_complete |

Reviewed coverage: baseline 2/4, baseline_wide 3/4, initial 2/4, refined 4/4.

### baseline

Full passages, answer, prompt, usage, and provenance: [baseline JSON](baseline__synthesis_search_strategies.json).

Rubric assessment:

- Criterion 1: complete=False, supported=False; evidence []. The answer does not state that CVC4SY searches grammar-constrained terms using bounded term enumeration. Instead, it discusses generic symbolic search over candidate programs, which is not the same claim and is not supported by the supplied passages.
- Criterion 2: complete=False, supported=False; evidence []. The answer explicitly says the documents do not provide enough information about CVC4SY, so it omits the required algebraic-datatype encoding and optimized brute-force/combined strategy. No passage supports those omitted details.
- Criterion 3: complete=True, supported=True; evidence [1, 3]. This matches the passages stating that adaptive concretization combines explicit and symbolic search and concretizes influential unknowns with random values while symbolically searching the rest.
- Criterion 4: complete=True, supported=True; evidence [1, 2, 3]. The passages explicitly describe the explicit-vs-symbolic benefit tradeoff and the natural parallelization / performance motivation on multi-core machines.
- Unsupported claim: CVC4SY / symbolic search over the candidate space
- Unsupported claim: The tradeoff is that symbolic methods can be efficient for some unknowns, but the context also notes that some unknowns can make synthesis time grow dramatically.

### baseline_wide

Full passages, answer, prompt, usage, and provenance: [baseline_wide JSON](baseline_wide__synthesis_search_strategies.json).

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [7]. The answer says CVC4SY searches candidate terms/programs and uses bounded term enumeration, which matches the passage describing an enumerative approach with term enumerator outputting candidate terms and bounded term generation.
- Criterion 2: complete=True, supported=True; evidence [4]. The answer explicitly mentions algebraic-datatype encoding, optimized brute-force enumeration, and a combined strategy, all directly supported by the CVC4SY abstract.
- Criterion 3: complete=True, supported=True; evidence [1, 3]. The answer correctly describes adaptive concretization as searching assignments to unknowns by mixing explicit concretization with symbolic search, exactly as stated in the passages.
- Criterion 4: complete=True, supported=True; evidence [1, 2, 3]. The passages say adaptive concretization combines benefits of explicit and symbolic search, parallelizes naturally, and has good parallel scalability, which supports the stated motivation and tradeoff.

### initial

Full passages, answer, prompt, usage, and provenance: [initial JSON](initial__synthesis_search_strategies.json).

Action trace:

1. **retrieve** — {"query": "Compare CVC4SY and adaptive concretization as search strategies for syntax-guided synthesis. What search space does each address, what mechanism does each use, and what tradeoff or benefit is each trying to achieve?"}.  Added 3 passages.
2. **answer** — . The passages already state both methods’ target search spaces, mechanisms, and intended benefits/tradeoffs: CVC4SY is about symbolic search over SyGuS candidates, while adaptive concretization targets symbolic-search unknowns that are highly influential by concretizing some explicitly and solving the rest symbolically to gain scalability/parallelism. Added 0 passages.
3. **answer** — .  Added 0 passages.

Rubric assessment:

- Criterion 1: complete=False, supported=False; evidence []. The answer does not state that CVC4SY searches grammar-constrained terms using bounded term enumeration, and no passage about CVC4SY is provided to support that claim.
- Criterion 2: complete=False, supported=False; evidence []. The answer omits the required CVC4SY mechanisms (algebraic-datatype encoding and optimized brute-force enumeration or their combined strategy), so this criterion is not covered and not supported.
- Criterion 3: complete=True, supported=True; evidence [1, 3]. The passages state adaptive concretization targets unknowns that parameterize the symbolic search space and uses explicit search to concretize influential unknowns while symbolically searching the remainder.
- Criterion 4: complete=True, supported=True; evidence [1, 3]. The passages explicitly mention the explicit-versus-symbolic benefit combination and natural parallelization/multi-core motivation.
- Unsupported claim: The answer claims that the retrieved context does not provide a direct description of CVC4SY's mechanism or exact search space, which is a refusal rather than an unsupported factual claim.

### refined

Full passages, answer, prompt, usage, and provenance: [refined JSON](refined__synthesis_search_strategies.json).

Action trace:

1. **retrieve** — CVC4SY syntax-guided synthesis search strategy adaptive concretization search strategy compare search space mechanism tradeoff benefit. Need to discover the relevant papers or passages for both named search strategies before comparing them. Added 0 passages.
2. **retrieve** — {"query": "CVC4SY syntax-guided synthesis search strategy adaptive concretization search strategy compare search space mechanism tradeoff benefit"}.  Added 3 passages.
3. **answer** — . The retrieved passages already support both named strategies: CVC4SY’s symbolic search over syntax-guided candidates and adaptive concretization’s hybrid explicit/symbolic search over influential unknowns, along with their intended tradeoffs. Added 0 passages.
4. **plan** — .  Added 0 passages.
5. **retrieve** — CVC4SY syntax-guided synthesis explicit symbolic search strategy search space mechanism tradeoff benefit. Adaptive concretization is covered, but there is still no evidence for CVC4SY; retrieve specifically for CVC4SY to find passages describing its search strategy and tradeoff. Added 0 passages.
6. **retrieve** — {"query": "CVC4SY syntax-guided synthesis explicit symbolic search strategy search space mechanism tradeoff benefit"}.  Added 2 passages.
7. **answer** — . The retrieved passages now cover both named strategies: adaptive concretization and CVC4SY. Added 0 passages.
8. **answer** — .  Added 0 passages.
9. **answer** — .  Added 0 passages.

Rubric assessment:

- Criterion 1: complete=True, supported=True; evidence [4]. The answer states CVC4SY searches bounded term-enumeration space, matching the paper’s description of CVC4SY as based on bounded term enumeration strategies.
- Criterion 2: complete=True, supported=True; evidence [4]. This directly matches the paper’s three strategies: algebraic datatypes encoding, brute-force enumeration, and a combined strategy.
- Criterion 3: complete=True, supported=True; evidence [1, 3]. The passages say adaptive concretization targets symbolic-search unknowns, concretizing influential unknowns explicitly and searching symbolically for the rest.
- Criterion 4: complete=True, supported=True; evidence [1, 2, 3]. The passages explicitly mention the explicit-vs-symbolic combination, natural parallelization, and improved performance / good parallel scalability.

Final answer:

CVC4SY and adaptive concretization are both synthesis search strategies, but they address different parts of the search problem and use different mechanisms.

- **CVC4SY** addresses **bounded term enumeration in the SyGuS candidate-program space**. It is a solver based on “three bounded term enumeration strategies”: one “encodes term enumeration as an extension of the quantifier-free theory of algebraic datatypes,” one uses “a highly optimized brute-force algorithm,” and one “combines elements of the others” [Source 4]. Its benefit is to make enumerative SyGuS search “smart and fast,” and the paper reports that choosing among these strategies “leads to significant improvements over state-of-the-art SyGuS solvers” [Source 4].

- **Adaptive concretization** addresses the **symbolic-search parameter space** in synthesis, specifically the unknowns that parameterize the search space. The paper says these unknowns “are not all equally important in terms of solving time,” and some “highly influential unknowns” make synthesis time grow dramatically [Source 1][Source 3]. Its mechanism is to use “explicit search to concretize influential unknowns with randomly chosen values” and then “search symbolically for the remaining unknowns” [Source 1][Source 3]. Its benefit is to “combine many of the benefits of explicit and symbolic search,” parallelize naturally, and improve performance; the paper also says it “outperform[s] Sketch in many cases” and has “good parallel scalability” [Source 1][Source 2].

**Comparison of tradeoff/benefit:**
- **CVC4SY** is trying to get the best performance from **enumerative bounded search** by selecting among enumeration methods, including a brute-force one, to improve speed and coverage on SyGuS benchmarks [Source 4][Source 5].
- **Adaptive concretization** is trying to reduce the cost of **symbolic search** by partially fixing hard-to-handle unknowns, trading some symbolic generality for faster solving and natural parallelism [Source 1][Source 3].

The available documents do not provide enough information to compare them beyond these points in a more detailed algorithmic sense.

Source map:

- Source 1: `DBLP_conf_cav_JeonQSF15.pdf`, page 2.
- Source 2: `DBLP_conf_cav_JeonQSF15.pdf`, page 1.
- Source 3: `DBLP_journals_fmsd_JeonQSF17.pdf`, page 2.
- Source 4: `DBLP_conf_cav_GaoKDRSAK19.pdf`, page 92.
- Source 5: `DBLP_conf_cav_GaoKDRSAK19.pdf`, page 99.
