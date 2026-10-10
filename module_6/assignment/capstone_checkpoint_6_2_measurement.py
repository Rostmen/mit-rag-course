"""Lab 6.2 measurement-only configurations around the unchanged Module 5 graph."""
from pathlib import Path
from datetime import datetime, timezone
import sys, json, time, hashlib, statistics
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'module_5/assignment'))
import capstone_checkpoint_5_1_agent_rag_starter as agent
import retrieval_backend as backend

CURRENT='openai/gpt-5.4-mini'
CHEAP='openai/gpt-4o-mini'
CONFIGS=[('current',CURRENT,CURRENT),('cheap',CHEAP,CHEAP),('mixed',CURRENT,CHEAP)]
QUESTIONS=[
 {'id':'simple','question':'What is CVC4SY and how does it search for synthesis solutions?'},
 {'id':'comparison','question':'Compare CVC4SY and adaptive concretization as search strategies for syntax-guided synthesis. What search space does each address, what mechanism does each use, and what tradeoff or benefit is each trying to achieve?'},
]
# OpenRouter standard advertised rates verified 2026-10-09, USD/million tokens.
PRICES={CURRENT:{'input':0.75,'output':4.50,'cached':0.075},CHEAP:{'input':0.15,'output':0.60,'cached':0.075}}

class RoleMeter(agent.Meter):
    """Reuse existing invocation/validation unchanged; select model by call role."""
    def __init__(self,plan,answer):
        super().__init__(plan)
        self.plan,self.answer=plan,answer
    def _call(self,method,role,*args):
        self.llm=self.answer if role=='answer' else self.plan
        start=len(self.calls)
        try:return getattr(super(),method)(role,*args)
        finally:
            for call in self.calls[start:]:call['model']=self.llm.model_name
    def invoke(self,role,*args):return self._call('invoke',role,*args)
    def structured(self,role,*args):return self._call('structured',role,*args)


def tally(calls):
    buckets={}
    for c in calls:
        key=c['model'];b=buckets.setdefault(key,{'calls':0,'input':0,'output':0,'cached':0,'missing_usage':0,'missing_cache':0})
        b['calls']+=1;u=c.get('usage') or {}
        if 'input_tokens' not in u or 'output_tokens' not in u:
            b['missing_usage']+=1;continue
        b['input']+=u['input_tokens'];b['output']+=u['output_tokens']
        details=u.get('input_token_details') or {}
        if 'cache_read' not in details:b['missing_cache']+=1
        else:b['cached']+=details['cache_read']
    for model,b in buckets.items():
        price=PRICES[model]  # Unknown prices must not silently count as zero.
        b['full_input_rate_usd']=None if b['missing_usage'] else (b['input']*price['input']+b['output']*price['output'])/1e6
        b['cache_adjusted_usd']=None if b['missing_usage'] or b['missing_cache'] else ((b['input']-b['cached'])*price['input']+b['cached']*price['cached']+b['output']*price['output'])/1e6
    return buckets


def summarize(runs):
    result={}
    for label,_,_ in CONFIGS:
        rs=[r for r in runs if r['configuration']==label]
        calls=[c for r in rs for c in r['calls']]
        by_model=tally(calls)
        result[label]={'completed':sum('answer' in r for r in rs),'attempted':len(rs),
          'median_seconds':statistics.median(r['seconds'] for r in rs) if rs else None,
          'by_model':by_model,'by_role':{role:tally([c for c in calls if c['role']==role]) for role in sorted({c['role'] for c in calls})},
          'full_input_rate_usd':sum(b['full_input_rate_usd'] for b in by_model.values()) if calls and all(b['full_input_rate_usd'] is not None for b in by_model.values()) else None,
          'cache_adjusted_usd':sum(b['cache_adjusted_usd'] for b in by_model.values()) if calls and all(b['cache_adjusted_usd'] is not None for b in by_model.values()) else None}
    return result


def main():
    out=HERE/'evidence/cost_6_2';out.mkdir(parents=True,exist_ok=True)
    if (out/'runs.json').exists():raise SystemExit('Preserve existing measurement evidence before rerunning.')
    sources=list((ROOT/'module_5/assignment').glob('*.py'))
    fingerprint=lambda:{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    before=fingerprint()
    target=HERE/'.rag_indexes/research_papers'
    if not (target/'.index_ready').exists():raise RuntimeError('Run Module 6 audit setup first; existing isolated index required.')
    backend.VECTOR_INDEX_DIR=target;backend.VECTOR_READY_FILE=target/'.index_ready'
    start=time.perf_counter();toolkit=agent.ResearchTools();initialization=time.perf_counter()-start
    clients={m:backend.ChatOpenAI(model=m,temperature=backend.TEMPERATURE,api_key=backend.require_api_key(),base_url=backend.OPENROUTER_BASE_URL,timeout=90,max_retries=2) for m in [CURRENT,CHEAP]}
    runs=[]
    (out/'pricing.json').write_text(json.dumps({'checked_on':'2026-10-09','usd_per_million_tokens':PRICES,'sources':['https://openrouter.ai/'+m for m in PRICES],
       'formula':'Lab estimate: (input * input_rate + output * output_rate) / 1e6. Cache-aware estimate: ((input - cache_read) * input_rate + cache_read * cache_rate + output * output_rate) / 1e6.',
       'scope':'Estimated chat cost, not invoice. Excludes embeddings, fees and unreported retry usage. Standard advertised rates; routing may change billing.'},indent=2))
    (out/'test_cases.json').write_text(json.dumps(QUESTIONS,indent=2))
    for label,plan,answer in CONFIGS:
        for case in QUESTIONS:
            # New agent/call list: no shared dialogue or token counter between runs.
            session=agent.ToolUsingResearchAgent(toolkit,clients[plan]);session.meter=RoleMeter(clients[plan],clients[answer])
            start=time.perf_counter();r={'configuration':label,'plan_model':plan,'answer_model':answer,**case}
            try:
                state=session.query(case['question'])
                r.update(answer=state['answer'],stop_reason=state['stop_reason'],trace=state['trace'],requirements=state['requirements'],evidence=[agent.evidence_record(v) for v in state['evidence'].values()])
            except Exception as exc:r['error_type']=type(exc).__name__
            r.update(seconds=round(time.perf_counter()-start,3),calls=session.meter.calls)
            r['embedding_requests']=sum(t.get('node')=='retrieve' and 'returned_ids' in t for t in r.get('trace',[]))
            runs.append(r)
            (out/'runs.json').write_text(json.dumps(runs,indent=2))
            (out/'summary.json').write_text(json.dumps(summarize(runs),indent=2))
            print(label,case['id'],r['seconds'],len(r['calls']),r.get('stop_reason',r.get('error_type')),flush=True)
    (out/'manifest.json').write_text(json.dumps({'timestamp_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':before,'module_5_sources_unchanged':before==fingerprint(),'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'initialization_seconds':initialization,'temperature':backend.TEMPERATURE,
      'role_mapping':'Requirements, planning and coverage use plan_model. Final answer uses answer_model.',
      'scope':'Two fixed questions, three configurations, one pass. Existing prompts, tool definitions, graph and limits unchanged. Model routing only in this audit harness; no adopted capstone improvement.',
      'limitations':'Order is current, cheap, mixed; provider caches are uncontrolled. Latency excludes initialization. Usage counts successful responses only, not unreported retries. Embedding requests incur separate cost not included here. No free or pro tier, no judge calls.'},indent=2))

if __name__=='__main__':main()
