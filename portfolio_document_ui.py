"""One shared native source viewer for library, mappings and accepted findings."""
from html import escape
import streamlit as st
from portfolio_source_device import source_desktop, MOBILE_MESSAGE
from engine import InputError
from portfolio_documents import (original_document, source_books, checked_coordinate,
    source_fact, evidence_locations)

XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def open_source(company, sheet=None, cell=None):
    if not source_desktop():
        st.info(MOBILE_MESSAGE)
        return
    try:
        document = original_document(company)
        book, _ = source_books(document)
        if sheet is not None:
            if sheet not in book.sheetnames: raise InputError('The cited worksheet is not in the original workbook.')
            checked_coordinate(book[sheet], cell)
        default_sheet=next((s.title for s in book if s.max_column>1),book.sheetnames[0])
        serial=st.session_state.get('source_open_serial',0)+1
        st.session_state.source_open_serial=serial
        source_dialog(company, sheet or default_sheet, cell or 'A1',serial)
    except (InputError, OSError, ValueError) as exc:
        st.error('Source preview unavailable: '+str(exc))


@st.dialog('Source inspection', width='large', dismissible=True)
def source_dialog(company, requested_sheet, requested_cell, request_id):
    try:
        document = original_document(company)
        book, cached = source_books(document)
        if not source_desktop():
            st.info(MOBILE_MESSAGE)
            return
        st.markdown('<div class="source-document-header"><h3>'+escape(company.name)+'</h3><p>'+escape(document.filename)+'</p><small>Read-only · Verified original</small></div>',unsafe_allow_html=True)
        prefix='source_'+str(request_id)+'_'+company.id
        from portfolio_sheet_grid import render_sheet_grid
        render_sheet_grid(company,book,cached,requested_sheet,requested_cell,prefix+'_grid')
        st.download_button('Download Original',document.data,file_name=document.filename,mime=XLSX,on_click='ignore',key=prefix+'_download')
    except (InputError,OSError,ValueError) as exc:
        st.error('Source preview unavailable: '+str(exc))


def source_action(company, fact_id, key):
    if not source_desktop():return
    try:
        fact=source_fact(company,fact_id)
    except (InputError,OSError,ValueError) as exc:
        st.caption('Original source unavailable: '+str(exc)); return
    with st.container(key='desktop_source_'+key):
        if st.button('View in Source',key=key): open_source(company,fact['sheet'],fact['cell'])


def evidence_actions(company, source_ids, key):
    if not source_desktop():return
    try: originals,derived,unsupported=evidence_locations(company,source_ids)
    except (InputError,OSError,ValueError) as exc:
        st.warning('Original sources unavailable: '+str(exc)); return
    if derived:
        with st.expander('Derived calculations & original operands'):
            for calculation in derived:
                st.text(calculation['label'])
                st.code(calculation.get('expression',calculation.get('raw','')),language=None)
                st.caption('Inputs: '+', '.join(calculation['inputs'])+' · '+calculation.get('limitation',''))
            st.caption('Calculated values are not original worksheet cells. Inspect their recorded source operands below.')
    if originals:
        index={f['id']:f for f in originals}
        identity=st.selectbox('Original source cell',list(index),format_func=lambda i:index[i]['ref']+' · '+(index[i].get('label') or i),key=key+'_operand')
        source_action(company,identity,key+'_view')
    if unsupported: st.caption(str(len(unsupported))+' supporting records have no supported single-cell location; their original evidence remains available above.')


def render_documents(companies, workbook_data):
    from portfolio_ui import page_heading
    from portfolio_comparison import comparison
    from portfolio_company import company_export
    page_heading('Documents & Reports','Original company reporting packages · Source-backed reporting',None)
    st.subheader('Source Documents')
    st.caption('Approved original workbooks, verified against the prepared-analysis manifest before preview or download.')
    for company in companies:
        with st.container(border=True,key='source_document_'+company.id):
            try: document=original_document(company)
            except (InputError,OSError,ValueError) as exc:
                st.error(company.name+' · '+str(exc));continue
            if source_desktop():
                title,preview,download=st.columns([3,1,1.5],vertical_alignment='center')
            else:
                title,download=st.columns([3,1.5],vertical_alignment='center')
            title.markdown('**'+company.name+'**')
            title.caption(document.filename+' · '+comparison(company)['period_label'])
            if source_desktop():
                with preview,st.container(key='desktop_source_preview_'+company.id):
                    if st.button('Preview',key='preview_'+company.id,width='stretch'): open_source(company)
            download.download_button('Download Original',document.data,file_name=document.filename,mime=XLSX,on_click='ignore',key='original_'+company.id,width='stretch')
    st.subheader('Generated Reports')
    st.caption('Generated portfolio and company analyses. Original reporting packages are listed separately above.')
    st.download_button('↓ Download Portfolio Excel',workbook_data,file_name='GP_Portfolio_Review.xlsx',mime=XLSX,key='documents_gp_download')
    ids={c.id:c for c in companies}
    selected=st.selectbox('Company report',list(ids),format_func=lambda identity:ids[identity].name,key='documents_company')
    company=ids[selected]
    choice=st.selectbox('Company Excel format',['Standard Excel report','Use supplied firm template'],key='documents_format')
    custom=choice=='Use supplied firm template'
    template=st.file_uploader('Optional company Excel template',type=['xlsx'],key='documents_template') if custom else None
    if template:
        from portfolio_financial_reporting import export_company_report as export_report
        try: data=export_report(company.review,template.getvalue())
        except Exception:
            st.error('This template could not be populated. Choose the standard report or supplied firm template.');return
    else: data=company_export(company.review,custom)
    st.download_button('Download Company Excel',data[0],file_name=data[1],mime=XLSX,key='documents_company_download')


def render_source_route(companies):
    """A guarded direct inspection URL; never a file path or upload endpoint."""
    from portfolio_data import company_by_id
    st.title('Source Documents')
    if not source_desktop():
        st.info(MOBILE_MESSAGE)
        return
    company=company_by_id(companies,st.query_params.get('company',''))
    if company is None:
        st.error('Unknown approved source company.')
        return
    open_source(company,st.query_params.get('sheet'),st.query_params.get('cell'))
