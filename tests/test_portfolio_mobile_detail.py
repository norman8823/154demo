"""Phone details retain original assessments and incremental investment data."""
from copy import deepcopy
from html import unescape
import pytest
from streamlit.testing.v1 import AppTest
from portfolio_data import load_companies
from portfolio_mobile_detail import assessment_items
from portfolio_investments import investments_for,investment_summary


@pytest.mark.parametrize('index',[0,1,2])
def test_mobile_assessment_preserves_every_finding_and_deep_link(index):
    company=load_companies()[index];original=deepcopy(company.review.package)
    rows=assessment_items(company)
    assert rows[0]['id']==original['ai_briefing'][0]['finding_id']
    assert len(rows)==len(original['ai_insights'])
    assert {r['id'] for r in rows}=={r['id'] for r in original['ai_insights']}
    for requested in [f['id'] for f in rows]:
        selected=assessment_items(company,str(requested))
        assert selected[0]['id']==requested
        assert len({f['id'] for f in selected})==len(rows)
        for f in selected:assert f==next(r for r in original['ai_insights'] if r['id']==f['id'])
    for invalid in ('bad','999999',None):assert assessment_items(company,invalid)==rows
    assert company.review.package==original


@pytest.mark.parametrize('index',[0,1,2])
def test_phone_component_contains_context_and_prepared_actions_without_report_controls(index):
    at=AppTest.from_string(f'''
from portfolio_data import load_companies
from portfolio_mobile_detail import render_mobile_detail
render_mobile_detail(load_companies()[{index}])
''',default_timeout=60).run()
    assert not at.exception
    company=load_companies()[index];lead=assessment_items(company)[0]
    html=unescape('\n'.join(m.value for m in at.markdown))
    for text in (company.name,lead['conclusion'],lead['assessment'],lead['action'],lead['management_question']):assert text in html
    assert any(b.label=='← Back to portfolio' for b in at.button)
    assert not at.metric and not at.dataframe and not at.radio and not at.selectbox
    assert not at.get('download_button') and not at.get('file_uploader')
    assert 'mobile-investment-context' in html and 'v2-figures' not in html
    assert 'Gross MOIC' not in html and 'Gross IRR' not in html
    result=investment_summary(investments_for([company]))
    from portfolio_comparison import money
    for field in ('invested_capital','realized_proceeds','current_equity_value'):assert money(result[field]) in html
    assert len(at.expander)==len(company.review.package['ai_insights']) # all butlead +investmentcontext
