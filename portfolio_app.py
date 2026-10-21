"""Prepared-only GP dashboard. Run on 8502; the frozen analyst app is separate."""
import streamlit as st
from engine import InputError
from portfolio_data import load_companies, company_by_id
from portfolio_ui import shell, overview, footer, render_watchlist

st.set_page_config(page_title='Portfolio Intelligence · GP', page_icon='▣', layout='wide', initial_sidebar_state='expanded')


@st.cache_data(show_spinner=False)
def prepared_companies():
    return load_companies()


try:
    with st.spinner('Verifying prepared company reports…'):
        companies = prepared_companies()
except (InputError, OSError, ValueError, KeyError) as exc:
    st.error('Prepared reports could not be verified. Restore the checkpoint sources and run scripts/seed_demo_results.py --verify-only. '+str(exc))
    st.stop()

page = st.query_params.get('page', 'overview')
shell(page, companies)
if page == 'company':
    from portfolio_company import render_company
    company = company_by_id(companies, st.query_params.get('company', 'summit'))
    if company is None:
        st.warning('Unknown company. Select Portfolio Overview to open a prepared report.')
    else:
        render_company(company)
elif page == 'watchlist':
    st.title('Portfolio Watchlist')
    render_watchlist(companies)
else:
    overview(companies)
    render_watchlist(companies, compact=True)
footer()
