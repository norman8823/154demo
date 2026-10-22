"""Company presentation contract: numbers, template ownership, and provenance."""
import io
from copy import copy
from pathlib import Path
import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from portfolio_data import load_companies
from portfolio_comparison import comparison
from portfolio_financial_reporting import export_company_report, statement
from portfolio_company_excel import company_filename
from portfolio_outlook import investment_outlook
from reports import export_report as frozen_export

@pytest.fixture(scope='module')
def companies():
    return load_companies()

@pytest.mark.parametrize('custom', [False, True])
def test_company_executive_numeric_kpis_context_and_complete_findings(companies, custom):
    template = Path('sample_templates/Sample_Firm_Review_Template.xlsx').read_bytes() if custom else None
    for company in companies:
        data, filename, _ = export_company_report(company.review, template)
        wb = load_workbook(io.BytesIO(data)); ws = wb['Executive Summary']
        expected = {'summit': 'Summit_Home_Services_Sep2026_MonthlyReview',
                    'tallis': 'Tallis_Brook_Accounting_Sep2026_MonthlyReview',
                    'harrow': 'Harrow_Ridge_Environmental_FY2026_AnnualReview'}[company.id]
        assert filename == expected + ('_CustomTemplate' if custom else '') + '.xlsx'
        assert ws['A1'].value == company.name
        assert ws['A2'].value.startswith(comparison(company)['period_label'])
        assert ws['A3'].value == 'Investment Review'
        assert ws['A4'].value == 'For Investment Team Review'
        assert len({ws.column_dimensions[chr(65+i)].width for i in range(12)}) == 1
        lines = {line.key: line for line in statement(company.review)}
        for col, key in (('A', 'revenue'), ('E', 'ebitda'), ('I', 'gm')):
            for row, attr in ((7, 'actual'), (9, 'budget'), (11, 'variance')):
                cell = ws[f'{col}{row}']
                assert cell.data_type == 'n'
                assert cell.value == pytest.approx(getattr(lines[key], attr))
                assert cell.hyperlink.location.startswith("'Financial Performance'!")
            assert ('%' in ws[f'{col}7'].number_format) if key == 'gm' else (company.review.currency in ws[f'{col}7'].number_format)
        assert 'pp' in ws['I11'].number_format
        texts = [cell.value for row in ws for cell in row if isinstance(cell.value, str)]
        for heading in ('Business Overview', 'Investment Outlook / Assessment', 'Priority Findings', 'Management Follow-Up'):
            cells = [cell for row in ws for cell in row if cell.value == heading]
            assert len(cells) == 1 and cells[0].font.bold and not cells[0].alignment.wrap_text
            assert any(cells[0].coordinate in area and area.size['columns'] == 12 for area in ws.merged_cells.ranges)
        assert company.review.package['company_profile']['description'] in texts
        outlook = investment_outlook(company)
        assert all(paragraph in texts for paragraph in outlook.paragraphs)
        for finding in company.review.package['ai_insights']:
            assert finding['conclusion'] in texts
            assert finding['action'] in texts
            assert finding['management_question'] in texts
        assert not any(text in ('money', 'ratio') for text in texts)
        assert all(dim.height <= 409 for dim in ws.row_dimensions.values() if dim.height)
        assert ('Investment Summary' in wb) == custom
        assert wb.active.title == ('Partner Review' if custom else 'Executive Summary')
        # Complete analytical narratives and technical source inventories unchanged.
        original = load_workbook(io.BytesIO(frozen_export(company.review, template)[0]))
        for name in ('Findings', 'Source Evidence', 'Extracted Detail', 'Data Quality', 'Exceptions', 'Analyst Execution'):
            assert list(wb[name].values) == list(original[name].values), name


def test_supplied_executive_and_investment_summary_keep_layout_formulas_and_mapping(companies):
    template = Workbook(); exec = template.active; exec.title = 'Executive Summary'
    exec['B2'] = '{{COMPANY_NAME}}'; exec['C5'] = '=2+3'
    exec.merge_cells('B2:G2'); exec.column_dimensions['B'].width = 33
    exec['B2'].font = Font(name='Arial', bold=True, color='112233')
    ctx = template.create_sheet('Investment Summary')
    ctx['A1'] = '{{REPORT_PERIOD}}'; ctx['B2'] = 7; ctx['D4'] = '=B2*2'
    ctx.merge_cells('A1:E1'); ctx.column_dimensions['B'].width = 29
    ctx.row_dimensions[4].height = 46
    ctx['D4'].alignment = Alignment(horizontal='right')
    template.create_sheet('Supplied Investment Summary')['A1'] = 'Existing sheet'
    template.create_sheet('Partner Inputs')['A3'] = "='Investment Summary'!D4+1"
    out = io.BytesIO(); template.save(out)
    data, _, _ = export_company_report(companies[1].review, out.getvalue())
    wb = load_workbook(io.BytesIO(data))
    assert wb['Executive Summary']['B2'].value == companies[1].review.company
    assert wb['Executive Summary']['B2']._style == exec['B2']._style
    assert wb['Executive Summary']['C5'].value == '=2+3'
    assert str(wb['Executive Summary'].merged_cells) == 'B2:G2'
    assert wb['Executive Summary'].column_dimensions['B'].width == 33
    ctx2 = wb['Investment Summary']
    assert ctx2.max_row == 4 and ctx2.max_column == 5
    assert ctx2['A1'].value == companies[1].review.report_period
    assert ctx2['D4'].value == '=B2*2' and copy(ctx2['D4'].alignment) == copy(ctx['D4'].alignment)
    assert ctx2.row_dimensions[4].height == 46 and ctx2.column_dimensions['B'].width == 29
    assert wb['Partner Inputs']['A3'].value == "='Investment Summary'!D4+1"
    assert wb['Supplied Investment Summary']['A1'].value == 'Existing sheet'
    assert 'Supplied Summary 1' not in wb


def test_filename_follows_approved_period_not_a_fixed_demo_date(companies):
    company = companies[0]
    context = dict(comparison(company), period='January 2027')
    assert company_filename(company.review, context) == 'Summit_Home_Services_Jan2027_MonthlyReview.xlsx'
    context.update(period='2028-FY', frequency='Annual')
    assert company_filename(company.review, context, custom=True) == 'Summit_Home_Services_FY2028_AnnualReview_CustomTemplate.xlsx'
