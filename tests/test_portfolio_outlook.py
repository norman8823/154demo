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

@pytest.mark.parametrize('index,moic,irr,equity,period,pct',[
 (0,'2.50x','21.77%','$27.00M','September 2026 monthly','23.8%'),
 (1,'0.71x','-9.54%','$15.00M','September 2026 monthly','27.7%'),
 (2,'1.68x','13.80%','$40.00M','FY2026 annual','10.9%')])
def test_editorial_words_figures_periods_and_approved_support(index,moic,irr,equity,period,pct):
 company=load_companies()[index];original=deepcopy(company.review)
 outlook=investment_outlook(company);text=' '.join(outlook.paragraphs)
 assert 80<=len(text.split())<=120
 for value in (moic,irr,equity,period,pct,'synthetic'):assert value in text
 ledger=investment_summary(investments_for([company]))
 assert f'{ledger["gross_moic"]:.2f}x'==moic
 assert f'{ledger["gross_irr"]:.2%}'==irr
 assert money(ledger['current_equity_value'])==equity
 assert f'{abs(comparison(company)["ebitda"].variance_pct):.1%}'==pct
 assert set(outlook.finding_ids)<={f['id'] for f in original.package['ai_insights']}
 assert outlook.ledger_sha256==investments_for([company])[0].ledger_sha256
 assert company.review==original
 if index==2:assert 'monthly' not in text
 else:assert 'does not establish' in text


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
   assert finding['action'] in text and finding['management_question'] in text
  assert len([e for e in at.expander if e.label=='Follow Up'])==len(company.review.package['ai_insights'])
