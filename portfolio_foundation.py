"""Versioned CSV/JSON handoff over approved Review records; no raw extraction.

The independent consumer is copied as a standalone file, never imported here.
Illustrative sponsor investment assumptions are deliberately excluded.
"""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
from portfolio_comparison import metric_operand

SCHEMA='operating-data-1.0'
RESOURCE_ROOT=Path(__file__).resolve().parent/'data_foundation'
METRICS={
    'revenue':'Reported revenue category; source account labels and detail/total roles retain the original scope.',
    'cogs':'Reported direct costs / cost of services category; approved source sign normalization retained.',
    'gross_profit':'Reported gross profit category; not a standardized cross-company margin definition.',
    'operating_expenses':'Reported operating-expense category; original labels and scope retained.',
    'ebitda':'Reported EBITDA category; not a standardized adjusted EBITDA or cash-flow measure.',
    'depreciation':'Reported depreciation/amortization category; original source classification retained.',
    'interest':'Reported interest category; source period and sign normalization retained.',
    'tax':'Reported income-tax category; source period and sign normalization retained.',
    'net_income':'Reported net-income category; source period and entity scope retained.',
    'other':'Unmapped or other source observation; no standardized financial meaning or aggregation is established.'
}
FACT_FIELDS={
    'schema_version':'operating-data-1.0', 'fact_key':'company_id:approved_run:source_fact_id; version-qualified unique key',
    'company_id':'Stable registry ID', 'company_name':'Registry display name','entity_name':'Original normalized entity label',
    'metric_id':'Canonical retained category; unmapped.source_observation for other', 'metric_definition':'Definition from metric catalog',
    'source_label':'Original account label','context':'Original classification context','role':'Original detail, subtotal or total role',
    'period':'Original normalized reporting period','period_grain':'Original month, fiscal_quarter or annual grain','scenario':'Original actual or budget scenario',
    'value':'Retained normalized value, not an account aggregation','unit':'Retained observed source fact unit; unknown remains unknown',
    'currency':'Original currency label; $ is not promoted to USD','accounting_basis':'Original basis; unknown remains unknown',
    'source_scale':'Original scale multiplier; empty means unknown','sign_adjustment':'1 or -1 where retained normalization establishes it; empty otherwise',
    'raw_source_value':'Original source-unit numeric value; blank is not zero','normalization_status':'Scale/sign arithmetic status',
    'source_fact_id':'Original normalized financial alias, company/version-qualified by fact_key',
    'workbook_reference':'Original quoted worksheet/cell reference','verification_status':'Source observation verification; separate from mapping/interpretation approval',
    'mapping_accepted':'Original normalized acceptance flag, often automatic','mapping_status':'Original automatic or unresolved mapping status',
    'human_approval_status':'not_recorded; no explicit sign-off evidence in the exported contract',
    'comparison_selected':'Existing report adapter current-period revenue/EBITDA actual/budget operand; never sum duplicate presentations',
    'approved_run':'Approved Review identifier','workbook_sha256':'Canonical approved workbook version hash',
    'snapshot_sha256':'Approved prepared Review snapshot hash','provenance_class':'prepared_operating_observation; excludes illustrative investment assumptions'
}
LINEAGE_FIELDS={
    'fact_key':'Join to financial_facts.csv','company_id':'Registry ID','source_fact_id':'Normalized financial alias',
    'observed_source_fact_id':'Retained checked source fact ID; blank for blank source observations',
    'canonical_workbook':'Approved manifest-relative workbook path','source_file':'Original basename',
    'source_sheet':'Original worksheet','source_cell':'Original cell coordinate','source_reference':'Original quoted reference',
    'period_header_cell':'Retained period header coordinate','original_source_value_json':'JSON literal of retained original-unit numeric value',
    'original_formula_json':'JSON string literal of original formula, provenance only, never executed',
    'source_unit':'Retained source fact unit','source_scale':'Normalized source scale multiplier',
    'verification_status':'Same source-observation status as financial_facts.csv','approved_run':'Prepared Review version',
    'workbook_sha256':'Canonical workbook SHA-256','snapshot_sha256':'Prepared snapshot SHA-256'
}


