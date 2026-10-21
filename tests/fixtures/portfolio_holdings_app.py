"""Test-only twelve-company layout; no production registry or ledger mutations."""
from dataclasses import replace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import streamlit as st
from portfolio_data import load_companies
from portfolio_investments import investments_for,investment_summary
from portfolio_ui import CSS
from portfolio_holdings import render_holdings

st.set_page_config(layout='wide',page_title='Test fixture · 12 holdings')
st.markdown(CSS,unsafe_allow_html=True)
from portfolio_mobile import mobile_panel
with st.sidebar:mobile_panel()
st.title('Twelve-company presentation fixture')
st.caption('Synthetic layout test only; copied prepared operating records, separate fixture IDs. Not the production portfolio.')
base=load_companies();results={i.company_id:investment_summary([i]) for i in investments_for(base)}
companies=[];fixture_results={}
for n in range(12):
    company=base[n%3];identity=f'fixture-{n+1:02}'
    companies.append(replace(company,id=identity,name=f'Fixture {n+1:02} · '+company.name))
    fixture_results[identity]=results[company.id]
render_holdings(companies,fixture_results)
