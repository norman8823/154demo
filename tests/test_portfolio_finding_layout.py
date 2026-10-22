"""Presentation preserves complete accepted prose, actions and source identities."""
from copy import deepcopy
from html import unescape
import pytest
from streamlit.testing.v1 import AppTest
from portfolio_data import load_companies
from portfolio_documents import evidence_locations


@pytest.mark.parametrize('index',[0,1,2])
def test_memo_rows_keep_original_content_and_each_source_action(index,monkeypatch):
    company=load_companies()[index];original=deepcopy(company.review.package)
    opened=[]
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
    assert len(at.columns)==3+2*len(findings)
    assert len([e for e in at.expander if e.label=='Follow Up'])==len(findings)
    assert not any(e.label=='Management follow-up' for e in at.expander)
    text=unescape('\n'.join(m.value for m in at.markdown))
    for finding in findings:
        for field in ('title','text','action','management_question'):assert finding[field] in text
        assert any(c.value==finding['priority'].title()+' priority' for c in at.caption)
        targets,_,_=evidence_locations(company,finding['fact_ids'])
        at.button(key='company_source_'+company.id+'_'+str(finding['id'])+'_view').click().run()
        assert not at.exception
        assert opened[-1]==(company.id,targets[0]['sheet'],targets[0]['cell'])
    assert company.review.package==original
