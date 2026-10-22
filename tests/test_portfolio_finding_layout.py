"""All approved investment analysis and follow-up are visible without toggles."""
from copy import deepcopy
from html import unescape
import pytest
from streamlit.testing.v1 import AppTest
from portfolio_data import load_companies
from portfolio_documents import evidence_locations


@pytest.mark.parametrize('index',[0,1,2])
def test_original_analysis_actions_questions_visible_and_only_source_action(index,monkeypatch):
    company=load_companies()[index];original=deepcopy(company.review.package);opened=[]
    monkeypatch.setattr('portfolio_document_ui.open_source',lambda company,sheet,cell:opened.append((company.id,sheet,cell)))
    at=AppTest.from_string(f'''
import streamlit as st
from portfolio_company import render_company_summary
from portfolio_data import load_companies
st.session_state.source_desktop=True
render_company_summary(load_companies()[{index}])
''',default_timeout=60).run()
    assert not at.exception
    findings=original['ai_insights'];html=unescape('\n'.join(m.value for m in at.markdown))
    assert len(at.columns)==3 # Only the summary metrics, no narrative columns.
    assert [b.label for b in at.button]==['View in Source']*len(findings)
    assert not at.expander
    assert len([m for m in at.markdown if m.value=='**Follow Up**'])==len(findings)
    for f in findings:
        for key in ('title','text','action','management_question'):assert f[key] in html
        targets,_,_=evidence_locations(company,f['fact_ids'])
        at.button(key='company_source_'+company.id+'_'+str(f['id'])+'_view').click().run()
        assert not at.exception
        assert opened[-1]==(company.id,targets[0]['sheet'],targets[0]['cell'])
    assert company.review.package==original


def test_finding_deep_link_and_company_switch_keep_original_navigation():
    from engine import ROOT
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params.update({'page':'company','company':'tallis','finding':'10002'});at.run()
    assert not at.exception
    assert at.session_state['gp_selected_finding']==10002
    at.selectbox(key='gp_company_selector').set_value('harrow').run()
    assert not at.exception and at.query_params['company']=='harrow'
    assert 'finding' not in at.query_params
    assert not any(b.label in ('Read Full Analysis','Follow Up') for b in at.button)
