"""Prepared-only GP dashboard. Run on 8502; the frozen analyst app is separate."""
import streamlit as st
from engine import InputError
from portfolio_data import load_companies, company_by_id
from portfolio_ui import shell, overview, footer, render_watchlist, page_heading
from portfolio_excel import export_portfolio

st.set_page_config(page_title='Portfolio Reporting Copilot | 154 Partners', page_icon='▣', layout='wide', initial_sidebar_state='auto')


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
if page == 'comparison':
    page = 'overview'
    st.query_params.from_dict({'page':'overview'})
shell(page, companies)
try:
    workbook_data = gp_workbook(companies)
except (InputError,OSError,ValueError) as exc:
    st.error('GP Excel source verification failed. Restore the canonical prepared sources before downloading. '+str(exc))
    st.stop()
if page == 'foundation':
    from portfolio_foundation_ui import render_foundation
    try:
        render_foundation(companies)
    except (ValueError,OSError) as exc:
        st.error('Operating data package verification failed: '+str(exc))
elif page == 'company':
    from portfolio_company import render_company
    company = company_by_id(companies, st.query_params.get('company', 'summit'))
    if company is None:
        st.warning('Unknown company. Select Portfolio Overview to open a prepared report.')
    else:
        render_company(company, companies)
elif page == 'issues':
    page_heading('Investment Issues', 'Verified findings → Management follow-up → Supporting source evidence', workbook_data)
    render_watchlist(companies)
elif page == 'source':
    from portfolio_document_ui import render_source_route
    render_source_route(companies)
elif page == 'excel':
    from portfolio_document_ui import render_documents
    render_documents(companies, workbook_data)
else:
    overview(companies, workbook_data)
    render_watchlist(companies, compact=True)
footer()
