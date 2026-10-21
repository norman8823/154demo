"""Compact synthetic-return presentation, visibly separate from operating data."""
from html import escape
import altair as alt
import pandas as pd
import streamlit as st
from portfolio_comparison import money, percent
from portfolio_investments import NOTICE, METHOD, investments_for, investment_summary


def gross_rate(value):
    return f'{value:.2%}' if value is not None else 'Unavailable'


def investment_cards(companies):
    investments=investments_for(companies);summary=investment_summary(investments)
    st.caption(NOTICE)
    items=[('Current Portfolio Equity Value',money(summary['current_equity_value']),'Unrealized sponsor equity · USD'),
           ('Gross MOIC',f'{summary["gross_moic"]:.2f}x' if summary['gross_moic'] is not None else 'Unavailable','Realized + unrealized / paid-in'),
           ('Gross IRR',gross_rate(summary['gross_irr']),'Combined dated sponsor cash flows'),
           ('Total Invested Capital',money(summary['invested_capital']),'Cumulative sponsor contributions · USD')]
    st.markdown('<div class="gp-stats">'+''.join('<div class="gp-stat"><small>'+escape(label)+'</small><strong>'+escape(value)+'</strong><small>'+escape(note)+'</small></div>' for label,value,note in items)+'</div>',unsafe_allow_html=True)
    st.caption('Illustrative valuation: '+summary['valuation_date']+' · Realized proceeds '+money(summary['realized_proceeds'])+' · '+METHOD)
    with st.expander('Illustrative investment values and valuation context'):
        st.caption('Invested capital versus current unrealized sponsor equity. Distributions are excluded from the current-value bar. All investment amounts are illustrative USD.')
        records=[{'Company':i.company_name,'Measure':label,'USD':value,'Valuation date':i.valuation_date.isoformat()} for i in investments
                 for label,value in [('Invested capital',investment_summary([i])['invested_capital']),('Current equity value',i.current_equity_value)]]
        chart=alt.Chart(pd.DataFrame(records)).mark_bar(cornerRadiusTopRight=2,cornerRadiusBottomRight=2).encode(
            y=alt.Y('Company:N',sort=[i.company_name for i in investments],title=None,axis=alt.Axis(labelExpr="split(datum.label, ' ')[0]",labelLimit=100,labelFontSize=10,labelOverlap=False)),
            yOffset=alt.YOffset('Measure:N',sort=['Invested capital','Current equity value']),
            x=alt.X('USD:Q',title='Illustrative sponsor USD',scale=alt.Scale(zero=True),axis=alt.Axis(format='$~s',tickCount=3)),
            color=alt.Color('Measure:N',scale=alt.Scale(domain=['Invested capital','Current equity value'],range=['#b8cbd9','#173e57']),legend=alt.Legend(title=None,orient='bottom',columns=1,labelLimit=250,labelFontSize=10)),
            tooltip=['Company:N','Measure:N',alt.Tooltip('USD:Q',format='$,.0f'),'Valuation date:N']).properties(height=260).configure_view(stroke=None)
        st.altair_chart(chart,width='stretch',key='illustrative_equity_chart')
        st.caption(investments[0].sponsor+' · '+investments[0].fund+' · '+investments[0].asset_class)
        st.caption('Enterprise value, debt, cash, ownership and dated sponsor cash flows are exposed in each company detail and the GP workbook Investment Ledger.')


def company_investment(company):
    investment=investments_for([company])[0];result=investment_summary([investment])
    with st.expander('Synthetic illustrative investment · '+money(result['current_equity_value'])+' equity · '+f'{result["gross_moic"]:.2f}x MOIC · '+gross_rate(result['gross_irr'])+' gross IRR'):
        st.caption(NOTICE+' · '+METHOD)
        st.write(investment.sponsor+' · '+investment.fund+' · '+investment.investment_id)
        st.write(f'Invested {money(result["invested_capital"])} · Realized {money(result["realized_proceeds"])} · Ownership {investment.ownership:.1%} · Valuation {investment.valuation_date}')
        st.write(f'Illustrative enterprise value {money(investment.enterprise_value)} − gross debt {money(investment.gross_debt)} + cash {money(investment.cash)} = total common equity {money(investment.total_common_equity)}. Sponsor equity {money(investment.current_equity_value)}.')
        st.write(investment.assumptions)
        st.dataframe(pd.DataFrame([{'Date':f.date.isoformat(),'Type':f.kind,'Sponsor USD':f.amount,'Description':f.description} for f in investment.return_cash_flows]),hide_index=True,width='stretch',column_config={'Sponsor USD':st.column_config.NumberColumn(format='dollar')})
        st.caption(result['irr_detail']+' · Ledger SHA-256 '+investment.ledger_sha256)
