"""Offline regression replay of saved responses; never a fresh inference benchmark."""
import argparse
import copy
from dataclasses import asdict
import json
from pathlib import Path
import sys
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai_runtime import load_environment
from skill_engine import run
from report_cache import pack
from executive import present,report_findings
from reports import export_report


def main():
    p=argparse.ArgumentParser();p.add_argument('workbook',type=Path);p.add_argument('receipt',type=Path);p.add_argument('destination',type=Path)
    a=p.parse_args()
    if a.destination.exists():p.error('Use a new destination.')
    load_environment()
    def no_network(*args,**kwargs):raise AssertionError('Offline replay cannot use network.')
    urllib.request.urlopen=no_network
    saved=json.loads(a.receipt.read_text());responses=iter(saved['responses']);count=0
    def transport(request):
        nonlocal count
        count+=1
        try:response=copy.deepcopy(next(responses)['response'])
        except StopIteration:raise ValueError('Replay exhausted; current engine requested an additional response.')
        # Original token/cost records remain in the immutable source receipt.
        response['usage']={'input_tokens':0,'output_tokens':0}
        return response
    review=run({a.workbook.name:a.workbook.read_bytes()},request_fn=transport)
    state=review.package['skill_engine']
    state['offline_replay']={'original_receipt':str(a.receipt),'original_unattended_status':saved['skill_engine']['status'],'new_provider_calls':0,'actual_new_cost_usd':0,'responses_replayed':count}
    review.narrative_mode='OFFLINE REPLAY — '+state['status']+'; original unattended run failed'
    review.package['mode']=review.narrative_mode
    a.destination.mkdir(parents=True)
    (a.destination/'review-packed.json').write_text(json.dumps(pack(asdict(review))))
    (a.destination/'review.json').write_text(json.dumps(asdict(review),default=str,indent=2))
    (a.destination/'view.json').write_text(json.dumps(present(review),indent=2))
    (a.destination/'findings.json').write_text(json.dumps(report_findings(review),indent=2))
    exports=[]
    for name,template in [('standard',None),('custom',(Path(__file__).resolve().parents[1]/'sample_templates'/'Sample_Firm_Review_Template.xlsx').read_bytes())]:
        data,filename,warnings=export_report(review,template);(a.destination/(name+'.xlsx')).write_bytes(data)
        exports.append(dict(format=name,bytes=len(data),warnings=warnings))
    result=dict(mode='offline_replay',status=state['status'],reason=state['reason'],validation=state.get('validation'),coverage=state['coverage'],calculations=len(state['calculations']),exports=exports,**state['offline_replay'])
    (a.destination/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))


if __name__=='__main__':main()
