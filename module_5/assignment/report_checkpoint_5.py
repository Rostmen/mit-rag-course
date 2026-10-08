"""Recompute the human-readable comparison directly from saved evaluation JSON."""
import json
from pathlib import Path
from audit_checkpoint_5 import summarize, reviewed_records

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE/'evidence'
MODES = ['baseline','baseline_wide','initial','refined']


def main():
    records = [json.loads(p.read_text()) for p in sorted(EVIDENCE.glob('*__*.json'))]
    records = [r for r in records if 'grade' in r]
    summary = summarize(records)
    reviews = reviewed_records(records)
    reviewed_summary = summarize(reviews)
    lines = ['# Checkpoint 5.1 evaluation evidence', '',
             'Generated from the saved per-case JSON. Passes require every rubric criterion to be both complete and supported, with no material unsupported claims flagged by the judge.', '',
             '| System | Task passes | Supported criteria | Chat calls | Chat tokens | Embedding requests | Median seconds | Mean context characters |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for mode in MODES:
        if mode not in summary:
            continue
        s = summary[mode]
        lines.append(f'| {mode} | {s["passes"]}/{s["cases"]} | {s["supported_criteria"]}/{s["total_criteria"]} | {s["chat_calls"]} | {s["chat_tokens"]:,} | {s["embedding_requests"]} | {s["median_seconds"]} | {s["mean_context_characters"]:,} |')
    lines.extend(['', 'Chat calls and tokens exclude judging and embeddings. Elapsed time excludes corpus initialization and judging. Each successful hybrid search makes one embedding request. Counts do not include transparent provider retries. One malformed judge response required regrading a saved answer; that failed attempt’s tokens were not captured. No dollar cost was measured. This is one development-set run per case and mode, not a repeated or held-out benchmark.', ''])
    lines.extend(['## Passage-reviewed results', '',
                  'These are assistant-conducted inspections of the saved answers and passages, not independent human grades. They correct specific automated-grader errors described in [review notes](review_notes.md) and [per-criterion reviews](passage_review.json). The table above preserves raw automated results.', '',
                  '| System | Reviewed task passes | Reviewed supported criteria |',
                  '| --- | ---: | ---: |'])
    for mode,s in reviewed_summary.items():
        lines.append(f'| {mode} | {s["passes"]}/{s["cases"]} | {s["supported_criteria"]}/{s["total_criteria"]} |')
    lines.extend(['', 'The selected questions are reused Module 4 evaluation cases, not topics prescribed by the worksheet. The pre-LangGraph implementation is excluded and archived under ../archive/pre_langgraph/. LangGraph development runs remain in the directories ending in `_pilot`; their usage is separate from the final comparison. Tool decisions in the current graphs occur after observations; this small development set does not establish general superiority over fixed retrieval.', ''])
    cases = json.loads((HERE/'capstone_checkpoint_5_test_inputs.json').read_text())
    for case in cases:
        lines.extend([f'## {case["id"]}', '', case['question'], '',
                      '| System | Supported criteria | Pass | Seconds | Chat calls | Chunks | Stop |',
                      '| --- | ---: | --- | ---: | ---: | ---: | --- |'])
        runs = [r for m in MODES for r in records if r['case_id']==case['id'] and r['mode']==m]
        for r in runs:
            g = r['grade']
            lines.append(f'| {r["mode"]} | {g["covered_criteria"]}/{g["total_criteria"]} | {g["passed"]} | {r["seconds"]} | {len(r["chat_calls"])} | {len(r["evidence"])} | {r["stop_reason"]} |')
        lines.extend(['', 'Reviewed coverage: '+', '.join(f'{r["mode"]} {r["grade"]["covered_criteria"]}/{r["grade"]["total_criteria"]}' for r in reviews if r['case_id']==case['id'])+'.'])
        for r in runs:
            lines.extend(['', f'### {r["mode"]}', '', f'Full passages, answer, prompt, usage, and provenance: [{r["mode"]} JSON]({r["mode"]}__{case["id"]}.json).', ''])
            if r['mode'] in {'initial','refined'}:
                lines.extend(['Action trace:', ''])
                for i,t in enumerate(r['trace'],1):
                    target = json.dumps(t.get('args',{}),ensure_ascii=False) if 'args' in t else t.get('query','') or t.get('filename','')
                    details = f'; file `{t["filename"]}`' if t.get('filename') else ''
                    lines.append(f'{i}. **{t["action"]}** — {target}{details}. {t.get("reasoning", t.get("reason", ""))} Added {len(t.get("added_ids",[]))} passages.' + (f' Error: {t["error"]}' if 'error' in t else ''))
                lines.append('')
            lines.extend(['Rubric assessment:', ''])
            for c in r['grade']['criteria']:
                lines.append(f'- Criterion {c["index"]}: complete={c["complete"]}, supported={c["supported"]}; evidence {c["source_ids"]}. {c["reason"]}')
            for claim in r['grade']['unsupported_claims']:
                lines.append(f'- Unsupported claim: {claim}')
            if r['mode']=='refined':
                lines.extend(['', 'Final answer:', '', r['answer'], '', 'Source map:', ''])
                for i,p in enumerate(r['evidence'],1):
                    lines.append(f'- Source {i}: `{p["source"]}`, page {p["page"]}.')
    (EVIDENCE/'evaluation_report.md').write_text('\n'.join(lines)+'\n')
    archived=[json.loads(p.read_text()) for folder in sorted(EVIDENCE.glob('*_pilot'))
              for p in folder.glob('*__*.json')]
    payload={'automated':summary,'reviewed':reviewed_summary,
             'additional_langgraph_development_runs':summarize(archived)}
    (EVIDENCE/'summary.json').write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(payload,indent=2))


if __name__=='__main__':
    main()
