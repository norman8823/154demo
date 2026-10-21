"""Four-sheet GP workbook over exactly the dashboard's prepared data contracts."""
import io
import math
import textwrap
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from portfolio_comparison import comparison, COMPARABILITY
from portfolio_watchlist import watchlist, source_closure, evidence_for

NAVY = '18364A'
MUTED = '60798A'
PALE = 'EFF5F7'
MONEY = '"$"#,##0;[Red]("$"#,##0);"$0"'
PERCENT = '0.0%;[Red](0.0%);"0.0%"'
SHEETS = ('Portfolio Overview', 'Company Comparison', 'Portfolio Watchlist', 'Source References')


def literal(ws, row, column, value):
    c = ws.cell(row, column, value if value is not None else 'Unavailable')
    if isinstance(c.value, str):
        c.data_type = 's'
    c.font = Font(name='Aptos', size=10, color=NAVY)
    c.alignment = Alignment(vertical='top', wrap_text=True)
    return c


def base_sheet(wb, title, headers, widths, description):
    ws = wb.create_sheet(title)
    last = len(headers)
    for row, text in [(1, title), (2, 'SYNTHETIC GP REVIEW · Prepared results · For Investment Team Review'), (3, description)]:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last)
        c = literal(ws, row, 1, text)
        c.font = Font(name='Aptos', size=22 if row == 1 else 10, bold=row == 1, color=NAVY if row == 1 else MUTED)
    ws.row_dimensions[1].height = 34
    ws.row_dimensions[2].height = 22
    ws.row_dimensions[3].height = 46
    for col, (header, width) in enumerate(zip(headers, widths), 1):
        c = literal(ws, 5, col, header)
        c.fill = PatternFill('solid', fgColor=NAVY)
        c.font = Font(name='Aptos', bold=True, size=10, color='FFFFFF')
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[5].height = 32
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'C6' if title == 'Source References' else 'C6'
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.sheet_properties.tabColor = NAVY
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.paperSize = ws.PAPERSIZE_A3
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = '1:5'
    ws.page_margins.left = .25
    ws.page_margins.right = .25
    ws.oddFooter.center.text = 'Synthetic demonstration · Prepared company reports · Page &P of &N'
    return ws


def row_values(ws, row, values, height=48):
    for col, value in enumerate(values, 1):
        c = literal(ws, row, col, value)
        if row % 2 == 0:
            c.fill = PatternFill('solid', fgColor=PALE)
        c.border = Border(bottom=Side(style='hair', color='DCE6EB'))
    ws.row_dimensions[row].height = height


def link(cell, sheet, row, label=None):
    cell.hyperlink = "#'" + sheet + "'!A" + str(row)
    if label is not None:
        cell.value = label
        cell.data_type = 's'
    cell.font = Font(name='Aptos', size=10, color='206482', underline='single')


