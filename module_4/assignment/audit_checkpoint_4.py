"""Verify completed evaluation artifacts against code, fixed cases and source PDFs."""
import csv
import hashlib
import json
from pathlib import Path
import re
import pymupdf

HERE=Path(__file__).resolve().parent
CORPUS=HERE.parents[1]/'module_1'/'assignment'/'ResearchPapers'

def main():
    manifest=json.loads((HERE/'checkpoint_4_comparison_results.manifest.json').read_text())
    for key,name in [('inputs_sha256','capstone_checkpoint_4_test_inputs.json'),
                     ('annotations_sha256','annotatedResearchPapers.json'),
                     ('solution_sha256','capstone_checkpoint_4_solution.py'),
                     ('graph_code_sha256','research_graph.py')]:
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==manifest[key],name
    original=HERE.parents[1]/'module_3'/'assignment'/'capstone_checkpoint_3_1_test_inputs.json'
    assert original.read_bytes()==(HERE/'capstone_checkpoint_4_test_inputs.json').read_bytes()
    rows=list(csv.DictReader((HERE/'checkpoint_4_comparison_results.csv').open()))
    details=json.loads((HERE/'checkpoint_4_comparison_results.json').read_text())
    cases=json.loads((HERE/'capstone_checkpoint_4_test_inputs.json').read_text())
    expected={(c['id'],m) for c in cases for m in ['hybrid','decomposition','graph','combined']}
    assert len(rows)==len(details)==80
    assert {(r['case_id'],r['mode']) for r in rows}==expected
    assert {(d['case_id'],d['mode']) for d in details}==expected
    assert all(r['judge_score'] in {'pass','failure'} for r in rows)
    assert all(len(d['results'])==3 for d in details)
    norm=lambda t:re.sub(r'\s+','',t)
    corpus_text={}; errors=[]; checked=0
    for d in details:
        for r in d['results']:
            name=r['source']
            if name not in corpus_text:
                with pymupdf.open(CORPUS/name) as pdf:
                    corpus_text[name]=norm('\n'.join(p.get_text() for p in pdf))
            if norm(r['text']) not in corpus_text[name]:
                errors.append({'case_id':d['case_id'],'mode':d['mode'],'source':name,'page':r['page']})
            checked+=1
    assert not errors,errors
    text=(HERE/'capstone_checkpoint_4_worksheet_responses.md').read_text()
    assert text.count('\n## Step ')==7
    assert text.count('\nResponse:\n')==16
    assert 'Pending implementation' not in text and 'Pending evaluation' not in text
    report={'comparisons':80,'passages_verified_in_source_pdfs':checked,
            'all_modes_use_three_chunks':True,'fixed_inputs_unchanged':True,
            'implementation_hashes_match':True,'worksheet_steps':7,'worksheet_responses':16,
            'errors':errors}
    (HERE/'checkpoint_4_final_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
