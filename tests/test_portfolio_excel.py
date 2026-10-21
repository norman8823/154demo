import io
import re
from dataclasses import replace
import pytest
from openpyxl import load_workbook
from portfolio_data import load_companies
from portfolio_excel import export_portfolio, SHEETS, COMPANY_SHEETS, OVERVIEW_HEAD
from portfolio_comparison import comparison
from portfolio_watchlist import watchlist


@pytest.fixture(scope='module')
def exported():
    companies=load_companies()
    return companies,load_workbook(io.BytesIO(export_portfolio(companies)))


def test_workbook_dashboard_matrix_company_sheets_and_output_reconcile(exported):
    companies,book=exported
    assert tuple(book.sheetnames[:len(SHEETS)])==SHEETS
    ws=book['Portfolio Overview']
    assert [ws.cell(6,c).value for c in (1,4,7,10)]==['3 / 3','3 / 3',17,6]
    assert len(ws._charts)==3
    assert all(c.y_axis.scaling.min==0 for c in ws._charts)
    for index,c in enumerate(companies):
        v=comparison(c);row=OVERVIEW_HEAD+1+index
        assert ws.cell(row,1).value==c.name
        assert ws.cell(row,2).value==v['period_label']
        assert ws.cell(row,3).value==v['revenue'].actual
        assert ws.cell(row,4).value==v['ebitda'].actual
        assert ws.cell(row,7).value==pytest.approx(v['ebitda'].variance_pct)
        assert ws.cell(row,8).value==pytest.approx(v['margin'].actual)
        matrix=book['Company Comparison'];col=3+index
        assert matrix.cell(5,col).value==c.name
        assert matrix.cell(6,col).value==v['period_label']
        assert matrix.cell(7,col).value==v['revenue'].actual
        assert matrix.cell(10,col).value==v['ebitda'].actual
        assert matrix.cell(5,col).hyperlink.location=="'"+COMPANY_SHEETS[c.id]+"'!A1"
        company=book[COMPANY_SHEETS[c.id]]
        assert company['B8'].value==v['revenue'].actual
        assert company['B9'].value==v['ebitda'].actual
        output=book['Reporting Output'];start=6+index*3
        assert output.cell(start,4).value==v['revenue'].actual
        assert output.cell(start+1,4).value==v['ebitda'].actual
        assert output.cell(start+2,4).value==pytest.approx(v['margin'].actual)
    assert 'No combined revenue' in ws['A9'].value
    for name in SHEETS:
        sheet=book[name]
        assert sheet.freeze_panes and sheet.auto_filter.ref and sheet.print_area
        assert not sheet.sheet_view.showGridLines


def test_original_findings_are_grouped_lossless_and_all_internal_links_resolve(exported):
    companies,book=exported
    ws=book['Investment Issues'];values={str(c.value) for row in ws for c in row if c.value is not None}
    assert [ws.cell(r,1).value for r in range(6,23)]==[companies[0].name]*5+[companies[1].name]*5+[companies[2].name]*7
    for item in watchlist(companies):
        for key in ('title','conclusion','text','evidence','financial_implication','assessment','action','management_question','classification'):
            assert item.finding[key] in values
        assert item.presentation['caveat'] in values
        assert all(q['quote'] in values for q in item.finding['source_quotes'])
    pairs={(row[0].value,row[1].value) for row in book['Source References'].iter_rows(min_row=6)}
    for item in watchlist(companies):assert {(item.company_name,sid) for sid in item.source_ids}<=pairs
    assert len([p for p in pairs if p[1]=='calc_2'])==3
    links=[]
    for sheet in book:
        for row in sheet:
            for cell in row:
                assert cell.data_type not in ('e','f')
                if cell.hyperlink:
                    assert cell.hyperlink.target is None
                    match=re.fullmatch(r"'((?:[^']|'')+)'!([A-Z]+[1-9]\d*)",cell.hyperlink.location)
                    assert match,cell.hyperlink.location
                    target,coordinate=match.groups();target=target.replace("''", "'")
                    assert target in book.sheetnames
                    assert book[target][coordinate].value is not None
                    links.append(cell.hyperlink.location)
    assert len(links)>200


def test_source_text_cannot_become_an_excel_formula():
    companies=list(load_companies());companies[0]=replace(companies[0],name='=HYPERLINK("https://invalid","test")')
    book=load_workbook(io.BytesIO(export_portfolio(companies)))
    assert book['Portfolio Overview'].cell(OVERVIEW_HEAD+1,1).data_type=='s'
