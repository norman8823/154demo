import json
import pytest
from streamlit.testing.v1 import AppTest
from engine import ROOT
from portfolio_data import load_companies
from portfolio_documents import original_document,source_books
from portfolio_sheet_grid import workbook_payload
from portfolio_source_device import MOBILE_MESSAGE


@pytest.mark.parametrize('desktop',[False,None])
@pytest.mark.parametrize('route',['excel','foundation','issues','source'])
def test_phone_or_unknown_viewport_never_mounts_worksheet(desktop,route):
 at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
 at.session_state['source_viewport']={'desktop':desktop}
 at.query_params.update({'page':route,'company':'summit','sheet':'Income Statement','cell':'D15'})
 at.run()
 assert not at.exception
 assert not any(b.label in ('Preview','View in Source') for b in at.button)
 assert not any(n.proto.component_name=='original_worksheet_grid' for n in at.get('bidi_component'))
 if route=='source':assert any(i.value==MOBILE_MESSAGE for i in at.info)


def test_workbook_tabs_are_original_and_citation_is_separate():
 for company in load_companies():
  book,cached=source_books(original_document(company))
  sheet,cell={'summit':('Income Statement','D15'),'tallis':('Practice P&L','G12'),'harrow':('P&L Summary','F13')}[company.id]
  data=workbook_payload(company,book,cached,sheet,cell)
  assert list(data['sheets'])==book.sheetnames
  assert data['citation']=={'sheet':sheet,'cell':cell}
  assert data['initial_sheet']==sheet
  for ws in book:
   assert data['sheets'][ws.title]['rows']==ws.max_row
   assert data['sheets'][ws.title]['columns']==ws.max_column
   assert data['sheets'][ws.title]['cells']['A1']['bar']==str(ws['A1'].value)
  assert json.loads(json.dumps(data))==data


def test_invalid_direct_citation_fails_safely():
 at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60)
 at.session_state['source_viewport']={'desktop':True}
 at.query_params.update({'page':'source','company':'summit','sheet':'No such worksheet','cell':'D15'})
 at.run()
 assert not at.exception
 assert any('not in the original workbook' in e.value for e in at.error)
 assert not any(n.proto.component_name=='original_worksheet_grid' for n in at.get('bidi_component'))
