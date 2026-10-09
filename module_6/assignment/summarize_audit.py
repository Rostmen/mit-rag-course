"""Summarize recorded measurements without making API calls."""
import json
from pathlib import Path
from collections import defaultdict
HERE=Path(__file__).resolve().parent

def main():
 runs=json.loads((HERE/'evidence/runs.json').read_text()); rows=[];roles=defaultdict(lambda:{'calls':0,'input':0,'output':0})
 text=['# Audit transcript','', 'One observation per prompt; staged turns share history. All other scenarios start fresh.','']
 for r in runs:
  inp=sum(c['usage'].get('input_tokens',0) for c in r['calls']);out=sum(c['usage'].get('output_tokens',0) for c in r['calls'])
  row={'case':f"{r['scenario']}/{r['turn']}",'seconds':r['seconds'],'calls':len(r['calls']),'input_tokens':inp,'output_tokens':out,'total_tokens':inp+out,'stop_reason':r.get('stop_reason',r.get('error_type')),
       'tool_calls':sum('returned_ids' in t for t in r.get('trace',[]))}
  rows.append(row)
  for c in r['calls']:
   d=roles[c['role']];d['calls']+=1;d['input']+=c['usage'].get('input_tokens',0);d['output']+=c['usage'].get('output_tokens',0)
  text += [f"## {row['case']}",'','**Input:** '+r['input'],'','**Observed output:**','',r.get('answer',r.get('error_type','')),'',f"Measurements: {json.dumps(row)}",'']
 (HERE/'evidence/transcript.md').write_text('\n'.join(text))
 (HERE/'evidence/measurements.json').write_text(json.dumps({'runs':rows,'by_role':dict(roles)},indent=2))
 print(json.dumps({'runs':rows,'by_role':dict(roles)},indent=2))

if __name__=='__main__':main()
