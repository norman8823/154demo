"""Prepared-only GP dashboard. Run on 8502; the frozen analyst app is separate."""
import streamlit as st
import io
import pandas as pd
from openpyxl import load_workbook
from engine import InputError
from portfolio_data import load_companies, company_by_id
from portfolio_ui import shell, overview, footer, render_watchlist, page_heading, workbook_preview_value, render_comparison
from portfolio_excel import export_portfolio, SHEETS, OVERVIEW_HEAD, reference_records
from portfolio_watchlist import watchlist

st.set_page_config(page_title='Portfolio Intelligence · GP', page_icon='▣', layout='wide', initial_sidebar_state='auto')


@st.cache_data(show_spinner=False)
def prepared_companies():
    return load_companies()


@st.cache_data(show_spinner=False)
def gp_workbook(companies):
    return export_portfolio(companies)


try:
    with st.spinner('Verifying prepared company reports…'):
        companies = prepared_companies()
except (InputError, OSError, ValueError, KeyError) as exc:
    st.error('Prepared reports could not be verified. Restore the checkpoint sources and run scripts/seed_demo_results.py --verify-only. '+str(exc))
    st.stop()

page = st.query_params.get('page', 'overview')
if page == 'watchlist':
    page = 'issues'  # Existing deep links remain valid; current UI uses new name.
shell(page, companies)
workbook_data = gp_workbook(companies)
if page == 'company':
    from portfolio_company import render_company
    company = company_by_id(companies, st.query_params.get('company', 'summit'))
    if company is None:
        st.warning('Unknown company. Select Portfolio Overview to open a prepared report.')
    else:
        render_company(company, companies)
elif page == 'issues':
    page_heading('Investment Issues', 'Verified findings → Management follow-up → Supporting source evidence', workbook_data)
    render_watchlist(companies)
elif page == 'comparison':
    page_heading('Company Comparison', 'Verified financials · Clearly separated reporting periods',workbook_data)
    render_comparison(companies,matrix=True)
elif page == 'excel':
    from portfolio_ui import stats
    page_heading('Excel Reporting', 'Operational review · Company worksheets · Source-linked evidence', workbook_data)
    stats(companies)
    st.info('Use the GP workbook for portfolio review and management follow-up. Company figures retain their original reporting periods. Reporting Output provides numeric rows for copying or mapping into your existing template.')
    st.subheader('Workbook preview')
    book = load_workbook(io.BytesIO(workbook_data), data_only=True)
    previews=['Portfolio Overview','Company Comparison','Investment Issues','Source References']
    for tab, name in zip(st.tabs(previews), previews):
        with tab:
            sheet = book[name]
            # Show the actual generated tables; watchlist detail narratives follow
            # its index in Excel and are also available in the portfolio watchlist.
            head=OVERVIEW_HEAD if name=='Portfolio Overview' else 5
            count=(len(companies) if name=='Portfolio Overview' else (14 if name=='Company Comparison' else (len(watchlist(companies)) if name=='Investment Issues' else len(reference_records(companies)))))
            rows = list(sheet.iter_rows(min_row=head, max_row=head+count))
            frame = pd.DataFrame([[workbook_preview_value(c) for c in row] for row in rows[1:]], columns=[c.value for c in rows[0]])
            st.dataframe(frame, hide_index=True, width='stretch')
            st.caption(f'{len(frame)} records · Preview reads the generated workbook')
else:
    overview(companies, workbook_data)
    render_watchlist(companies, compact=True)
footer()
