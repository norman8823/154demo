"""Company-only Excel presentation; approved numbers and findings remain inputs."""
import calendar
import re
import textwrap
from datetime import datetime
from types import SimpleNamespace

from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.pagebreak import Break

NAVY = '18364A'
MUTED = '60798A'
PALE = 'EFF5F7'
RULE = 'DCE5EA'


def company_identity(review):
    """Prepared-run registry identity; other approved reviews retain their name."""
    from portfolio_data import REGISTRY
    run = review.package.get('prepared_demo', {}).get('run')
    match = next((entry for entry in REGISTRY if entry[3] == run), None)
    if match:
        return SimpleNamespace(id=match[0], name=match[1], review=review)
    from engine import company_name
    return SimpleNamespace(id=None, name=company_name(review), review=review)


def company_filename(review, context):
    company = company_identity(review)
    period = context['period']
    for fmt in ('%B %Y', '%b %Y', '%Y-%m'):
        try:
            date = datetime.strptime(period, fmt)
        except ValueError:
            continue
        period = calendar.month_abbr[date.month] + str(date.year)
        break
    if re.fullmatch(r'\d{4}-FY', period):
        period = 'FY' + period[:4]
    clean = lambda text: re.sub(r'[^A-Za-z0-9]+', '_', text).strip('_')
    frequency = context['frequency'] if context['frequency'] in ('Monthly', 'Annual') else ''
    return clean(company.name) + '_' + clean(period) + '_' + frequency + 'Review.xlsx'


