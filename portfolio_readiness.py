"""Workflow configuration and evidence views over unchanged v3 export contracts.

No extraction, mapping acceptance, new financial calculation or model invocation.
Known issues are an evidence-backed review queue, not an exhaustive quality audit.
"""
import json
import math
from pathlib import Path
from portfolio_foundation import foundation_records, METRICS
from portfolio_watchlist import evidence_for, source_closure

MODEL_PATH = Path(__file__).resolve().parent/'data_foundation/models/monthly_portfolio_operating_review.json'


def load_model(path=MODEL_PATH):
    model = json.loads(Path(path).read_text())
    if model['schema_version'] != 'gp-workflow-model-1.0' or model['selection_policy'] != 'existing_report_adapter_current_totals':
        raise ValueError('Unsupported GP workflow model or selection policy.')
    ids = [m['metric_id'] for m in model['metrics']]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError('GP metric identifiers must be nonempty and unique.')
    for m in model['metrics']:
        if m['metric_id'] not in {'financial.'+key for key in METRICS if key != 'other'}:
            raise ValueError('Unsupported GP metric: '+m['metric_id'])
        if not m['scenarios'] or len(m['scenarios']) != len(set(m['scenarios'])) or set(m['scenarios'])-{'actual','budget'}:
            raise ValueError('Unsupported or duplicate GP scenario.')
    return model


def workflow_mappings(companies, model, facts, lineage):
    origins = {r['fact_key']: r for r in lineage}
    targets = {m['metric_id']: m for m in model['metrics']}
    rows = []
    for fact in facts:
        target = targets.get(fact['metric_id'])
        if not target or fact['scenario'] not in target['scenarios'] or not fact['comparison_selected']:
            continue
        origin = origins[fact['fact_key']]
        row = dict(fact, target_label=target['label'], target_definition=target['definition'], lineage=origin)
        row['monthly_scope_matches'] = fact['period_grain'] == model['period_grain'] and fact['period'] == model['target_period']
        row['required_context_present'] = all(fact.get(f['field']) not in (None, '', 'unknown') for f in model['context_fields'] if f['required'])
        row['usable_mapping'] = (fact['mapping_accepted'] and fact['value'] is not None
                                 and fact['verification_status'] == 'source_observation_verified'
                                 and row['required_context_present'])
        row['status'] = ('Source checked · auto-mapped' if row['usable_mapping'] else 'Review required')
        if not row['monthly_scope_matches']:
            row['status'] = 'Period review required'
        rows.append(row)
    return sorted(rows, key=lambda r: (next(i for i,c in enumerate(companies) if c.id==r['company_id']),
                                      list(targets).index(r['metric_id']), r['scenario']))


def _observation_evidence(rows, lineage):
    index = {r['fact_key']: r for r in lineage}
    return [dict(source_id=r['source_fact_id'], reference=r['workbook_reference'],
                 source_label=r['source_label'], original_value=r['raw_source_value'],
                 standardized_value=r['value'], period=r['period'], scenario=r['scenario'],
                 mapping_status=r['mapping_status'], verification_status=r['verification_status'],
                 workbook=index[r['fact_key']]['canonical_workbook']) for r in rows]


def data_issues(companies, facts, lineage, mappings, model):
    issues=[]
    for company in companies:
        owned=[r for r in facts if r['company_id']==company.id]
        # Reuse accepted data-quality findings, including their full calculation
        # closure. Do not turn operating underperformance into a quality issue.
        for finding in company.review.package['ai_insights']:
            if finding.get('category') != 'data_quality':
                continue
            ids=source_closure(company.review,finding['fact_ids'])
            evidence=evidence_for(company.review,ids)
            if set(ids)-{e['Fact ID'] for e in evidence}:
                raise ValueError('Incomplete data-issue evidence: '+company.id)
            issues.append(dict(id=company.id+':finding:'+str(finding['id']),company_id=company.id,
                               company_name=company.name,title=finding['title'],status='Review Required',
                               problem=finding['conclusion'],why=finding['financial_implication'],
                               action=finding['action'],caveat=finding['assessment'],
                               evidence=list(evidence),finding_id=finding['id'],impact=finding.get('impact','')))
        unresolved=[r for r in owned if not r['mapping_accepted']]
        if unresolved:
            issues.append(dict(id=company.id+':unresolved',company_id=company.id,company_name=company.name,
                               title='Supporting observations lack accepted financial classifications',status='Review Required',
                               problem=f"{len(unresolved)} observation rows have unresolved mappings across {len({r['source_label'] for r in unresolved})} source labels. These rows are not distinct business issues.",
                               why='Current revenue and reported EBITDA remain mapped. Supporting metrics cannot safely inherit standardized financial meanings or be summed into those totals.',
                               action='Clarify ambiguous labels and reporting scope before using these observations in additional reporting or downstream models.',
                               caveat='Source checks do not establish semantic mapping acceptance. This grouped queue includes repeated periods and some blanks; human approval is not recorded.',
                               evidence=_observation_evidence(unresolved,lineage),finding_id=None))
        blanks=[r for r in owned if r['value'] is None]
        if blanks:
            issues.append(dict(id=company.id+':blanks',company_id=company.id,company_name=company.name,
                               title='Historical supporting comparators are blank',status='Review Required',
                               problem=f"{len(blanks)} retained source observations have no numeric value: "+', '.join(r['workbook_reference'] for r in blanks)+'.',
                               why='Historical supporting-metric comparisons are incomplete; blank values must not be treated as zero. Current revenue/EBITDA are unaffected.',
                               action='Request the missing comparator values or confirm that the measures were not available for the prior period.',
                               caveat='Some blank rows also appear in the unresolved-mapping queue; issue groups are not additive observation counts.',
                               evidence=_observation_evidence(blanks,lineage),finding_id=None))
        out_of_scope=[r for r in mappings if r['company_id']==company.id and not r['monthly_scope_matches']]
        if out_of_scope:
            issues.append(dict(id=company.id+':period',company_id=company.id,company_name=company.name,
                               title='Available headline reporting does not meet the monthly intake',status='Blocked',
                               problem='Current selected totals are '+', '.join(sorted({r['period']+' / '+r['period_grain'] for r in out_of_scope}))+f"; the model requests {model['target_period']} / {model['period_grain']}.",
                               why='Valid annual figures cannot satisfy a monthly actual/budget comparison. Broader annual and quarterly observations remain useful in the data package.',
                               action='Obtain the requested reporting frequency or explicitly configure a different workflow. Do not divide annual totals into invented monthly amounts.',
                               caveat='This is a workflow coverage gap, not an error in the annual source statements. No additional source extraction has been performed.',
                               evidence=_observation_evidence(out_of_scope,lineage),finding_id=None))
    return issues


