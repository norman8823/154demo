"""Editorial assertions, source distinctions and hidden-route preservation."""
from copy import deepcopy
from html import unescape
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_data import load_companies
from portfolio_outlook import investment_outlook
from portfolio_comparison import comparison,money
from portfolio_investments import investments_for,investment_summary

@pytest.mark.parametrize('index,keywords',[
 (0,('HVAC','technician','installation','equipment procurement','maintenance agreement','collections')),
 (1,('tax','billable utilization','realization','partner compensation','client','work-in-progress','collection')),
 (2,('commercial','route density','fleet utilization','downtime','capital spending','cash conversion','renewal'))])
def test_business_sections_grounded_context_and_unchanged_financial_contracts(index,keywords):
 from portfolio_outlook import SECTIONS
 company=load_companies()[index];original=deepcopy(company.review)
 outlook=investment_outlook(company);text=' '.join(outlook.paragraphs)
 assert len(outlook.paragraphs)==4
 assert [s[0] for s in SECTIONS]==['Business Overview',"What's Working", "What's Under Pressure",'Operational Priorities']
 assert 150<=len(text.split())<=250
 for word in keywords:assert word.lower() in text.lower()
 assert 'illustrative' in outlook.paragraphs[0].lower()
 assert 'Illustrative business context'==SECTIONS[0][1]
 assert 'Proposed initiatives' in SECTIONS[3][1]
 assert 'Source-backed' in SECTIONS[2][1]
 ledger=investment_summary(investments_for([company]))
 assert ledger['gross_moic']==pytest.approx([2.5,0.7142857142857143,1.68][index])
 assert ledger['gross_irr']==pytest.approx([.2177,-.0954,.1380][index],abs=.00005)
 assert ledger['current_equity_value']==[27000000,15000000,40000000][index]
 # No duplicated monetary/return figures in the editorial prose.
 assert money(ledger['current_equity_value']) not in text
 assert f'{ledger["gross_moic"]:.2f}x' not in text
 assert set(outlook.finding_ids)<={f['id'] for f in original.package['ai_insights']}
 assert outlook.ledger_sha256==investments_for([company])[0].ledger_sha256
 assert company.review==original
 if index==2:assert 'FY2026 annual' in text and 'September monthly' not in text
 else:assert 'September monthly' in text and 'FY2026 annual' not in text


def test_hidden_navigation_and_legacy_issues_are_lossless():
 at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60).run()
 assert not at.exception
 assert not any(b.label=='Investment Issues' for b in at.button)
 assert not any(h.value=='Investment Issues' for h in at.subheader)
 assert not any(str(b.key).startswith('watch_') for b in at.button)
 for route in ('issues','watchlist'):
  at.query_params['page']=route;at.run()
  assert not at.exception
  assert at.title[0].value=='Investment Issues'
  assert len([b for b in at.button if str(b.key).startswith('watch_')])==17
  assert not any(b.key=='nav_watchlist' for b in at.button)


def test_switching_narrative_hierarchy_and_original_followups():
 at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60).run()
 at.button(key='open_summit').click().run()
 for company in load_companies():
  at.selectbox(key='gp_company_selector').set_value(company.id).run()
  assert not at.exception
  headings=[s.value for s in at.subheader]
  assert headings[:3]==['Investment Outlook','Investment Summary','Priority findings']
  text=unescape('\n'.join(m.value for m in at.markdown))
  assert investment_outlook(company).headline in text
  assert all(investment_outlook(other).headline not in text for other in load_companies() if other.id!=company.id)
  for finding in company.review.package['ai_insights']:
   assert finding['text'] in text and finding['action'] in text and finding['management_question'] in text
  assert not any(b.label in ('Follow Up','Read Full Analysis') for b in at.button)
