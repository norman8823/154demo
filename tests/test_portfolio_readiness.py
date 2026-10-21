"""Focused workflow contract, lineage, gap and UI regression checks."""
from copy import deepcopy
import json
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_data import load_companies
from portfolio_comparison import comparison
from portfolio_readiness import load_model, workflow_readiness, workflow_mappings, readiness


@pytest.fixture(scope='module')
def view():
    return workflow_readiness(load_companies())


def test_json_model_controls_targets_scenarios_and_monthly_coverage(view,tmp_path):
    model=deepcopy(view['model'])
    model['metrics']=model['metrics'][:1]
    model['metrics'][0]['label']='Configured revenue definition'
    model['metrics'][0]['scenarios']=['actual']
    path=tmp_path/'model.json';path.write_text(json.dumps(model))
    result=workflow_readiness(load_companies(),load_model(path))
    assert len(result['mappings'])==3
    assert {r['target_label'] for r in result['mappings']}=={'Configured revenue definition'}
    assert {r['metric_id'] for r in result['mappings']}=={'financial.revenue'}
    assert {r['scenario'] for r in result['mappings']}=={'actual'}
    assert result['assessment']['required_slots']==3
    assert result['assessment']['monthly_slots']==2
    model['target_period']='2026-10'
    assert workflow_readiness(load_companies(),model)['assessment']['monthly_slots']==0
    model['metrics'][0]['metric_id']='invented.metric'
    path.write_text(json.dumps(model))
    with pytest.raises(ValueError,match='Unsupported GP metric'):load_model(path)


def test_all_twelve_mappings_reconcile_to_existing_reports_and_original_lineage(view):
    companies=load_companies()
    assert len(view['mappings'])==12
    for company in companies:
        original={n['fact_id']:n for n in company.review.normalized}
        rows=[r for r in view['mappings'] if r['company_id']==company.id]
        assert len(rows)==4
        for row in rows:
            metric=comparison(company)[row['metric_id'].split('.')[1]]
            assert row['value']==getattr(metric,row['scenario'])
            n=original[row['source_fact_id']]
            assert row['entity_name']==n['company']
            for output,key in [('period','period'),('period_grain','grain'),('scenario','scenario'),('currency','currency'),('source_scale','scale'),('raw_source_value','raw_value')]:
                assert row[output]==n[key]
            assert row['lineage']['source_reference']==n['source_ref']
            assert row['lineage']['source_cell']==n['cell']
            assert row['lineage']['canonical_workbook']==company.provenance['workbook']
            assert row['value']==row['raw_source_value']*row['source_scale']*row['sign_adjustment']
            assert row['mapping_accepted'] is True
            assert row['verification_status']=='source_observation_verified'
            assert row['human_approval_status']=='not_recorded'
            assert row['monthly_scope_matches'] is (company.id!='harrow')
    assert {r['lineage']['source_sheet'] for r in view['mappings']}=={'Income Statement','Practice P&L','P&L Summary'}


def test_readiness_is_reproducible_illustrative_and_keeps_untested_checks_explicit(view):
    a=view['assessment']
    assert a==workflow_readiness(load_companies())['assessment']
    assert a['score']==76 and a['score_status']=='76/100'
    assert [c['Maximum'] for c in a['components']]==[25,25,35,15]
    assert [c['Points'] for c in a['components']]==pytest.approx([25,25,35*8/12,3])
    assert (a['mapped_slots'],a['verified_slots'],a['monthly_slots'],a['required_slots'])==(12,12,8,12)
    assert a['coverage']==pytest.approx(2/3)
    assert a['issue_groups']==4
    assert 'Not Evaluated' in a['reconciliation_status']
    assert view['quality']['normalized_observations']==1002
    assert view['quality']['unresolved_mappings']==204
    assert view['quality']['blank_observations']==6
    assert view['quality']['new_model_calls']==0


