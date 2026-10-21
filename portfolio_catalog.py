"""Metric-centered presentation of retained observations, not a new mapping layer."""
import re
from portfolio_foundation import METRICS, metric_id

LABELS={key:key.replace('_',' ').title() for key in METRICS}
LABELS.update(ebitda='Reported EBITDA',cogs='Cost of services / direct costs',other='Unmapped / other source observations')
GRAINS={'month':'Monthly','fiscal_quarter':'Fiscal quarter','annual':'Annual / FY'}


def measurement_basis(row):
    """Source labels can qualify the retained grain; never infer annualization."""
    text=row['source_label']+' '+row['context']
    for token in ('LTM','TTM','YTD'):
        if re.search(r'\b'+token+r'\b',text,re.I):return token+' (explicit source label)'
    if 'run-rate' in text.lower() or 'run rate' in text.lower():return 'Run-rate (explicit source label; '+row['source_label']+')'
    if row['metric_id']=='unmapped.source_observation':return 'Not established; retained '+row['period_grain']+' grain'
    return GRAINS.get(row['period_grain'],row['period_grain'])+' (retained grain)'


def catalog_entries(facts,lineage,model):
    origins={r['fact_key']:r for r in lineage}
    targets={m['metric_id']:m for m in model['metrics']}
    result=[]
    for category,definition in METRICS.items():
        identity=metric_id(category);rows=[r for r in facts if r['metric_id']==identity]
        if not rows:continue
        result.append(dict(metric_id=identity,label=targets.get(identity,{}).get('label',LABELS[category]),
            definition=definition,workflow_definition=targets.get(identity,{}).get('definition'),
            category='Unclassified source observations' if category=='other' else 'Retained financial category',
            observations=len(rows),accepted=sum(r['mapping_accepted'] for r in rows),
            verified=sum(r['verification_status']=='source_observation_verified' for r in rows),
            units=sorted({r['unit'] for r in rows}),currencies=sorted({r['currency'] for r in rows}),
            scales=sorted({str(r['source_scale']) for r in rows}),basis=sorted({measurement_basis(r) for r in rows}),
            periods={g:sorted({r['period'] for r in rows if r['period_grain']==g}) for g in sorted({r['period_grain'] for r in rows})},
            packages=sorted({origins[r['fact_key']]['source_file'] for r in rows}),
            companies=sorted({r['company_name'] for r in rows}),entities=sorted({r['entity_name'] for r in rows}),
            owner='Not assigned',refresh_cadence='Not configured',approval_authority='Not recorded',
            lineage_available=sum(r['fact_key'] in origins for r in rows),rows=rows))
    return result


def catalog_detail(row,lineage,model):
    """Use the same three-column component for all categories, retaining statuses."""
    targets={m['metric_id']:m for m in model['metrics']}
    category=next(k for k in METRICS if metric_id(k)==row['metric_id'])
    target=targets.get(row['metric_id'],{})
    return dict(row,lineage=next(r for r in lineage if r['fact_key']==row['fact_key']),
                target_label=target.get('label',LABELS[category]),target_definition=target.get('definition',row['metric_definition']),
                monthly_scope_matches=row['period']==model['target_period'] and row['period_grain']==model['period_grain'],
                measurement_basis=measurement_basis(row))
