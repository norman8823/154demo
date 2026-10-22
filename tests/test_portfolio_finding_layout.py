"""Compact finding summaries preserve original prose, actions and source targets."""
from copy import deepcopy
from html import unescape
import pytest
from streamlit.testing.v1 import AppTest
from portfolio_data import load_companies
from portfolio_documents import evidence_locations


def prose(at):return unescape('\n'.join(m.value for m in at.markdown))


@pytest.mark.parametrize('index',[0,1,2])
def test_compact_cards_defaults_extracts_original_analysis_actions_and_source(index,monkeypatch):
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
    findings=original['ai_insights']
    assert len(at.columns)==3 # Summary metrics only; no70/30 narrative columns.
    assert len([b for b in at.button if b.label=='Read Full Analysis'])==len(findings)
    assert len([b for b in at.button if b.label=='Follow Up'])==len(findings)
    assert len([b for b in at.button if b.label=='View in Source'])==len(findings)
    assert not any(e.label=='Follow Up' for e in at.expander)
    for index,finding in enumerate(findings):
        analysis='finding_analysis_'+company.id+'_'+str(finding['id'])
        followup='finding_followup_'+company.id+'_'+str(finding['id'])
        assert at.session_state[analysis] is (index==0)
        assert at.session_state[followup] is False
        assert finding['title'] in prose(at)
        assert (finding['text'] if index==0 else finding['conclusion']) in prose(at)
        if index:at.button(key='toggle_'+analysis).click().run()
        assert finding['text'] in prose(at)
        at.button(key='toggle_'+analysis).click().run()
        assert finding['conclusion'] in prose(at)
        at.button(key='toggle_'+followup).click().run()
        for field in ('action','management_question'):assert finding[field] in prose(at)
        targets,_,_=evidence_locations(company,finding['fact_ids'])
        at.button(key='company_source_'+company.id+'_'+str(finding['id'])+'_view').click().run()
        assert opened[-1]==(company.id,targets[0]['sheet'],targets[0]['cell'])
        assert at.session_state[followup] is True
    assert not at.exception
    assert company.review.package==original


def test_valid_finding_deep_link_opens_that_analysis_and_company_switch_resets():
    from engine import ROOT
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params.update({'page':'company','company':'tallis','finding':'10002'});at.run()
    assert not at.exception
    assert at.session_state['finding_analysis_tallis_10002'] is True
    assert at.session_state['finding_analysis_tallis_10000'] is False
    at.selectbox(key='gp_company_selector').set_value('harrow').run()
    assert not at.exception
    assert 'finding' not in at.query_params
    assert at.session_state['finding_analysis_harrow_10000'] is True
    assert at.session_state['finding_analysis_harrow_10002'] is False
