"""Compact synthetic-return presentation, visibly separate from operating data."""
from html import escape
import pandas as pd
import streamlit as st
from portfolio_comparison import money, percent
from portfolio_investments import METHOD, investments_for, investment_summary


def gross_rate(value):
    return f'{value:.2%}' if value is not None else 'Unavailable'


def investment_cards(companies):
    investments=investments_for(companies);summary=investment_summary(investments)
    items=[('Current Portfolio Equity Value',money(summary['current_equity_value']),'Unrealized sponsor equity · USD'),
           ('Gross MOIC',f'{summary["gross_moic"]:.2f}x' if summary['gross_moic'] is not None else 'Unavailable','Realized + unrealized / paid-in'),
           ('Gross IRR',gross_rate(summary['gross_irr']),'Combined dated sponsor cash flows'),
           ('Total Invested Capital',money(summary['invested_capital']),'Cumulative sponsor contributions · USD')]
    st.markdown('<div class="gp-stats">'+''.join('<div class="gp-stat"><small>'+escape(label)+'</small><strong>'+escape(value)+'</strong><small>'+escape(note)+'</small></div>' for label,value,note in items)+'</div>',unsafe_allow_html=True)
    st.caption('Valuation '+summary['valuation_date']+' · Realized proceeds '+money(summary['realized_proceeds'])+' · Gross sponsor returns before fees, carry and fund expenses.')


def company_investment(company):
    from portfolio_ui import literal_prose
    investment=investments_for([company])[0];result=investment_summary([investment])
    with st.expander('Investment context · '+money(result['current_equity_value'])+' equity · '+f'{result["gross_moic"]:.2f}x MOIC · '+gross_rate(result['gross_irr'])+' gross IRR'):
        st.caption('Product Demo · Synthetic Data · '+METHOD)
        literal_prose(investment.sponsor+' · '+investment.fund+' · '+investment.investment_id)
        literal_prose(f'Invested {money(result["invested_capital"])} · Realized {money(result["realized_proceeds"])} · Ownership {investment.ownership:.1%} · Valuation {investment.valuation_date}')
        literal_prose(f'Illustrative enterprise value {money(investment.enterprise_value)} − gross debt {money(investment.gross_debt)} + cash {money(investment.cash)} = total common equity {money(investment.total_common_equity)}. Sponsor equity {money(investment.current_equity_value)}.')
        literal_prose(investment.assumptions)
        from portfolio_tables import responsive_table
        responsive_table(pd.DataFrame([{'Date':f.date.isoformat(),'Type':f.kind,'Sponsor USD':f.amount,'Description':f.description} for f in investment.return_cash_flows]),key='investment_flows_'+company.id,formatters={'Sponsor USD':lambda n:f'${n:,.0f}'})
        st.caption(result['irr_detail']+' · Ledger SHA-256 '+investment.ledger_sha256)