def metric_id(category):
    if category not in METRICS:raise ValueError('Unsupported normalized category: '+str(category))
    return 'unmapped.source_observation' if category=='other' else 'financial.'+category


def _close(a,b):
    return isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool) and math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9)


def foundation_records(companies):
    facts=[];lineage=[];reports=[];seen=set()
    for company in companies:
        review=company.review
        source={(f.get('sheet'),f.get('cell')):f for f in review.package['facts']}
        selected=set()
        for category in ('revenue','ebitda'):
            for scenario in ('actual','budget'):
                support=metric_operand(company,category,scenario)
                if support is not None:selected.update(support[3])
        start=len(facts)
        for n in review.normalized:
            identity=company.id+':'+company.run+':'+n['fact_id']
            if identity in seen:raise ValueError('Duplicate versioned financial fact key.')
            seen.add(identity)
            observed=source.get((n['source_sheet'],n['cell']))
            if n['source_file']!=Path(company.provenance['workbook']).name or (observed and (observed.get('ref')!=n['source_ref'] or observed.get('file')!=n['source_file'])):
                raise ValueError('Normalized source identity differs from approved lineage: '+identity)
            raw=n['raw_value'];value=n['value'];scale=n['scale'];adjustment=None
            if raw is None and value is None:
                verified='blank_source_no_numeric_value';normalization='blank_no_numeric_value'
            else:
                if observed is None or not _close(raw,observed.get('source_value')) or n['raw']!=observed.get('raw'):
                    raise ValueError('A normalized observation does not match its retained verified source: '+identity)
                verified='source_observation_verified'
                if scale is None:
                    normalization='unknown_source_scale'
                elif _close(value,raw*scale):adjustment=1;normalization='retained_scale_sign_reconciled'
                elif _close(value,-raw*scale):adjustment=-1;normalization='retained_scale_sign_reconciled'
                else:raise ValueError('Retained normalization arithmetic does not reconcile: '+identity)
            selected_fact=n['fact_id'] in selected
            if selected_fact and (not n['accepted'] or n['role']!='total' or verified!='source_observation_verified'):
                raise ValueError('A comparison operand is not an accepted verified reported total.')
            row=dict(schema_version=SCHEMA,fact_key=identity,company_id=company.id,company_name=company.name,entity_name=n['company'],
                     metric_id=metric_id(n['category']),metric_definition=METRICS[n['category']],source_label=n['label'],context=n['context'],role=n['role'],
                     period=n['period'],period_grain=n['grain'],scenario=n['scenario'],value=value,unit=observed.get('unit','unknown') if observed else 'unknown',
                     currency=n['currency'],accounting_basis=n['basis'],source_scale=scale,sign_adjustment=adjustment,raw_source_value=raw,normalization_status=normalization,
                     source_fact_id=n['fact_id'],workbook_reference=n['source_ref'],verification_status=verified,mapping_accepted=n['accepted'],mapping_status=n['mapping_status'],
                     human_approval_status='not_recorded',comparison_selected=selected_fact,approved_run=company.run,workbook_sha256=company.provenance['workbook_sha256'],
                     snapshot_sha256=company.provenance['snapshot_sha256'],provenance_class='prepared_operating_observation')
            facts.append(row)
            original_formula=observed.get('raw') if observed and isinstance(observed.get('raw'),str) and observed['raw'].startswith('=') else None
            lineage.append(dict(fact_key=identity,company_id=company.id,source_fact_id=n['fact_id'],observed_source_fact_id=observed.get('id','') if observed else '',
                                canonical_workbook=company.provenance['workbook'],source_file=n['source_file'],source_sheet=n['source_sheet'],source_cell=n['cell'],source_reference=n['source_ref'],
                                period_header_cell=n['header_ref'],original_source_value_json=json.dumps(raw,allow_nan=False),original_formula_json=json.dumps(original_formula,allow_nan=False),
                                source_unit=row['unit'],source_scale=scale,verification_status=verified,approved_run=company.run,workbook_sha256=company.provenance['workbook_sha256'],snapshot_sha256=company.provenance['snapshot_sha256']))
        own=facts[start:]
        reports.append(dict(company_id=company.id,approved_run=company.run,normalized_observations=len(own),source_observations_verified=sum(f['verification_status']=='source_observation_verified' for f in own),
                            blank_observations=sum(f['verification_status']=='blank_source_no_numeric_value' for f in own),automatically_accepted_mappings=sum(f['mapping_accepted'] for f in own),
                            unresolved_mappings=sum(not f['mapping_accepted'] for f in own),human_approved_mappings=0,human_approval_status='not_recorded',
                            current_reported_comparison_facts=sum(f['comparison_selected'] for f in own),source_verification='Approved canonical source/snapshot hashes and retained source arithmetic verified by the existing prepared adapter.',
                            unknown_currency_label=any(f['currency'] not in ('USD','EUR','GBP') for f in own),unknown_basis=any(f['accounting_basis']=='unknown' for f in own),
                            original_warnings=review.warnings,original_analytical_limitations=company.provenance.get('quality_review',{}).get('remaining_material_gaps',[]),
                            workbook_sha256=company.provenance['workbook_sha256'],snapshot_sha256=company.provenance['snapshot_sha256']))
    quality=dict(schema_version=SCHEMA,provenance_class='prepared_operating_observation',companies=reports,
                 normalized_observations=len(facts),source_observations_verified=sum(r['source_observations_verified'] for r in reports),
                 blank_observations=sum(r['blank_observations'] for r in reports),unresolved_mappings=sum(r['unresolved_mappings'] for r in reports),human_approved_mappings=0,
                 new_model_calls=0,synthetic_investment_ledger_included=False,
                 approval_distinction='Prepared checkpoint approval and technical acceptance of AI finding references/arithmetic do not establish human mapping sign-off. All human approval fields are not_recorded.',
                 limitations=['Fictional demo operating companies and packages. No real-fund claims.','Source observation verification is not mapping, narrative or forecast approval.',
                              'Accepted automatic mappings and unresolved mappings are retained separately. Detail/subtotal/duplicate presentations must not be summed blindly.',
                              'Blank values are not zero; unknown basis/currency/scale are not inferred. No FX conversion or monthly/annual aggregation.',
                              'Canonical metric IDs name retained categories, not standardized GAAP consolidation definitions.',
                              'No persistent analyst-approved mapping reuse or fully automated subsequent reporting cycle has been implemented.',
                              'Illustrative investment assumptions and returns are excluded from this operating data package.'])
    return facts,lineage,quality


