"""Final product policy, catalog semantics and scalable presentation contracts."""
from copy import deepcopy
import hashlib
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_data import load_companies
from portfolio_readiness import workflow_readiness,readiness_score,readiness
from portfolio_catalog import catalog_entries,catalog_detail,measurement_basis
from portfolio_foundation import export_foundation,METRICS,metric_id
from portfolio_holdings import selected_holdings
from portfolio_mobile import demo_url,qr_image


def test_score_sensitivity_denominators_caps_and_rounding():
    view=workflow_readiness(load_companies());p=view['model']['scoring_policy']
    score=lambda *a:readiness_score(*a,p)[0]
    assert score(12,12,12,8,4)==76
    for counts in [(12,11,12,8,4),(12,12,11,8,4),(12,12,12,7,4),(12,12,12,8,5)]:assert score(*counts)<76
    assert score(12,12,12,12,0)==100
    assert score(12,12,12,8,99)==73
    assert score(2,1,0,0,5)==13  # 12.5 rounds up, not bankers rounding.
    assert score(0,0,0,0,0) is None
    with pytest.raises(ValueError):score(12,13,12,8,4)
    with pytest.raises(ValueError):score(12,12,12,8,-1)
    rows=deepcopy(view['mappings']);rows[0]['usable_mapping']=False
    assert readiness(load_companies(),view['model'],rows,view['issues'])['score']<76


def test_catalog_covers_all_records_without_inventing_semantics_or_ownership():
    v=workflow_readiness(load_companies());entries=catalog_entries(v['facts'],v['lineage'],v['model'])
    assert len(entries)==10 and sum(e['observations'] for e in entries)==1002
    assert {e['metric_id'] for e in entries}=={metric_id(k) for k in METRICS}
    assert sum(e['accepted'] for e in entries)==798 and sum(e['verified'] for e in entries)==996
    for e in entries:
        assert e['owner']=='Not assigned' and e['refresh_cadence']=='Not configured' and e['approval_authority']=='Not recorded'
        assert e['definition']==e['rows'][0]['metric_definition']
        assert e['lineage_available']==e['observations']
        for r in e['rows']:
            detail=catalog_detail(r,v['lineage'],v['model'])
            assert detail['lineage']['source_reference']==r['workbook_reference']
            assert detail['value']==r['value'] and detail['entity_name']==r['entity_name']
    ltm=next(r for r in v['facts'] if r['source_label']=='LTM pro forma adjusted EBITDA')
    assert ltm['period_grain']=='month' and measurement_basis(ltm)=='LTM (explicit source label)'
    other=next(e for e in entries if e['metric_id']=='unmapped.source_observation')
    assert other['observations']==230 and other['accepted']==26
    assert 'no standardized financial meaning' in other['definition']
    assert any('Not established' in b for b in other['basis'])
    monthly=next(r for r in v['facts'] if r['comparison_selected'] and r['company_id']=='summit')
    assert measurement_basis(monthly)=='Monthly (retained grain)'
    assert hashlib.sha256(export_foundation(load_companies())).hexdigest()=='b2e5da282e8b950dbae6a4c48cd45d4694a0441ac8cdbe35bc2d26fe72811a7b'


def test_twelve_holdings_selection_defaults_limit_clear_replace_and_stable_ids():
    ids=[f'fixture-{n:02}' for n in range(1,13)]
    assert selected_holdings(ids)==ids[:2]
    assert selected_holdings(ids,[])==[]
    assert selected_holdings(ids,[ids[3],ids[3],'missing',ids[6],ids[8]])==[ids[3],ids[6]]
    at=AppTest.from_file(str(ROOT/'tests/fixtures/portfolio_holdings_app.py'),default_timeout=60).run()
    assert not at.exception
    assert len(at.checkbox)==13  # 12 rows plus sort-direction control.
    assert [b.key for b in at.button if b.key.startswith('open_')]==['open_fixture-01','open_fixture-02']
    assert at.checkbox(key='holding_select_fixture-03').disabled
    at.checkbox(key='holding_select_fixture-01').uncheck().run()
    at.checkbox(key='holding_select_fixture-03').check().run()
    assert [b.key for b in at.button if b.key.startswith('open_')]==['open_fixture-02','open_fixture-03']
    at.button(key='holdings_clear').click().run()
    assert not at.exception and not any(b.key.startswith('open_') for b in at.button)
    at.checkbox(key='holding_select_fixture-12').check().run()
    at.button(key='open_fixture-12').click().run()
    assert at.query_params['company']=='fixture-12'
    assert not at.exception


@pytest.mark.parametrize('value',['','http://localhost:8502','https://127.0.0.1','https://[::1]','http://0.0.0.0','https://user:secret@example.com','http://example.com','javascript:alert(1)','https://localhost.','https://[::]','https://127.1','https://2130706433','https://0x7f000001'])
def test_mobile_link_rejects_unusable_or_credentialled_addresses(value):assert demo_url(value) is None


@pytest.mark.parametrize('url',['https://demo.example.com/?page=foundation','http://192.168.1.24:8502/?page=overview','http://normans-mac.local:8502/?page=foundation'])
def test_opt_in_url_is_exact_and_both_qr_sizes_encode_it(url,monkeypatch):
    import qrcode
    original=qrcode.QRCode.add_data;seen=[]
    def record(self,data,*a,**kw):seen.append(data);return original(self,data,*a,**kw)
    monkeypatch.setattr(qrcode.QRCode,'add_data',record)
    qr_image.clear()
    assert demo_url(url)==url
    for size in (140,280):assert qr_image(url,size).startswith(b'\x89PNG')
    assert seen==[url,url]


def test_branding_and_contextual_company_selection():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60).run()
    assert not at.exception
    html='\n'.join(m.value for m in at.markdown)
    for text in ['154 Partners','Portfolio Reporting Copilot','Concept developed for 154 Partners by NL Intelligence']:assert text in html
    assert not any(s.key=='gp_sidebar_company' for s in at.selectbox)
    assert not any(e.label=='Illustrative investment values and valuation context' for e in at.expander)
    at.button(key='nav_company').click().run()
    assert not at.exception and len(at.selectbox(key='gp_company_selector').options)==3
