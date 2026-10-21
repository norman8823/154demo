"""Unattended application-path benchmark. Never reads comparator/answer-key files."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai_runtime import load_environment,configuration
from engine import analyze
from executive import present,report_findings
from reports import export_report
from report_cache import pack,cache_key,ReportCache,successful


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('workbook',type=Path);parser.add_argument('destination',type=Path)
    parser.add_argument('--authorize',action='store_true',help='Explicitly authorize external model processing of this workbook.')
    args=parser.parse_args()
    if args.destination.exists():parser.error('Use a new destination; previous runs are immutable.')
    if not args.authorize:parser.error('--authorize is required for paid execution.')
    load_environment();cfg=configuration()
    data=args.workbook.read_bytes();files={args.workbook.name:data}
    args.destination.mkdir(parents=True,mode=0o700)
    (args.destination/'inputs.json').write_text(json.dumps(dict(workbook=args.workbook.name,sha256=hashlib.sha256(data).hexdigest(),model=cfg['model'],authorized_limit=cfg['limit'],engine='skill',comparator_input=False),indent=2))
    start=time.monotonic()
    review=analyze(files,ai_authorized=True,engine_name='skill')
    elapsed=time.monotonic()-start
    (args.destination/'review.json').write_text(json.dumps(asdict(review),default=str,indent=2))
    (args.destination/'review-packed.json').write_text(json.dumps(pack(asdict(review))))
    (args.destination/'view.json').write_text(json.dumps(present(review),indent=2))
    (args.destination/'findings.json').write_text(json.dumps(report_findings(review),indent=2))
    exports=[]
    for name,template in [('standard',None),('custom',(Path(__file__).resolve().parents[1]/'sample_templates'/'Sample_Firm_Review_Template.xlsx').read_bytes())]:
        output,filename,warnings=export_report(review,template)
        (args.destination/(name+'.xlsx')).write_bytes(output)
        exports.append(dict(format=name,bytes=len(output),filename=filename,warnings=warnings))
    key=cache_key(files,ai_authorized=True,engine_name='skill')
    cached=ReportCache().save(key,review)
    state=review.package['skill_engine']
    result=dict(status=state['status'],reason=state['reason'],elapsed_seconds=elapsed,measurement=state['measurement'],
        rounds=state['rounds'],tool_calls=state['tool_calls'],inference=review.package['inference'],validation=state.get('validation'),
        cache_saved=cached,cache_key=key,export_results=exports,completed=successful(review))
    (args.destination/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:result[k] for k in ('status','reason','elapsed_seconds','measurement','rounds','tool_calls','cache_saved','completed')},indent=2))


if __name__=='__main__':main()
