"""Presentation-only brand and source-linked catalog context contracts."""
from html import unescape
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_catalog import catalog_entries
from portfolio_data import load_companies
from portfolio_readiness import workflow_readiness
from portfolio_foundation_ui import catalog_linked_issues


@pytest.mark.parametrize('identity,expected',[
 ('financial.revenue',{'harrow:period'}),
 ('financial.ebitda',{'summit:finding:10004','harrow:period'}),
 ('unmapped.source_observation',{'tallis:unresolved','tallis:blanks'}),
 ('financial.net_income',set())])
def test_catalog_gaps_use_exact_original_company_and_source_reference(identity,expected):
 v=workflow_readiness(load_companies());entry=next(e for e in catalog_entries(v['facts'],v['lineage'],v['model']) if e['metric_id']==identity)
 linked=catalog_linked_issues(entry,v)
 assert {i['id'] for i in linked}==expected
 for issue in linked:
  own={r['workbook_reference'] for r in entry['rows'] if r['company_id']==issue['company_id']}
  assert any(e.get('Reference',e.get('reference')) in own for e in issue['evidence'])
  assert issue==next(i for i in v['issues'] if i['id']==issue['id'])


def test_application_branding_and_disclosure_are_presentation_only():
 at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60).run()
 assert not at.exception
 html='\n'.join(m.value for m in at.markdown)
 for text in ('NL Intelligence','Portfolio Reporting Copilot','Product Demo · Synthetic Data','For demo only. All portfolio companies, investment data, and financial figures are synthetic. Any resemblance to real companies or investments is coincidental.'):
  assert text in html
 for old in ('Concept developed for','Synthetic demonstration','Prepared results · 0 new model calls'):assert old not in html
 at.button(key='open_tallis').click().run()
 assert not at.exception
 captions='\n'.join(c.value for c in at.caption)
 for old in ('0 model calls','0 new model calls','no new model request','current inference'):assert old not in captions


def test_selected_catalog_metric_shows_definition_company_sources_gaps_and_usage():
 at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
 at.query_params['page']='foundation';at.run()
 assert not at.exception
 at.selectbox(key='foundation_metric').set_value('financial.ebitda').run()
 html=unescape('\n'.join(m.value for m in at.markdown))
 assert html.count('<div class="catalog-company-source">')==3
 for text in ('Reported EBITDA category','Income Statement','Practice P&L','P&L Summary','Workflow usage','Known linked gaps','Available headline reporting does not meet the monthly intake','Branch and consolidated EBITDA schedules do not reconcile'):
  assert text in html or any(text in c.value for c in at.caption)
 # The prior source-index CSV remains available, outside the primary catalog view.
 assert at.selectbox(key='foundation_sources_sort')
 at.selectbox(key='foundation_metric').set_value('unmapped.source_observation').run()
 assert not at.exception
 assert any('Not requested by the configured monthly workflow' in c.value for c in at.caption)
