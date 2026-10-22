"""Original-cell presentation data; financial contracts stay in existing adapters."""
import json
import pytest
from portfolio_data import load_companies
from portfolio_documents import original_document,source_books
from portfolio_sheet_grid import worksheet_payload
from engine import InputError


@pytest.fixture(scope='module')
def companies():return load_companies()


@pytest.mark.parametrize('slug,sheet,cell,raw,standard',[
 ('summit','Income Statement','D15','3298','3298000'),
 ('tallis','Practice P&L','G12','3475418','3475418'),
 ('harrow','P&L Summary','F13','46650','46650000')])
def test_original_formula_cached_units_and_initial_citation(companies,slug,sheet,cell,raw,standard):
 company=next(c for c in companies if c.id==slug)
 doc=original_document(company);book,cached=source_books(doc)
 payload=worksheet_payload(company,book[sheet],cached[sheet],cell)
 record=payload['cells'][cell]
 assert payload['initial']==cell and payload['sheet']==sheet
 assert record['bar']==book[sheet][cell].value
 assert record['observed']==raw and record['standardized']==standard
 assert record['origin']=='Original workbook cached value'
 assert json.loads(json.dumps(payload))==payload
 assert payload['rows']==book[sheet].max_row and payload['columns']==book[sheet].max_column
 # All original raw strings/formulas are retained verbatim, not reinterpreted.
 for row in book[sheet]:
  for original in row:
   if original.data_type=='f':
    assert payload['cells'][original.coordinate]['bar']==original.value


def test_blank_text_boolean_and_no_recalculation(companies):
 company=companies[0];doc=original_document(company);book,cached=source_books(doc)
 sheet=book['Income Statement'];values=cached[sheet.title]
 sheet['B16']='<img src=x onerror=alert(1)>'
 sheet['C16']=True
 sheet['D16']='=UNSUPPORTED_EXTERNAL_FUNCTION()';values['D16']=None
 payload=worksheet_payload(company,sheet,values,'D16')
 assert payload['cells']['B16']['bar']=='<img src=x onerror=alert(1)>'
 assert payload['cells']['C16']['bar']=='TRUE'
 assert payload['cells']['D16']['bar']=='=UNSUPPORTED_EXTERNAL_FUNCTION()'
 assert payload['cells']['D16']['observed']=='' # No invented / recalculated result.
 assert 'A16' not in payload['cells']
 with pytest.raises(InputError):worksheet_payload(company,sheet,values,'XFD999999')
