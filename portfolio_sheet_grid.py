"""Native, dependency-free read-only worksheet inspection component.

Only hash-verified original worksheet records are supplied by the shared viewer.
Selection stays in the browser: arrow keys never rerun Python or execute formulas.
"""
from datetime import date, datetime
from pathlib import Path
import streamlit.components.v2 as components
from portfolio_documents import checked_coordinate, cell_record, display_value

ASSETS=Path(__file__).with_name('portfolio_sheet_grid')
_grid=components.component('original_worksheet_grid',
    html='<div class="excel-viewer"></div>',
    css=(ASSETS/'grid.css').read_text(),js=(ASSETS/'grid.js').read_text())


def raw_text(value):
    if value is None:return ''
    if isinstance(value,(date,datetime)):return value.isoformat(sep=' ') if isinstance(value,datetime) else value.isoformat()
    if isinstance(value,bool):return 'TRUE' if value else 'FALSE'
    return str(value)


def worksheet_payload(company,sheet,cached,coordinate):
    checked_coordinate(sheet,coordinate)
    cells={}
    for row in sheet:
        for cell in row:
            if cell.value is None and cell.comment is None:continue
            record=cell_record(company,sheet,cached,cell.coordinate)
            fact=record['fact'] or {}
            cells[cell.coordinate]={
                'display':display_value(record['value'],cell.number_format),
                'bar':record['formula'] if record['formula'] is not None else raw_text(cell.value),
                'bold':bool(cell.font.bold),'label':record['label'],
                'observed':raw_text(record['value']),'origin':record['origin'],
                'format':cell.number_format,'comment':record['comment'],
                'standardized':raw_text(fact.get('value')),
                'scale':raw_text(fact.get('source_scale')),
                'currency':fact.get('currency',''),'period':fact.get('period',''),
            }
    return dict(sheet=sheet.title,rows=sheet.max_row,columns=sheet.max_column,
                initial=coordinate,cells=cells)


def workbook_payload(company,book,cached,sheet,coordinate):
    if sheet not in book.sheetnames:
        from engine import InputError
        raise InputError('The cited worksheet is not in the approved original.')
    checked_coordinate(book[sheet],coordinate)
    return dict(initial_sheet=sheet,citation={'sheet':sheet,'cell':coordinate},
                sheets={ws.title:worksheet_payload(company,ws,cached[ws.title],coordinate if ws.title==sheet else 'A1') for ws in book})


def render_sheet_grid(company,book,cached,sheet,coordinate,key):
    # Data is serialized as data, never interpolated into executable HTML/JS.
    _grid(key=key,data=workbook_payload(company,book,cached,sheet,coordinate),height='content')