def readiness(companies, model, rows, issues):
    required=[(c.id,m['metric_id'],s) for c in companies for m in model['metrics'] if m['required'] for s in m['scenarios']]
    def hits(predicate):
        return sum(any((r['company_id'],r['metric_id'],r['scenario'])==slot and predicate(r) for r in rows) for slot in required)
    total=len(required)
    mapped=hits(lambda r:r['usable_mapping'])
    in_scope=hits(lambda r:r['usable_mapping'] and r['monthly_scope_matches'])
    checked=hits(lambda r:r['verification_status']=='source_observation_verified')
    score,components=readiness_score(total,mapped,checked,in_scope,len(issues),model['scoring_policy'])
    return dict(score=score,score_status=f'{score}/100' if score is not None else 'Not Evaluated',
                components=components,required_slots=total,mapped_slots=mapped,
                verified_slots=checked,monthly_slots=in_scope,coverage=in_scope/total if total else None,
                issue_groups=len(issues),checks=[
                    dict(check='Required metric/scenario mappings at original frequency',passed=mapped,evaluated=total),
                    dict(check='Required metric/scenario source observations checked',passed=checked,evaluated=total),
                    dict(check='Mapped slots matching configured period and frequency',passed=in_scope,evaluated=total),
                ],reconciliation_status='Not Evaluated comprehensively; known source-backed exceptions remain open',
                limitation='Illustrative workflow assessment, not an externally certified automation-safety standard. '
                'The 3-point penalty per curated, non-exhaustive issue group is a demonstration policy, not a statistical risk estimate. '
                'Comprehensive cross-schedule reconciliation and semantic validation are not completed. '
                'This score does not certify unattended automation or company-wide AI maturity.')


def readiness_score(required,mapped,verified,monthly,issues,policy):
    """Explicit illustrative policy; nearest integer, with exact halves rounded up."""
    if any(not isinstance(n,int) or isinstance(n,bool) or n<0 for n in (required,mapped,verified,monthly,issues)):
        raise ValueError('Readiness counts must be nonnegative integers.')
    if any(n>required for n in (mapped,verified,monthly)):
        raise ValueError('Readiness coverage exceeds its required-slot denominator.')
    weights=[policy[k] for k in ('mapping_points','verification_points','period_points','issue_points')]
    if sum(weights)!=100 or any(w<0 for w in weights) or policy['penalty_per_issue_group']<0:
        raise ValueError('Readiness weights must be nonnegative and sum to100.')
    components=[]
    for label,points,count in zip(('Mapping completeness','Source verification','Reporting-period coverage'),weights,(mapped,verified,monthly)):
        components.append(dict(Component=label,Maximum=points,Input=f'{count} / {required} slots',
                               Calculation=f'{points} × {count} / {required}',Points=points*count/required if required else None))
    points=weights[3];penalty=policy['penalty_per_issue_group']
    components.append(dict(Component='Known data-issue adjustment',Maximum=points,Input=f'{issues} known issue groups',
                           Calculation=f'max(0, {points} − {penalty} × {issues})',Points=max(0,points-penalty*issues) if required else None))
    return (math.floor(math.fsum(c['Points'] for c in components)+.5) if required else None),components


def workflow_readiness(companies, model=None):
    model=load_model() if model is None else model
    facts,lineage,quality=foundation_records(companies)
    mappings=workflow_mappings(companies,model,facts,lineage)
    issues=data_issues(companies,facts,lineage,mappings,model)
    return dict(model=model,mappings=mappings,issues=issues,
                assessment=readiness(companies,model,mappings,issues),quality=quality,facts=facts,lineage=lineage)
