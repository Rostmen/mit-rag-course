# Lab 6.2 measurement approach

The first audit measured latency and chat tokens by role, but did not implement
Lab 6.2's full measurement method. This supplemental experiment adds separate
input/output/cache counts, per-model tallies, priced estimates, and a small
same-question comparison of uniform and mixed model configurations.

The Module 5 agent remains unchanged. A Module 6 meter selects the model used by
the existing calls and retains their original usage metadata. Requirement
extraction and coverage checking belong to the planning side; only final answer
generation uses the answer model. This mapping is explicit because the capstone
has more call types than the lab's email agent.

Two fixed research questions (one explanation, one comparison) run with:

- Current: GPT-5.4-mini for all calls.
- Cheap: GPT-4o-mini for all calls.
- Mixed: GPT-5.4-mini for planning/checks and GPT-4o-mini for answers.

This is a small adaptation of the lab's cost ladder. It does not run the optional
pro tier or free models, alter the deployed capstone configuration, or assume the
lab's illustrative quality findings apply to research papers. Every query starts
with fresh conversation state and usage accounting. All runs share the same
local corpus/index and unchanged prompts, tools, limits and temperature.

## Cost calculation

The lab's full-input-rate estimate is
`(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`.
Cached input is a subset of input tokens, not extra tokens. A second estimate
applies its discount:
`((input_tokens − cache_read) × input_rate + cache_read × cache_rate + output_tokens × output_rate) / 1,000,000`.
Missing usage or cache fields are flagged; missing prices cannot silently become
zero. The lab's hardcoded rates were not copied because they differ from the
current advertised rates.

Standard OpenRouter prices checked on October 9, 2026, in USD per million tokens:
[GPT-5.4-mini](https://openrouter.ai/openai/gpt-5.4-mini) uses $0.75 input, $4.50 output,
and $0.075 cache reads; [GPT-4o-mini](https://openrouter.ai/openai/gpt-4o-mini) uses
$0.15 input, $0.60 output, and $0.075 cache reads. These estimates are not invoices;
provider routing, fees, and unreported retries may affect billing.

Unlike the lab README's simplified retrieval description, this capstone's hybrid
search creates query embeddings through an API. Those calls are counted as
requests but their token usage/cost is not captured. Corpus embeddings are reused.
Reported dollar estimates therefore cover chat calls only.

## Evidence and interpretation

The [raw runs](evidence/cost_6_2/runs.json) retain complete answers, PDF passages,
action traces and per-call usage. The [summary](evidence/cost_6_2/summary.json)
groups by model and role; [pricing](evidence/cost_6_2/pricing.json) records the
rate snapshot and formulas. The [manifest](evidence/cost_6_2/manifest.json) records
source fingerprints and experiment settings.

Quality is reviewed against the saved passages and the same criteria for all
configurations. No extra judge API calls are required. One run per question is
not a quality or latency benchmark; the experiment identifies trade-offs worth
investigating. Provider caching is not controlled, and the fixed run order may
benefit later configurations. Mixed routing is a measurement condition, not an
adopted improvement.
