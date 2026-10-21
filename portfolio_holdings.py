"""Adaptive holdings presentation. No changes to investment or operating math."""
from html import escape
import streamlit as st
from portfolio_comparison import money
from portfolio_investments import investments_for,investment_summary


def selected_holdings(ids,current=None):
    """None initializes two; an empty selection stays empty across reruns."""
    if len(set(ids))!=len(ids):raise ValueError('Holdings require unique company IDs.')
    return list(ids[:2]) if current is None else list(dict.fromkeys(i for i in current if i in ids))[:2]


def _toggle(identity):
    current=list(st.session_state.gp_holding_selected)
    checked=st.session_state['holding_select_'+identity]
    st.session_state.gp_holding_selected=selected_holdings(st.session_state.gp_holding_ids,
        current+[identity] if checked else [i for i in current if i!=identity])


def _clear():
    st.session_state.gp_holding_selected=[]
    for identity in st.session_state.gp_holding_ids:st.session_state['holding_select_'+identity]=False


def render_holdings(companies,investment_results=None):
    """Optional result injection permits larger presentation fixtures, never demo data."""
    from portfolio_ui import company_card
    from portfolio_investment_ui import gross_rate
    ids=[c.id for c in companies]
    selected_holdings(ids)  # Validate IDs even for the small-card layout.
    if investment_results is None:
        investment_results={i.company_id:investment_summary([i]) for i in investments_for(companies)}
    if set(ids)-investment_results.keys():raise ValueError('Missing company investment presentation.')
    st.subheader('Portfolio Holdings & Performance')
    st.caption('Operating financials retain their original periods. Actual / Budget charts use separate company axes. Gross MOIC and IRR are synthetic illustrative sponsor data, before fees and carry.')
    selected=companies
    if len(companies)>3:
        current=selected_holdings(ids,st.session_state.get('gp_holding_selected'))
        st.session_state.gp_holding_selected=current
        st.session_state.gp_holding_ids=ids
        with st.container(key='adaptive_holdings'):
            controls,clear=st.columns([4,1])
            controls.caption(f'{len(current)} of 2 companies selected · Uncheck a company to replace it, or clear the selection.')
            clear.button('Clear selection',on_click=_clear,key='holdings_clear',width='stretch')
            with st.expander('Holdings table options'):
                search=st.text_input('Find a company',key='holdings_search')
                sort=st.selectbox('Sort holdings',['Company','Invested capital','Current equity','Gross MOIC','Gross IRR'],key='holdings_order')
                descending=st.checkbox('Descending',key='holdings_descending')
            fields=['Company','Invested capital','Current equity','Gross MOIC','Gross IRR']
            st.markdown('<div class="holdings-head">'+''.join('<span>'+f+'</span>' for f in fields)+'</div>',unsafe_allow_html=True)
            keys={'Invested capital':'invested_capital','Current equity':'current_equity_value','Gross MOIC':'gross_moic','Gross IRR':'gross_irr'}
            visible=[c for c in companies if search.casefold() in c.name.casefold()]
            visible.sort(key=lambda c:c.name.casefold() if sort=='Company' else (investment_results[c.id][keys[sort]] is None,investment_results[c.id][keys[sort]] or 0),reverse=descending)
            for c in visible:
                r=investment_results[c.id];key='holding_select_'+c.id
                st.session_state[key]=c.id in current
                with st.container(key='holding_row_'+c.id):
                    check,values=st.columns([.35,9],gap='small')
                    check.checkbox('Select '+c.name,key=key,label_visibility='collapsed',disabled=len(current)==2 and c.id not in current,on_change=_toggle,args=(c.id,))
                    moic=f'{r["gross_moic"]:.2f}x' if r['gross_moic'] is not None else 'Unavailable'
                    cells=[('<a href="?page=company&amp;company='+escape(c.id,quote=True)+'">'+escape(c.name)+'</a>')]+[escape(v) for v in (money(r['invested_capital']),money(r['current_equity_value']),moic,gross_rate(r['gross_irr']))]
                    values.markdown('<div class="holdings-row">'+''.join('<div><small>'+label+'</small>'+cell+'</div>' for label,cell in zip(fields,cells))+'</div>',unsafe_allow_html=True)
            if not visible:st.info('No companies match this filter. Selected companies remain below.')
        selected=[c for c in companies if c.id in current]
        if not selected:st.info('Select up to two companies above to inspect operating performance.')
    if selected:
        with st.container(key='operating_cards'):
            for col,c in zip(st.columns(len(selected)),selected):
                with col:company_card(c,investment_results[c.id])