def _csv(rows,fields):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(fields),lineterminator='\n');writer.writeheader()
    for row in rows:writer.writerow({k:('true' if v else 'false') if isinstance(v,bool) else v for k,v in row.items()})
    return stream.getvalue().encode('utf8')


def _json(value):
    return (json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode('utf8')


def export_foundation(companies):
    if not companies:raise ValueError('At least one verified company is required.')
    facts,lineage,quality=foundation_records(companies)
    definitions=dict(schema_version=SCHEMA,fact_fields=FACT_FIELDS,lineage_fields=LINEAGE_FIELDS,
                     metrics={metric_id(k):v for k,v in METRICS.items()},period_grains=sorted({r['period_grain'] for r in facts}),
                     scenarios=sorted({r['scenario'] for r in facts}),value_convention='Retained normalized base units; original scale and expense-sign adjustments exposed. No new metric calculation or raw extraction.',
                     comparison_convention='Existing approved report financial-table operands for current-period revenue/EBITDA actual/budget. One selected reported total per metric/scenario/company scope; no duplicate sums.')
    files={'financial_facts.csv':_csv(facts,FACT_FIELDS),'metric_definitions.json':_json(definitions),'source_lineage.csv':_csv(lineage,LINEAGE_FIELDS),
           'example_consumer.py':(RESOURCE_ROOT/'example_consumer.py').read_bytes(),'README.md':(RESOURCE_ROOT/'README.md').read_bytes()}
    quality['content_sha256']={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
    files['quality_report.json']=_json(quality)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name in sorted(files):
            info=zipfile.ZipInfo(name,date_time=(2026,9,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,files[name])
    return stream.getvalue()
