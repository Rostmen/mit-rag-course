"""Audit saved passages, worksheet structure, and prior-module byte preservation."""
from __future__ import annotations
import hashlib
import json
import re
import statistics
from pathlib import Path
import pymupdf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EVIDENCE = HERE/'evidence'


def prior_modules_audit():
    before_path = EVIDENCE/'prior_modules_before.json'
    if not before_path.exists():
        return {'verified': False, 'reason': 'Local pre-execution manifest is not available.'}
    before = json.loads(before_path.read_text())
    changed = [p for p,h in before.items() if not (ROOT/p).is_file()
               or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    current = {str(p.relative_to(ROOT)) for i in range(1,5)
               for p in (ROOT/f'module_{i}').rglob('*') if p.is_file()}
    added = sorted(current-set(before))
    return {'verified': not changed and not added, 'files_checked': len(before),
            'changed_or_removed': changed, 'added': added}


def summarize(records):
    summary = {}
    for mode in ['baseline','baseline_wide','initial','refined']:
        runs = [r for r in records if r['mode']==mode]
        if not runs:
            continue
        summary[mode] = {
            'cases': len(runs), 'passes': sum(r['grade']['passed'] for r in runs),
            'supported_criteria': sum(r['grade']['covered_criteria'] for r in runs),
            'total_criteria': sum(r['grade']['total_criteria'] for r in runs),
            'chat_calls': sum(len(r['chat_calls']) for r in runs),
            'chat_tokens': sum(r['chat_tokens'] for r in runs),
            'embedding_requests': sum(r['embedding_requests'] for r in runs),
            'median_seconds': round(statistics.median(r['seconds'] for r in runs),2),
            'mean_context_characters': round(statistics.mean(r['context_characters'] for r in runs)),
            'judge_tokens': sum(c['usage'].get('total_tokens',0) for r in runs for c in r['grade']['calls']),
            'tool_calls':sum(len([t for t in r['trace'] if 'seconds' in t]) for r in runs),
            'non_hybrid_tool_calls':sum(len([t for t in r['trace'] if 'seconds' in t and t['node']!='retrieve']) for r in runs),
        }
    return summary


def reviewed_records(records):
    """Keep original automated grades intact; return a separate reviewed view."""
    review = json.loads((EVIDENCE/'passage_review.json').read_text())
    by_key = {(r['mode'],r['case_id']): r for r in review['records']}
    output = []
    for record in records:
        grade = by_key[(record['mode'],record['case_id'])]
        assert [c['index'] for c in grade['criteria']]==list(range(1,grade['total_criteria']+1))
        assert grade['covered_criteria']==sum(c['complete'] and c['supported'] for c in grade['criteria'])
        assert grade['passed']==(grade['covered_criteria']==grade['total_criteria'] and not grade['unsupported_claims'])
        for c in grade['criteria']:
            assert all(1<=i<=len(record['evidence']) for i in c['source_ids'])
        output.append({**record,'grade':{**grade,'calls':record['grade']['calls']}})
    return output


def main():
    records = [json.loads(p.read_text()) for p in sorted(EVIDENCE.glob('*__*.json'))]
    cases = json.loads((HERE/'capstone_checkpoint_5_test_inputs.json').read_text())
    expected = {(m,c['id']) for m in ['baseline','baseline_wide','initial','refined'] for c in cases}
    assert {(r['mode'],r['case_id']) for r in records}==expected, 'Missing comparisons'
    assert all('grade' in r for r in records), 'Missing grades'
    original = json.loads((ROOT/'module_4/assignment/capstone_checkpoint_4_test_inputs.json').read_text())
    assert all(c==next(o for o in original if o['id']==c['id']) for c in cases)
    norm = lambda t: re.sub(r'\s+','',t)
    pdfs = {}; checked = 0; errors = []
    for record in records:
        assert record['citation_ids_valid'], record['case_id']
        assert len(record['evidence'])<=12
        for bracket in re.findall(r'\[([^\]]+)\]',record['answer']):
            if re.search(r'\bSource\b',bracket):
                assert all(1<=int(i)<=len(record['evidence']) for i in re.findall(r'\d+',bracket))
        for name,sha in record['manifest']['fingerprints'].items():
            path = HERE/name
            if name.endswith('.py'):
                path = EVIDENCE/'source_snapshots'/f'{sha}__{name}'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==sha, (record['mode'],name)
            if record['mode']=='refined':
                assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha, ('Final code differs from evaluation',name)
        for passage in record['evidence']:
            name = passage['source']
            if name not in pdfs:
                with pymupdf.open(ROOT/'module_1/assignment/ResearchPapers'/name) as pdf:
                    pdfs[name] = [(str(p.get_label()),norm(p.get_text())) for p in pdf]
            # Metadata may contain a printed page label instead of a PDF page number.
            matching = [text for index,(label,text) in enumerate(pdfs[name],1)
                        if passage['page'] in {label,str(index)}]
            if not any(norm(passage['text']) in text for text in matching):
                errors.append({'mode':record['mode'],'case':record['case_id'],
                               'source':name,'page':passage['page']})
            checked += 1
    assert not errors, errors
    text = (HERE/'capstone_checkpoint_5_worksheet_responses.md').read_text()
    assert text.count('\n## Step ')==5
    for title in ['Task description','Agent workflow: Describe how your system works',
                  'Evaluation results','Strengths observed','Weaknesses or challenges identified',
                  'Changes implemented','Justification','Impact on system performance',
                  'Comparison of initial and refined systems','What contributed most to successful task completion?',
                  'What limitations remain?','What improvements would you prioritize next?','Supporting Materials']:
        assert title in text, title
    assert not re.search(r'TODO|Pending evaluation|NotImplementedError',text)
    # Verify every original heading, instruction and table label remains in order.
    from zipfile import ZipFile
    from xml.etree import ElementTree as ET
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    xml=ET.fromstring(ZipFile(HERE/'Required_Capstone_Checkpoint_5_1_Worksheet.docx').read('word/document.xml'))
    originals=[''.join(t.text or '' for t in p.findall('.//w:t',ns))
               for p in xml.findall('.//w:body//w:p',ns)]
    cursor=0
    for original in originals:
        if not original or original=='Response:' or original.startswith('☐'):
            continue
        needle=original.strip()
        found=text.find(needle,cursor)
        assert found>=0, f'Missing or reordered worksheet text: {needle}'
        cursor=found+len(needle)
    preservation = prior_modules_audit()
    if (EVIDENCE/'prior_modules_before.json').exists():
        assert preservation['verified'], preservation
    tests=json.loads((EVIDENCE/'offline_tests.json').read_text())
    assert not tests['failures'] and not tests['errors']
    assert tests['passed']==len(tests['tests'])
    assert hashlib.sha256((HERE/'test_agent_rag.py').read_bytes()).hexdigest()==tests['test_file_sha256']
    behavior={}
    for r in records:
        if r['mode'] not in {'initial','refined'}:continue
        trace=r['trace']; tools=[t for t in trace if 'seconds' in t]
        if r['mode']=='initial':
            assert trace[0]['node']=='retrieve'
            assert trace[-1]['node']=='answer_outside_graph'
            assert any(t['node']=='analyze' for t in trace)
        else:
            assert trace[0]['node']=='plan' and trace[-1]['node']=='answer'
            for index,t in enumerate(trace):
                if 'seconds' not in t:continue
                assert trace[index-1]['node']=='plan' and trace[index-1]['action']==t['node']
                assert trace[index+1]['node']=='plan'
        behavior[f'{r["mode"]}__{r["case_id"]}']={
            'tool_calls':len(tools),'tool_names':[t['node'] for t in tools],
            'decisions_after_observation':sum(t['node'] in {'analyze','plan'} and (t.get('evidence_seen',0)>0 or t.get('after_observation',0)>0) for t in trace),
            'stop_reason':r['stop_reason']}
    assert any(v['tool_calls']>1 for k,v in behavior.items() if k.startswith('initial__'))
    assert any(any(n!='retrieve' for n in v['tool_names']) for k,v in behavior.items() if k.startswith('refined__'))
    report = {'comparisons': len(records), 'passages_verified_on_source_pages': checked,
              'offline_tests_passed':tests['passed'],
              'fixed_cases_unchanged': True, 'worksheet_steps':5,
              'source_fingerprints_verified': True,
              'langgraph_trace_audit':behavior,
              'prior_modules': preservation, 'errors': errors,
              'automated_summary': summarize(records),
              'reviewed_summary': summarize(reviewed_records(records))}
    (EVIDENCE/'final_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
