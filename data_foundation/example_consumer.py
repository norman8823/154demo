"""Standalone standard-library consumer. Run beside the six extracted files.

python example_consumer.py [extracted_package_directory]
No application modules, Excel workbooks, credentials, network or model are used.
"""
import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path


def comparison(package):
    package=Path(package)
    definitions=json.loads((package/'metric_definitions.json').read_text(encoding='utf8'))
    quality=json.loads((package/'quality_report.json').read_text(encoding='utf8'))
    if definitions['schema_version']!='operating-data-1.0':raise ValueError('Unsupported schema version.')
    for name,expected in quality['content_sha256'].items():
        if name not in {'financial_facts.csv','source_lineage.csv','metric_definitions.json','example_consumer.py','README.md'}:raise ValueError('Unexpected package file.')
        if hashlib.sha256((package/name).read_bytes()).hexdigest()!=expected:raise ValueError('Package content changed: '+name)
    with (package/'financial_facts.csv').open(encoding='utf8',newline='') as stream:
        facts=list(csv.DictReader(stream))
    groups={}
    for row in facts:
        if row['comparison_selected']!='true':continue
        if row['verification_status']!='source_observation_verified' or row['mapping_accepted']!='true' or row['role']!='total' or row['unit']!='money':
            raise ValueError('A selected comparison fact is not an accepted, source-verified reported total.')
        key=(row['company_id'],row['period'],row['period_grain'],row['currency'],row['accounting_basis'],row['workbook_sha256'])
        group=groups.setdefault(key,{})
        slot=(row['metric_id'],row['scenario'])
        if slot in group:raise ValueError('Duplicate selected totals; never sum duplicate source presentations.')
        group[slot]=row
    result=[]
    for (company,period,grain,currency,basis,workbook),group in sorted(groups.items()):
        def value(metric,scenario):
            row=group.get(('financial.'+metric,scenario))
            return Decimal(row['value']) if row and row['value']!='' else None
        revenue=value('revenue','actual');revenue_budget=value('revenue','budget')
        ebitda=value('ebitda','actual');ebitda_budget=value('ebitda','budget')
        if revenue is None or ebitda is None:raise ValueError('A company comparison lacks reported revenue or EBITDA.')
        ratio=lambda a,b:a/b if a is not None and b is not None and b>0 else None
        relative=ratio(ebitda,ebitda_budget)
        row={'company_id':company,'company_name':next(iter(group.values()))['company_name'],'period':period,'period_grain':grain,
             'currency':currency,'accounting_basis':basis,'revenue':revenue,'revenue_budget':revenue_budget,'reported_ebitda':ebitda,
             'ebitda_budget':ebitda_budget,'ebitda_margin':ratio(ebitda,revenue),'ebitda_variance':ebitda-ebitda_budget if ebitda_budget is not None else None,
             'ebitda_variance_pct':relative-1 if relative is not None else None,
             'source_fact_ids':sorted(r['source_fact_id'] for r in group.values()),'human_approval_status':'not_recorded'}
        result.append({k:float(v) if isinstance(v,Decimal) else v for k,v in row.items()})
    if not result:raise ValueError('No explicitly selected reported comparison facts.')
    return {'schema_version':definitions['schema_version'],'comparison':result,
            'scope':'Separate company periods; no monthly/annual totals, currency conversion, valuation or investment returns. Unknown accounting basis is retained; no human mapping approval is asserted.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',nargs='?',default=str(Path(__file__).resolve().parent))
    args=parser.parse_args()
    print(json.dumps(comparison(args.package),indent=2,sort_keys=True))
