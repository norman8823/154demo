"""Concise phone presentation of original prepared findings; no analysis calls."""
from html import escape
import streamlit as st
from portfolio_investments import investments_for,investment_summary
from portfolio_comparison import money


def assessment_items(company,requested=None):
    """Original briefing/issue order, with an explicit valid deep link first."""
    findings=company.review.package['ai_insights']
    index={f['id']:f for f in findings}
    briefing=company.review.package.get('ai_briefing',[])
    lead=next((b['finding_id'] for b in briefing if b['finding_id'] in index),findings[0]['id'] if findings else None)
    try:requested=int(requested)
    except (ValueError,TypeError):requested=None
    lead=requested if requested in index else lead
    return ([index[lead]]+[f for f in findings if f['id']!=lead]) if lead is not None else []


def _finding(finding):
    from portfolio_ui import literal_prose
    st.caption(finding['priority'].title()+' · '+finding['disposition'].replace('_',' ').title())
    literal_prose(finding['conclusion'])
    if finding.get('assessment'):literal_prose(finding['assessment'])
    st.markdown('**Management follow-up**')
    literal_prose(finding['action'])
    st.markdown('**Question for management**')
    literal_prose(finding['management_question'])


def render_mobile_detail(company):
    from portfolio_ui import navigate,literal_prose
    with st.container(key='mobile_company_detail'):
        st.button('← Back to portfolio',key='mobile_back_portfolio',on_click=navigate,args=('overview',),width='stretch')
        st.markdown('<h1>'+escape(company.name)+'</h1>',unsafe_allow_html=True)
        st.caption(company.sector+' · '+company.review.report_period+' · Prepared assessment')
        investment=investments_for([company])[0];result=investment_summary([investment])
        values=[('Invested capital',result['invested_capital']),('Realized distributions',result['realized_proceeds']),('Current equity value',result['current_equity_value'])]
        st.markdown('<div class="mobile-investment-context">'+''.join('<div><small>'+label+'</small><strong>'+escape(money(value))+'</strong></div>' for label,value in values)+'</div>',unsafe_allow_html=True)
        st.caption('Product Demo · Synthetic Data · USD · As of '+investment.valuation_date.isoformat())
        st.subheader('Investment Assessment')
        findings=assessment_items(company,st.query_params.get('finding'))
        if findings:
            lead=findings[0]
            with st.container(key='mobile_primary_'+company.id+'_'+str(lead['id'])):
                st.markdown('<h3>'+escape(lead['title'])+'</h3>',unsafe_allow_html=True)
                _finding(lead)
            if len(findings)>1:
                st.subheader('Key risks & follow-ups')
                for finding in findings[1:]:
                    with st.expander(finding['title']):_finding(finding)
        else:st.info('No accepted investment assessment is available for this company.')
        with st.expander('Investment context'):
            literal_prose(investment.sponsor+' · '+investment.fund)
            st.caption('Investment date '+investment.investment_date.isoformat()+' · Ownership '+f'{investment.ownership:.1%}'+' · '+investment.status.replace('_',' ').title())
        st.caption('Source-backed assessment · Original conclusions and qualifications retained.')