def executive_review(wb, review, lines, context):
    """Rebuild the generated summary and preserve its in-workbook references."""
    company = company_identity(review)
    index = wb.sheetnames.index('Executive Summary')
    wb.remove(wb['Executive Summary'])
    ws = wb.create_sheet('Executive Summary', index)
    for col in range(1, 13):
        ws.column_dimensions[get_column_letter(col)].width = 9
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 90
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = 'portrait'
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins = PageMargins(left=.35, right=.35, top=.35, bottom=.4, header=.15, footer=.2)
    ws.oddFooter.center.text = 'For Investment Team Review · Page &P of &N'
    ws.oddFooter.center.size = 8
    ws.oddFooter.center.color = MUTED

    def merged(row, value, *, start=1, end=12, size=11, bold=False,
               color=NAVY, fill=None, wrap=True, height=None):
        ws.merge_cells(start_row=row, start_column=start, end_row=row, end_column=end)
        c = ws.cell(row, start, value)
        if isinstance(value, str):
            c.data_type = 's'
        c.font = Font(name='Calibri', size=size, bold=bold, color=color)
        c.alignment = Alignment(horizontal='left', vertical='center', wrap_text=wrap)
        if fill:
            for col in range(start, end+1):
                ws.cell(row, col).fill = PatternFill('solid', fgColor=fill)
        if height:
            ws.row_dimensions[row].height = height
        return c

    merged(1, company.name, size=22, bold=True, wrap=False, height=34)
    merged(2, context['period_label'] + ' · ' + review.currency + ' base units', color=MUTED, height=22)
    merged(3, 'Investment Review', size=15, bold=True, height=27)
    merged(4, 'For Investment Team Review', size=10, color=MUTED, height=19)
    ws.row_dimensions[5].height = 9
    lookup = {line.key: line for line in lines}
    for start, key, label in ((1, 'revenue', 'Revenue'), (5, 'ebitda', 'Reported EBITDA'), (9, 'gm', 'Gross Margin')):
        line = lookup[key]
        # Each KPI occupies exactly four equal-width columns and six equal rows.
        fmt = '0.0%;(0.0%);"—"' if key == 'gm' else ('"' + review.currency + ' "#,##0;("' + review.currency + ' "#,##0);"—"')
        merged(6, label, start=start, end=start+3, bold=True, fill=PALE, wrap=False, height=23)
        for row, value, size in ((7, line.actual, 24), (9, line.budget, 13), (11, line.variance, 12)):
            c = merged(row, value if value is not None else 'N/A', start=start, end=start+3,
                       size=size, bold=row == 7, fill=PALE, wrap=False, height=35 if row == 7 else 24)
            c.number_format = ('0.0" pp";(0.0)" pp";"—"' if row == 11 and key == 'gm' else fmt)
            from portfolio_financial_reporting import internal_link
            target_row = {'revenue': 7, 'ebitda': 12, 'gm': 10}[key]
            internal_link(c, 'Financial Performance', {7: 'B', 9: 'C', 11: 'D'}[row] + str(target_row))
        for row, text in ((8, 'Budget'), (10, 'Actual − Budget' + (' · pp' if key == 'gm' else ''))):
            merged(row, text, start=start, end=start+3, size=9, color=MUTED, fill=PALE, wrap=False, height=18)
    ws.row_dimensions[12].height = 12
    row = 13

    def heading(title, *, new_page=False):
        nonlocal row
        if new_page:
            ws.row_breaks.append(Break(id=row-1))
        merged(row, title, size=13, bold=True, fill=PALE, wrap=False, height=28)
        row += 1

    def body(text, *, bold=False, color=NAVY):
        nonlocal row
        # Explicit row heights are necessary: Excel cannot autofit merged text.
        # Conservative line lengths allow Calc and Excel to show complete prose.
        count = sum(max(1, len(textwrap.wrap(part, width=112))) for part in str(text).splitlines())
        height = max(25, count*15+14)
        c = merged(row, text, bold=bold, color=color, height=min(409, height))
        if height > 409:
            raise ValueError('Executive narrative is too long for a single Excel row.')
        row += 1
        return c

    def spacer():
        nonlocal row
        ws.row_dimensions[row].height = 9
        row += 1

    profile = review.package.get('company_profile', {})
    heading('Business Overview')
    body(profile.get('description') or 'Company description not recorded in the approved review.')
    if profile.get('segments'):
        body('Reporting structure: ' + '; '.join(s['name'] + ' (' + s['kind'] + ')' for s in profile['segments']) + '.', color=MUTED)
    outlook = None
    if company.id:
        from portfolio_outlook import investment_outlook
        outlook = investment_outlook(company)
        body(outlook.paragraphs[0], color=MUTED)
    spacer()
    heading('Investment Outlook / Assessment')
    if outlook:
        body(outlook.headline, bold=True)
        for label, paragraph in zip(("What's Working", "What's Under Pressure", 'Operational Priorities'), outlook.paragraphs[1:]):
            body(label, bold=True)
            body(paragraph)
        body('Editorial context and proposed initiatives are illustrative. Operating observations come from the accepted review; sponsor investment returns are synthetic and gross of fees and carry.', color=MUTED)
    else:
        from executive import present, briefing
        body(briefing(present(review)))
    spacer()
    findings = review.package.get('ai_insights', [])
    if not findings:
        from executive import report_findings
        findings = report_findings(review)
    finding_rows = {wb['Findings'].cell(r, 1).value: r for r in range(6, wb['Findings'].max_row+1)}
    from portfolio_financial_reporting import internal_link
    heading('Priority Findings', new_page=True)
    for i, finding in enumerate(findings, 1):
        c = body(str(i) + '. ' + finding['title'] + ' · ' + str(finding.get('priority', finding.get('severity', 'Review'))).title(), bold=True)
        if finding['id'] in finding_rows:
            internal_link(c, 'Findings', 'A' + str(finding_rows[finding['id']]))
        body(finding.get('conclusion') or finding.get('summary') or finding['text'])
        spacer()
    body('Complete accepted analysis, financial implications and source links are retained on Findings. Financial Performance retains the reported income statement; Source Evidence and Statement Evidence retain the original provenance.', color=MUTED)
    spacer()
    heading('Management Follow-Up', new_page=True)
    for i, finding in enumerate(findings, 1):
        body(str(i) + '. ' + finding['title'], bold=True)
        body(finding.get('action') or 'No proposed action recorded.')
        question = finding.get('management_question') or finding.get('question')
        if question:
            body(question, color=MUTED)
        spacer()
    body('For demo only. All portfolio companies, investment data, and financial figures are synthetic. Any resemblance to real companies or investments is coincidental.', color=MUTED)
    ws.print_area = 'A1:L' + str(row-1)
    if 'Investment Summary' in wb:
        # Generated context is now above. Preserve any old context hyperlinks.
        for sheet in wb:
            for cells in sheet:
                for c in cells:
                    h = c.hyperlink
                    if h and ((h.location or '').startswith("'Investment Summary'!") or (h.target or '').startswith("#'Investment Summary'!")):
                        internal_link(c, 'Executive Summary', 'A13')
                    if c.data_type == 'f' and re.search(r"(?:'Investment Summary'|Investment Summary)!", c.value):
                        raise ValueError('Cannot remove a referenced Investment Summary formula safely.')
        wb.remove(wb['Investment Summary'])
    return ws
