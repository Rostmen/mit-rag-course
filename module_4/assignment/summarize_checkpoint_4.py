"""Recompute report tables from saved evaluation and annotation evidence."""
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

HERE=Path(__file__).resolve().parent

def summarize():
    from research_graph import build_graph
    annotations=json.loads((HERE/'annotatedResearchPapers.json').read_text())
    papers=annotations['papers']
    graph,canonical=build_graph(papers)
    stats={
        'documents':len(papers),'sampled_documents':sum(p['sampled'] for p in papers),
        'document_types':dict(Counter(p['document_type'] for p in papers)),
        'nodes':graph.number_of_nodes(),'edges':graph.number_of_edges(),
        'edge_types':dict(Counter(d['edge_type'] for _,_,d in graph.edges(data=True))),
        'unresolved_references':graph.graph['unresolved_references'],
        'validated_references':sum(len(p['references']) for p in papers),
        'rejected_reference_evidence':sum(p['rejected_reference_evidence'] for p in papers),
        'canonical_works':len(set(canonical.values())),
        'successful_annotation_tokens':sum(p['usage'].get('total_tokens',0) for p in papers),
        'successful_annotation_cost_usd':round(sum(p['usage'].get('cost',0) or 0 for p in papers),4),
    }
    rows=list(csv.DictReader((HERE/'checkpoint_4_comparison_results.csv').open()))
    details=json.loads((HERE/'checkpoint_4_comparison_results.json').read_text())
    modes={}
    for mode in ['hybrid','decomposition','graph','combined']:
        subset=[r for r in rows if r['mode']==mode]
        if not subset: continue
        supported=[r for r in subset if r['source_hit']!='n/a']
        refusals=[r for r in subset if r['answer_type']=='refusal']
        traces=[d for d in details if d['mode']==mode]
        cover=[]
        for r in supported:
            a,b=map(int,r['expected_source_coverage'].split('/')); cover.append(a/b)
        modes[mode]={
            'cases':len(subset),'source_hit':sum(r['source_hit']=='true' for r in supported),
            'all_sources':sum(r['all_expected_sources_hit']=='true' for r in supported),
            'mean_source_coverage':round(mean(cover),4),
            'canonical_all_sources':sum(r['canonical_all_sources_hit']=='true' for r in supported),
            'answer_passes':sum(r['judge_score']=='pass' for r in subset),
            'supported_answer_passes':sum(r['judge_score']=='pass' for r in supported),
            'refusal_passes':sum(r['judge_score']=='pass' for r in refusals),
            'median_retrieval_seconds':round(median(float(r['retrieval_seconds']) for r in subset),2),
            'mean_context_characters':round(mean(int(r['context_characters']) for r in subset)),
            'graph_context_chunks':sum(r['role']=='graph_context' for d in traces for r in d['results']),
            'planner_fallbacks':sum('fallback' in d['trace'].get('planner',{}) for d in traces),
            'recorded_chat_tokens':sum(d.get('answer_usage',{}).get('total_tokens',0)+d.get('judge_usage',{}).get('total_tokens',0)+d['trace'].get('planner',{}).get('usage',{}).get('total_tokens',0) for d in traces),
        }
    result={'annotations':stats,'modes':modes}
    (HERE/'checkpoint_4_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__': summarize()
