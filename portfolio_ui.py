"""GP presentation; company analytics and financials stay in their existing modules."""
from html import escape
import streamlit as st
from portfolio_comparison import comparison, money, percent, against_plan, COMPARABILITY

from pathlib import Path

CSS = '<style>'+Path(__file__).with_name('portfolio_layout.css').read_text()+'</style>'


def navigate(page, company=None, finding=None):
    if page == 'company' and company and company != st.query_params.get('company'):
        for key in ('gp_company_route','gp_company_tab','selected','gp_selected_finding','export','custom','gp_company_format','gp_company_template'):
            st.session_state.pop(key, None)
        # Explicit widget state reaches the browser; deletion alone can retain
        # a prior company's frontend selection during a callback rerun.
        st.session_state.gp_company_format = 'Standard Excel report'
    params = {'page': page}
    if company:
        params['company'] = company
    if finding is not None:
        params['finding'] = str(finding)
    st.query_params.from_dict(params)


def shell(page, companies):
    st.markdown(CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="gp-brand">▣ &nbsp;Portfolio Intelligence<br><small>GP Reporting Copilot</small></div>', unsafe_allow_html=True)
        st.caption('WORKSPACE')
        for label, destination in [('Portfolio Overview', 'overview'), ('Data Foundation','foundation'), ('Investment Issues', 'issues'), ('Company Detail', 'company'), ('Excel Reports', 'excel')]:
            st.button(label, key='nav_watchlist' if destination == 'issues' else 'nav_'+destination, type='primary' if page == destination else 'secondary', width='stretch',
                      on_click=navigate, args=(destination, st.query_params.get('company', companies[0].id)) if destination == 'company' else (destination,))
        ids = [c.id for c in companies]
        current = st.query_params.get('company', ids[0])
        current = current if current in ids else ids[0]
        if st.session_state.get('gp_sidebar_company') != current:
            st.session_state.gp_sidebar_company = current
        st.selectbox('Open company', ids, format_func=lambda slug: next(c.name for c in companies if c.id == slug).split()[0],
                     key='gp_sidebar_company', on_change=select_company, args=('gp_sidebar_company',))
        st.divider()
        st.caption('Synthetic demonstration only')
        st.caption('Prepared results · 0 new model calls')
    names = {'overview': 'Overview', 'foundation':'Data Foundation', 'issues': 'Investment Issues', 'watchlist': 'Investment Issues', 'comparison':'Company Comparison', 'company': 'Company Detail', 'excel': 'Excel Reports'}
    st.markdown('<div class="gp-breadcrumb">Portfolio / '+names.get(page, 'Overview')+'<span class="gp-tag">SYNTHETIC DATA &nbsp; · &nbsp; GP</span></div>', unsafe_allow_html=True)


def stats(companies):
    from portfolio_dashboard import workflow_summary
    summary = workflow_summary(companies)
    items = [('Reporting coverage', f'{summary["received"]} / {summary["companies"]}', 'Prepared company assessments available'),
             ('Below EBITDA plan', f'{summary["below_plan"]} / {summary["comparable_budget"]}', 'Each company vs its same-period budget'),
             ('Accepted investment issues', str(summary['issues']), 'Original findings, including qualified opportunities'),
             ('Act-now follow-ups', str(summary['act_now']), 'Original analyst disposition · no new risk score')]
    st.markdown('<div class="gp-stats">'+''.join('<div class="gp-stat"><small>'+escape(a)+'</small><strong>'+escape(b)+'</strong><small>'+escape(c)+'</small></div>' for a,b,c in items)+'</div>', unsafe_allow_html=True)


def company_card(company):
    from portfolio_dashboard import ebitda_chart
    v = comparison(company)
    m = v['ebitda']
    with st.container(key='gp_company_'+company.id):
        st.markdown('<div class="v2-company-head"><div><strong>'+escape(company.name)+'</strong><small>'+escape(company.sector)+'</small></div><span class="v2-frequency">'+escape(v['frequency'].upper())+'</span></div><div class="v2-figures"><div><small>REVENUE</small><b>'+escape(money(v['revenue'].actual,v['revenue'].unit))+'</b></div><div><small>REPORTED EBITDA</small><b>'+escape(money(m.actual,m.unit))+'</b></div><div><small>EBITDA MARGIN</small><b>'+percent(v['margin'].actual)+'</b></div></div><div class="v2-rule"></div><div class="v2-period">'+escape(v['period_label'])+' · Reported EBITDA</div>', unsafe_allow_html=True)
        st.altair_chart(ebitda_chart(company), width='stretch', key='ebitda_chart_'+company.id)
        delta = (money(m.variance,m.unit)+' / '+against_plan(m)) if m.variance is not None else 'Budget comparison unavailable'
        st.markdown('<div class="v2-variance">'+escape(delta)+'</div>',unsafe_allow_html=True)
        st.button('Open investment review →', key='open_'+company.id, width='stretch', on_click=navigate, args=('company', company.id))


def page_heading(title, subtitle, workbook_data=None):
    heading, action = st.columns([3, 1])
    with heading:
        st.title(title)
        st.caption(subtitle)
    if workbook_data:
        action.download_button('↓ Download Portfolio Excel', workbook_data,
            file_name='GP_Portfolio_Review_Sep2026_FY2026.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type='primary', width='stretch', key='gp_download')


def overview(companies, workbook_data=None):
    st.markdown('<div class="gp-eyebrow">GP MONITORING / REPORTING CYCLE</div>', unsafe_allow_html=True)
    page_heading('Portfolio Overview', 'Operating performance, investment issues and management follow-up · September 2026 / FY2026', workbook_data)
    st.markdown('<div class="v2-workflow"><b>01 &nbsp;Company packages ✓</b><span>→</span><b>02 &nbsp;Prepared AI assessments ✓</b><span>→</span><b>03 &nbsp;Portfolio review</b><span>→</span><b>04 &nbsp;Management follow-up</b><span>→</span><b>05 &nbsp;Source-linked Excel</b></div>', unsafe_allow_html=True)
    from portfolio_investment_ui import investment_cards
    investment_cards(companies)
    from portfolio_dashboard import workflow_summary
    review=workflow_summary(companies)
    st.markdown('<div class="gp-guard">OPERATING REVIEW · '+str(review['received'])+'/'+str(review['companies'])+' packages verified · '+str(review['below_plan'])+' below EBITDA plan · '+str(review['issues'])+' accepted investment issues · '+str(review['act_now'])+' act-now follow-ups</div>',unsafe_allow_html=True)
    st.subheader('Operating performance')
    st.caption('Reported EBITDA: Actual vs Budget · Each chart has its own dollar axis and period. Annual and monthly amounts are never pooled.')
    with st.container(key='operating_cards'):
        for column, company in zip(st.columns(len(companies)), companies):
            with column:
                company_card(company)
    render_comparison(companies)
    st.markdown('<div class="gp-guard">'+escape(COMPARABILITY)+'</div>', unsafe_allow_html=True)


def render_comparison(companies, matrix=False):
    import pandas as pd
    from portfolio_dashboard import operating_rows, comparison_matrix
    from portfolio_tables import responsive_table
    st.subheader('Company comparison' if matrix else 'Investment holdings & operating comparison')
    st.caption('Investment values are synthetic illustrative USD, as of September 30, 2026. Operating periods remain on the company cards above. Use Table options to sort; select a company for detail.')
    if matrix:
        responsive_table(pd.DataFrame(comparison_matrix(companies)),key='comparison_matrix')
    else:
        columns=['Company','Invested capital (illustrative)','Current equity (illustrative)','Gross MOIC (illustrative)','Gross IRR (illustrative)','Reported EBITDA','EBITDA margin','Revenue vs budget','Sector']
        frame=pd.DataFrame(operating_rows(companies))[columns]
        labels=dict(zip(columns,['Company','Invested','Equity value','Gross MOIC','Gross IRR','EBITDA','Margin','Revenue vs plan','Sector']))
        formatters={c:money for c in ['Invested capital (illustrative)','Current equity (illustrative)','Reported EBITDA']}
        formatters.update({c:percent for c in ['Gross IRR (illustrative)','EBITDA margin','Revenue vs budget']})
        formatters['Gross IRR (illustrative)']=lambda v:f'{v:.2%}' if v is not None else 'Unavailable'
        formatters['Gross MOIC (illustrative)']=lambda v:f'{v:.2f}x' if v is not None else 'Unavailable'
        responsive_table(frame,key='holdings',page_size=12,labels=labels,formatters=formatters,css_class='gp-holdings',details=False,
                         links={'Company':{c.name:'?page=company&company='+c.id for c in companies}})


def footer():
    st.markdown('<div class="gp-note">Synthetic demonstration · Prepared assessments · For Investment Team Review · No new inference</div>', unsafe_allow_html=True)


def render_watchlist(companies, compact=False):
    from portfolio_watchlist import watchlist
    items = watchlist(companies)
    if compact:
        st.subheader('Investment Issues')
    st.caption('Original accepted findings, grouped by company. Priority and disposition are inherited; finding impacts may refer to YTD, LTM or other periods beyond the headline report.')
    if compact:
        # One original lead issue per company keeps the landing screen concise.
        items = [next(i for i in items if i.company_id == c.id and i.finding['id'] == c.review.package['ai_insights'][0]['id']) for c in companies]
    else:
        company_filter, priority_filter = st.columns(2)
        options = ['All companies']+[c.name for c in companies]
        route_company = st.query_params.get('company')
        if st.session_state.get('gp_issue_route') != route_company:
            st.session_state.gp_issue_route = route_company
            st.session_state.gp_issue_company = next((c.name for c in companies if c.id == route_company), 'All companies')
        selected_company = company_filter.selectbox('Company', options, key='gp_issue_company')
        selected_priority = priority_filter.selectbox('Original priority', ['All priorities', 'high', 'medium', 'low'])
        items = [i for i in items if (selected_company == 'All companies' or i.company_name == selected_company)
                 and (selected_priority == 'All priorities' or i.finding['priority'] == selected_priority)]
    st.caption(f'{len(items)} findings shown · company amounts and impacts are never summed')
    groups = [(c, [i for i in items if i.company_id == c.id]) for c in companies]
    groups = [(c, group) for c, group in groups if group]
    if not groups:
        st.info('No accepted issues match this selection.')
        return
    if compact:
        with st.container(key='issues_preview'):
            _compact_issues(groups)
    else:
        _full_issues(groups)
    if compact:
        st.button('Open all investment issues →', on_click=navigate, args=('issues',))


def _compact_issues(groups):
    for col, (company, group) in zip(st.columns(len(groups)), groups):
        with col, st.container(border=True):
            item = group[0]
            f = item.finding
            st.markdown('**'+company.name+'**')
            st.caption(f['priority'].title()+' · '+f['disposition'].replace('_',' ').title())
            literal_prose(f['title'])
            st.caption('Finding impact · source scope retained')
            literal_prose(f.get('impact','Not quantified'))
            st.markdown('**Management follow-up**')
            literal_prose(f['management_question'])
            st.button('View source evidence →', key='lead_'+company.id+'_'+str(f['id']), on_click=navigate,
                      args=('company',company.id,f['id']),width='stretch')

def _full_issues(groups):
    for company, group in groups:
        st.subheader(company.name)
        st.caption(comparison(company)['period_label']+' · '+str(len(group))+' accepted issues')
        for index, item in enumerate(group):
            f = item.finding
            with st.expander(f['title'], expanded=index == 0):
                st.caption(f['priority'].title()+' · '+f['disposition'].replace('_',' ').title()+' · '+item.presentation['severity'])
                st.markdown('**Source-supported impact**')
                literal_prose(f.get('impact','Not quantified'))
                literal_prose(f['conclusion'])
                for label, key in [('Management question','management_question'),('Proposed follow-up','action')]:
                    st.markdown('**'+label+'**')
                    literal_prose(f[key])
                st.button('View source evidence →',key='watch_'+company.id+'_'+str(f['id']),on_click=navigate,
                          args=('company',company.id,f['id']),width='stretch')
                with st.expander('Original analysis, qualifications & source quotations'):
                    for label,key in [('Accepted finding narrative','text'),('Evidence','evidence'),('Financial implication','financial_implication'),('Investment assessment','assessment')]:
                        st.markdown('**'+label+'**');literal_prose(f[key])
                    literal_prose(item.presentation['caveat'])
                    st.caption('Source IDs: '+', '.join(f['fact_ids']))
                    for quote in f.get('source_quotes',[]):
                        literal_prose(quote['quote']);st.caption('Original source quote · '+quote['source_id'])

def select_company(widget_key):
    navigate('company', st.session_state[widget_key])


def company_selector(companies, current):
    ids = [c.id for c in companies]
    if st.session_state.get('gp_company_selector') != current:
        st.session_state.gp_company_selector = current
    st.selectbox('Company', ids, format_func=lambda slug:next(c.name for c in companies if c.id == slug),
                 key='gp_company_selector',on_change=select_company,args=('gp_company_selector',))


def literal_prose(text):
    # Dollar signs in source financial prose are currency, never KaTeX math.
    st.markdown('<div class="prose">'+escape(text).replace('$', '&#36;')+'</div>', unsafe_allow_html=True)


def workbook_preview_value(cell):
    """Honor the generated workbook's currency/percent/pp presentation in UI."""
    value = cell.value
    if not isinstance(value, (int, float)):
        return value
    fmt = cell.number_format
    if '%' in fmt:
        return f'{value:.1%}'
    if '" pp"' in fmt:
        return f'{value:+.1f} pp'
    if '"$"' in fmt:
        return ('−' if value < 0 else '')+f'${abs(value):,.0f}'
    return str(value)
