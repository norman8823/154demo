"""Visible Investment Detail naming and generated-report labels preserve routes."""
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_data import load_companies


@pytest.mark.parametrize('company',load_companies(),ids=lambda c:c.id)
def test_investment_detail_keeps_company_deep_links_followups_and_standard_export(company):
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
    at.query_params.update({'page':'company','company':company.id,'finding':'10000'});at.run()
    assert not at.exception
    assert at.title[0].value=='Investment Detail'
    html='\n'.join(m.value for m in at.markdown)
    assert '<h2 class="investment-company-name">'+company.name+'</h2>' in html
    assert 'Portfolio / Investment Detail' in html
    assert at.button(key='nav_company').label=='Investment Detail'
    assert at.selectbox(key='gp_company_selector').value==company.id
    assert at.query_params['page']=='company' and at.query_params['finding']=='10000'
    assert len([m for m in at.markdown if m.value=='**Follow Up**'])==len(company.review.package['ai_insights'])
    assert not any(b.label in ('Follow Up','Read Full Analysis') for b in at.button)
    labels=[d.proto.label for d in at.get('download_button')]
    assert labels==['Download Excel']
    assert not any('Excel format' in s.label for s in at.selectbox)
    assert not at.get('file_uploader')
    assert at.session_state['export'][0].startswith(b'PK')


def test_generated_labels_are_contextual_and_original_downloads_remain_distinct():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60).run()
    assert not at.exception
    assert [d.proto.label for d in at.get('download_button')]==['Download Excel']
    at.button(key='nav_excel').click().run()
    assert not at.exception
    assert [d.proto.label for d in at.get('download_button')]==['Download Original']*3
    at.button(key='nav_foundation').click().run()
    assert not at.exception
    labels=[d.proto.label for d in at.get('download_button')]
    assert 'Download Excel' not in labels