def test_checked_sources_do_not_override_unresolved_mapping_or_missing_context(view):
    from portfolio_foundation import foundation_records
    companies=load_companies()
    facts,lineage,_=foundation_records(companies)
    selected=next(r for r in facts if r['comparison_selected'])
    selected['mapping_accepted']=False
    selected['mapping_status']='Review required — test unresolved classification'
    rows=workflow_mappings(companies,view['model'],facts,lineage)
    changed=next(r for r in rows if r['fact_key']==selected['fact_key'])
    assert changed['verification_status']=='source_observation_verified'
    assert changed['status']=='Review required' and changed['usable_mapping'] is False
    a=readiness(companies,view['model'],rows,view['issues'])
    assert (a['verified_slots'],a['mapped_slots'],a['monthly_slots'])==(12,11,7)
    selected['mapping_accepted']=True
    selected['entity_name']='unknown'
    rows=workflow_mappings(companies,view['model'],facts,lineage)
    assert next(r for r in rows if r['fact_key']==selected['fact_key'])['required_context_present'] is False
    assert readiness(companies,view['model'],rows,view['issues'])['monthly_slots']==7


def test_data_issues_preserve_exact_calculations_unresolved_mappings_and_blank_evidence(view):
    issues={i['id']:i for i in view['issues']}
    summit=issues['summit:finding:10004']
    assert summit['status']=='Review Required'
    ev={r['Fact ID']:r for r in summit['evidence']}
    assert ev['calc_6']['Validated value']==ev['s3_L19']['Validated value']-ev['s2_D44']['Validated value']==47000
    assert ev['s3_L19']['Reference']=="'Branch Results'!L19"
    assert ev['s2_D44']['Reference']=="'Income Statement'!D44"
    assert ev['calc_22']['Validated value']==ev['s3_L9']['Validated value']-ev['s2_D25']['Validated value']==-47000
    assert ev['calc_48']['Validated value']==0
    original=next(f for f in load_companies()[0].review.package['ai_insights'] if f['id']==10004)
    assert summit['problem']==original['conclusion']
    assert summit['action']==original['action']
    unresolved=issues['tallis:unresolved']['evidence']
    assert len(unresolved)==204
    assert all(r['mapping_status'].startswith('Review required') for r in unresolved)
    blanks=issues['tallis:blanks']['evidence']
    assert len(blanks)==6
    assert {r['reference'] for r in blanks}=={f"'Dashboard'!C{n}" for n in range(10,16)}
    assert all(r['standardized_value'] is None and r['verification_status']=='blank_source_no_numeric_value' for r in blanks)
    assert issues['harrow:period']['status']=='Blocked'
    assert len(issues['harrow:period']['evidence'])==4
    assert all(r['period']=='2026-FY' for r in issues['harrow:period']['evidence'])
    assert not any('scale' in i['title'].lower() or 'below' in i['title'].lower() for i in view['issues'])


def test_mapping_filters_detail_state_and_original_finding_navigation():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params['page']='foundation';at.run()
    assert not at.exception
    at.selectbox(key='foundation_metric').set_value('financial.ebitda').run()
    at.selectbox(key='foundation_company').set_value('Harrow Ridge Environmental').run()
    at.selectbox(key='foundation_scenario').set_value('budget').run()
    assert not at.exception
    html='\n'.join(m.value for m in at.markdown)
    assert '$10,895,000' in html and 'Outside monthly workflow scope' in html
    assert "'P&L Summary'!G34" in at.selectbox(key='foundation_mapping').options[0]
    at.selectbox(key='foundation_company').set_value('Tallis Brook Accounting').run()
    assert not at.exception
    assert "'Practice P&L'!I41" in at.selectbox(key='foundation_mapping').options[0]
    assert any('Entity: TALLIS BROOK ACCOUNTING GROUP' in c.value for c in at.caption)
    at.selectbox(key='foundation_period').set_value('2026-FY').run()
    assert not at.exception
    assert any('No source observations match' in i.value for i in at.info)
    at.button(key='foundation_issue_summit:finding:10004').click().run()
    assert not at.exception
    assert at.query_params['company']=='summit' and at.query_params['finding']=='10004'
    assert at.title[0].value=='Summit Home Services'