def export_portfolio(companies):
    wb = Workbook()
    wb.remove(wb.active)
    overview = base_sheet(wb, SHEETS[0],
        ['Portfolio company', 'Reporting period', 'Revenue', 'Reported EBITDA', 'EBITDA margin', 'Revenue vs budget', 'EBITDA vs budget', 'Report status', 'Priority investment issue'],
        [29, 28, 20, 20, 18, 20, 20, 25, 58], COMPARABILITY)
    compare = base_sheet(wb, SHEETS[1],
        ['Company', 'Reporting period', 'Metric / definition', 'Actual', 'Budget', 'Actual − budget / pp', 'Variance %', 'Units / accounting basis', 'Source IDs'],
        [29, 28, 49, 20, 20, 23, 18, 31, 56], 'Same-period company comparisons only. Reported EBITDA excludes adjusted earnings sensitivities. Margin = reported EBITDA / revenue. Unavailable comparisons are explicit.')
    watch = base_sheet(wb, SHEETS[2],
        ['Company', 'Report period', 'Original priority', 'Original disposition', 'Investment issue', 'Management question', 'Next action', 'Source evidence'],
        [29, 25, 15, 18, 56, 65, 70, 34], 'All accepted findings. Priority/disposition inherited from prepared analyses; no risk score or combined impact. Full original narratives, caveats and quotes follow the index. Finding periods can differ from headline periods.')
    sources = base_sheet(wb, SHEETS[3],
        ['Company', 'Source ID', 'Source workbook', 'Sheet / cell or calculation', 'Original value / formula', 'Validated value', 'Check / use and source period', 'Calculation inputs', 'Prepared run', 'Workbook SHA-256', 'Snapshot SHA-256'],
        [29, 22, 50, 44, 68, 28, 90, 48, 26, 68, 68], 'Company-qualified IDs; calculation inputs are included recursively to original cells. Source values/formulas are retained as text, never executed. Source workbooks are referenced, not embedded. Provenance hashes pin the approved package.')
    items = watchlist(companies)
    source_rows = {}
    next_source_row = 6
    for company in companies:
        view = comparison(company)
        ids = list(dict.fromkeys(s for key in ('revenue', 'ebitda', 'margin') for s in view[key].source_ids))
        ids += [s for item in items if item.company_id == company.id for s in item.source_ids]
        ids = source_closure(company.review, ids)
        calculations = {f['id']: f for f in company.review.package['skill_engine']['calculations']}
        for evidence in evidence_for(company.review, ids):
            sid = evidence['Fact ID']
            operands = ', '.join(calculations.get(sid, {}).get('inputs', []))
            vals = [company.name, sid, evidence['File'], evidence['Reference'], str(evidence['Original value / formula']),
                    evidence['Validated value'], evidence['Check / use'], operands, company.run,
                    company.provenance['workbook_sha256'], company.provenance['snapshot_sha256']]
            row_values(sources, next_source_row, vals, height=min(300, max(48, math.ceil(max(len(str(vals[4])) / 66, len(str(vals[6])) / 88)) * 14 + 14)))
            source_rows[(company.id, sid)] = next_source_row
            next_source_row += 1
    compare_row = 6
    for row, company in enumerate(companies, 6):
        v = comparison(company)
        rev, eb, margin = (v[k] for k in ('revenue', 'ebitda', 'margin'))
        issue = company.review.package['ai_insights'][0]
        row_values(overview, row, [company.name, v['period_label'], rev.actual, eb.actual, margin.actual,
                                 rev.variance_pct, eb.variance_pct, 'Verified prepared review', issue['title']], height=66)
        for col in (3, 4):
            overview.cell(row, col).number_format = MONEY
        for col in (5, 6, 7):
            overview.cell(row, col).number_format = PERCENT
        link(overview.cell(row, 1), SHEETS[1], compare_row)
        for key in ('revenue', 'ebitda', 'margin'):
            m = v[key]
            row_values(compare, compare_row, [company.name, v['period_label'], m.definition, m.actual, m.budget,
                                            m.variance, m.variance_pct, m.unit+' · basis: '+v['basis'], ', '.join(m.source_ids)], height=64)
            for col in (4, 5):
                compare.cell(compare_row, col).number_format = PERCENT if key == 'margin' else MONEY
            compare.cell(compare_row, 6).number_format = '0.0" pp";[Red](0.0" pp")' if key == 'margin' else MONEY
            compare.cell(compare_row, 7).number_format = PERCENT
            source_target = source_rows.get((company.id, m.source_ids[0])) if m.source_ids else None
            if source_target:
                link(compare.cell(compare_row, 9), SHEETS[3], source_target)
            compare_row += 1
    index_end = 5 + len(items)
    detail_row = index_end + 4
    for row, item in enumerate(items, 6):
        f = item.finding
        row_values(watch, row, [item.company_name, item.report_period, f['priority'], f['disposition'], f['title'],
                               f['management_question'], f['action'], ', '.join(f['fact_ids'])], height=130)
        link(watch.cell(row, 5), SHEETS[2], detail_row)
        first = source_rows[(item.company_id, f['fact_ids'][0])]
        link(watch.cell(row, 8), SHEETS[3], first)
        details = [('Finding', f['title']), ('Company / reporting package', item.company_name+' · '+item.report_period),
                   ('Finding ID / category', str(f['id'])+' · '+f['category']), ('Original priority / disposition', f['priority']+' · '+f['disposition']),
                   ('Evidence status', f['evidence_status']), ('Conclusion', f['conclusion']), ('Evidence', f['evidence']),
                   ('Financial implication', f['financial_implication']), ('Investment assessment', f['assessment']),
                   ('Next action', f['action']), ('Management question', f['management_question']), ('Caveat', item.presentation['caveat'])]
        details += [('Original source quote · '+q['source_id'], q['quote']) for q in f.get('source_quotes', [])]
        details += [('Source IDs / calculation operands', ', '.join(item.source_ids))]
        for label, value in details:
            literal(watch, detail_row, 1, label).font = Font(name='Aptos', bold=True, color=NAVY, size=10)
            watch.merge_cells(start_row=detail_row, start_column=2, end_row=detail_row, end_column=8)
            c = literal(watch, detail_row, 2, value)
            if label == 'Finding':
                c.font = Font(name='Aptos', size=13, bold=True, color=NAVY)
                c.fill = PatternFill('solid', fgColor='DCEAF0')
                link(watch.cell(detail_row, 1), SHEETS[2], row, '↑ Finding index')
            if label.startswith('Source IDs'):
                link(c, SHEETS[3], first)
            # Long original narratives are spread over wide merged cells.
            lines = max(1, len(textwrap.wrap(str(value), width=180)))
            watch.row_dimensions[detail_row].height = min(409, max(30, lines * 14 + 12))
            detail_row += 1
        detail_row += 2
    note_row = 6 + len(companies) + 2
    overview.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=9)
    literal(overview, note_row, 1, 'Prepared viewing: 0 new model calls / $0 current inference. Verified sources and arithmetic do not certify every investment conclusion. Review original findings and caveats before decisions.')
    overview.row_dimensions[note_row].height = 36
    for ws, end in [(overview, 5+len(companies)), (compare, compare_row-1), (watch, index_end), (sources, next_source_row-1)]:
        ws.auto_filter.ref = f'A5:{get_column_letter(ws.max_column)}{end}'
        ws.print_area = f'A1:{get_column_letter(ws.max_column)}{ws.max_row}'
    # Helpful, machine-verifiable provenance without provider payloads or credentials.
    overview['A2'].comment = Comment('Approved runs: '+', '.join(c.run for c in companies)+'; new model calls=0', 'Portfolio Intelligence')
    stream = io.BytesIO()
    wb.save(stream)
    data = stream.getvalue()
    check = load_workbook(io.BytesIO(data))
    if tuple(check.sheetnames) != SHEETS or any(c.data_type in ('e', 'f') for ws in check for row in ws for c in row):
        raise ValueError('GP workbook failed local validation.')
    return data
