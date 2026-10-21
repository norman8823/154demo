"""GP presentation; company analytics and financials stay in their existing modules."""
from html import escape
import streamlit as st
from portfolio_comparison import comparison, money, percent, against_plan, COMPARABILITY

CSS = '''<style>
.stApp {background:#fff;color:#18364a;}
.block-container {max-width:1460px;padding:2rem 2.6rem 3rem;}
header[data-testid="stHeader"] {background:transparent;height:0;}
[data-testid="stSidebar"] {background:#102e42;min-width:235px;max-width:235px;}
[data-testid="stSidebar"] * {color:#d8e6ee;}
[data-testid="stSidebar"] .stButton button {background:transparent;border:0;text-align:left;justify-content:flex-start;}
[data-testid="stSidebar"] .stButton button[kind="primary"] {background:#294e65;color:#fff;}
[data-testid="stSidebar"] [data-testid="stSelectbox"] * {color:#18364a;}
h1,h2,h3 {color:#18364a;letter-spacing:-.025em;}
h1 {font-size:2rem!important;} h2,h3 {font-size:1.15rem!important;}
[data-testid="stSidebarUserContent"] {padding-top:1.5rem;}
[data-testid="stVerticalBlock"] {gap:.75rem;}
p,li {line-height:1.55;}
.stButton button,.stDownloadButton button {border-radius:6px;min-height:40px;font-weight:600;}
.stButton button[kind="primary"],.stDownloadButton button[kind="primary"] {background:#183b52;border:0;}
.gp-brand {font-weight:750;font-size:17px;padding:0 0 28px;color:white;line-height:1.4;}
.gp-brand small {font-size:11px;color:#b8cbd7;font-weight:400;}
.gp-eyebrow {font-size:10px;font-weight:750;letter-spacing:.13em;color:#608299;margin-top:20px;}
.gp-breadcrumb {border-bottom:1px solid #dce6ec;padding:0 0 20px;font-size:12px;font-weight:600;color:#527086;}
.gp-tag {float:right;background:#e9f3f6;color:#27728a;padding:4px 12px;border-radius:20px;font-size:10px;letter-spacing:.06em;}
.gp-stats {display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:24px 0;}
.gp-stat {border:1px solid #d9e3eb;border-radius:10px;padding:16px 20px;background:white;}
.gp-stat small,.gp-company small,.gp-kpi small {display:block;color:#647f93;font-size:11px;}
.gp-stat strong {display:block;font-size:27px;margin:5px 0;color:#18364a;}
.gp-row {display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr 1.55fr;align-items:start;gap:16px;}
.gp-company {padding-right:8px;}.gp-company strong {display:block;font-size:16px;margin:3px 0 5px;}
.gp-period {margin:12px 0 5px;color:#58758b;font-size:11px;}
.gp-kpi {border-left:1px solid #dce6ec;padding-left:16px;min-height:80px;}
.gp-kpi strong {display:block;font-size:24px;margin:7px 0 4px;white-space:nowrap;}
.gp-delta {font-size:11px;}.gp-adverse {color:#ad4848;}.gp-favorable {color:#27755a;}
.gp-focus {border-left:3px solid #bf9449;padding-left:13px;font-size:12px;line-height:1.55;}
.gp-focus small {display:block;color:#9d722c;font-weight:700;font-size:10px;letter-spacing:.04em;margin-bottom:8px;}
div[class*="st-key-gp_company_"] {border:1px solid #d9e3eb;border-radius:10px;padding:18px 22px;background:white;margin-bottom:2px;}
div[class*="st-key-gp_company_"] [data-testid="stVerticalBlock"] {gap:.25rem;}
.gp-guard {background:#edf5f8;border:1px solid #d7e7ee;padding:12px 16px;border-radius:7px;color:#527086;font-size:12px;margin:16px 0 22px;}
.gp-note {font-size:11px;color:#7890a2;margin:20px 0;}
[data-testid="stMetric"] {background:white;border:1px solid #dce6ec;border-radius:8px;padding:16px;}
.prose {font-size:14px;line-height:1.65;color:#526d80;}
.finding {border-top:2px solid #a8b8c3;padding:15px 4px;}.finding h3 {font-size:16px!important;}
.indicator {font-size:25px;font-weight:700;color:#18364a;}.indicator small {font-size:11px;}
.chain {border:1px solid #dce7ee;background:#f6f9fb;padding:15px;border-radius:7px;min-height:140px;font-size:12px;}.chain small {display:block;color:#678394;font-size:10px;margin-bottom:12px;}
.badge {font-size:10px;background:#edf2f5;color:#416173;padding:4px;}
.excel-bar {background:#19694f;color:white;padding:12px;border-radius:6px;}.report-banner {font-size:11px;padding:10px;color:#527463;}
[data-testid="stToolbar"] {display:none;} footer {visibility:hidden;}
@media(max-width:1100px) {.gp-row {grid-template-columns:repeat(3,1fr);}.gp-company {grid-column:1/-1;}.gp-focus {grid-column:1/-1;}}
@media(max-width:600px) {.block-container {padding:1.5rem 1rem;}.gp-stats {grid-template-columns:1fr;}.gp-row {grid-template-columns:1fr;}.gp-company,.gp-focus {grid-column:auto;}.gp-kpi {border-left:0;padding-left:0;min-height:0;}}
@media(max-width:800px) {header[data-testid="stHeader"] {height:2.5rem;background:white;} [data-testid="stToolbar"] {display:flex;} .stAppDeployButton,#MainMenu {display:none;} .block-container {padding-top:3.2rem;}}
</style>'''

CSS += '''<style>
.block-container {max-width:1580px;padding:1.5rem 2.5rem 2rem;}
[data-testid="stSidebar"] {min-width:215px;max-width:215px;background:#112e42;}
[data-testid="stSidebarUserContent"] {padding:1.4rem 1.1rem;}
.gp-brand {font-size:17px;line-height:1.35;padding:0 0 16px;}
.gp-breadcrumb {padding-bottom:13px;font-size:11px;}
.gp-eyebrow {margin-top:12px;}
h1 {font-size:1.85rem!important;} h2,h3 {font-size:1.06rem!important;}
.gp-stats {grid-template-columns:repeat(4,1fr);gap:12px;margin:15px 0 20px;}
.gp-stat {padding:15px 18px;border-radius:8px;border-color:#e0e7ed;}
.gp-stat strong {font-size:29px;margin:7px 0;}
.gp-stat small {font-size:11px;line-height:1.45;}
.v2-workflow {display:flex;align-items:center;gap:12px;padding:11px 15px;margin:12px 0 6px;background:#f4f7fa;border:1px solid #e4ebf0;border-radius:6px;font-size:11px;color:#678195;flex-wrap:wrap;}
.v2-workflow b {color:#24485e;font-weight:600;}.v2-workflow span {color:#8b9eac;}
div[class*="st-key-gp_company_"] {border:1px solid #dce5ec;padding:17px 18px 13px;border-radius:9px;min-width:0;}
.v2-company-head {display:flex;align-items:start;justify-content:space-between;gap:8px;min-height:44px;}
.v2-company-head strong {font-size:15px;line-height:1.3;}.v2-company-head small {display:block;color:#708498;font-size:10px;margin-top:5px;}
.v2-frequency {font-size:9px;white-space:nowrap;color:#506b80;background:#eef3f7;padding:4px 6px;border-radius:4px;}
.v2-figures {display:grid;grid-template-columns:1.2fr 1.2fr 1fr;gap:10px;margin:12px 0 6px;}
.v2-figures small {display:block;font-size:9px;color:#6a8194;letter-spacing:.04em;}
.v2-figures b {font-size:21px;color:#18364a;display:block;margin-top:4px;}
.v2-variance {font-size:11px;color:#a05f34;background:#fbf5ef;padding:8px 10px;border-radius:5px;}
.v2-variance span {color:#7f8f9c;}.v2-period {font-size:11px;color:#647b8d;margin-bottom:6px;}
.v2-rule {height:1px;background:#e2e9ef;margin:12px 0;}
.gp-guard {margin:12px 0 15px;padding:10px 14px;font-size:11px;}
.gp-note {font-size:10px;margin:12px 0;}
.prose {font-size:13px;line-height:1.6;}
@media(max-width:1100px) {.v2-figures {grid-template-columns:1fr;}.v2-figures>div {display:flex;align-items:center;justify-content:space-between;}.v2-figures b {font-size:18px;}}
@media(max-width:800px) {.block-container {padding:3.2rem 1rem 2rem;}.gp-stats {grid-template-columns:repeat(2,1fr);}.v2-figures {grid-template-columns:repeat(3,1fr);}.v2-figures>div {display:block;}}
@media(max-width:420px) {.gp-stats {gap:8px;}.gp-stat {padding:12px;}.gp-stat strong {font-size:24px;}.v2-frequency {font-size:8px;}}
</style>'''


def navigate(page, company=None, finding=None):
    if page == 'company' and company and company != st.query_params.get('company'):
        for key in ('gp_company_route','gp_company_tab','selected','gp_selected_finding','export','custom','gp_company_format','gp_company_template'):
            st.session_state.pop(key, None)
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
        for label, destination in [('Portfolio Overview', 'overview'), ('Company Comparison', 'comparison'), ('Investment Issues', 'issues'), ('Company Detail', 'company'), ('Excel Reports', 'excel')]:
            st.button(label, key='nav_watchlist' if destination == 'issues' else 'nav_'+destination, type='primary' if page == destination else 'secondary', width='stretch',
                      on_click=navigate, args=(destination, st.query_params.get('company', companies[0].id)) if destination == 'company' else (destination,))
        ids = [c.id for c in companies]
        current = st.query_params.get('company', ids[0])
        current = current if current in ids else ids[0]
        if st.session_state.get('gp_sidebar_company') != current:
            st.session_state.gp_sidebar_company = current
        st.selectbox('Open company', ids, format_func=lambda slug: next(c.name for c in companies if c.id == slug),
                     key='gp_sidebar_company', on_change=select_company, args=('gp_sidebar_company',))
        st.divider()
        st.caption('Synthetic demonstration only')
        st.caption('Prepared results · 0 new model calls')
    names = {'overview': 'Overview', 'issues': 'Investment Issues', 'watchlist': 'Investment Issues', 'comparison':'Company Comparison', 'company': 'Company Detail', 'excel': 'Excel Reports'}
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
    stats(companies)
    st.subheader('Operating performance')
    st.caption('Reported EBITDA: Actual vs Budget · Each chart has its own dollar axis and period. Annual and monthly amounts are never pooled.')
    for column, company in zip(st.columns(len(companies)), companies):
        with column:
            company_card(company)
    render_comparison(companies)
    st.markdown('<div class="gp-guard">'+escape(COMPARABILITY)+'</div>', unsafe_allow_html=True)


def render_comparison(companies, matrix=False):
    import pandas as pd
    from portfolio_dashboard import operating_rows, comparison_matrix
    st.subheader('Company comparison')
    st.caption('Review source-period performance. Sort by a column heading; open a company above for findings and evidence.')
    if matrix:
        st.dataframe(pd.DataFrame(comparison_matrix(companies)), hide_index=True, width='stretch')
    else:
        st.dataframe(pd.DataFrame(operating_rows(companies)).drop(columns=['Company ID']), hide_index=True, width='stretch',
                     column_config={'Revenue':st.column_config.NumberColumn(format='dollar'), 'Reported EBITDA':st.column_config.NumberColumn(format='dollar'),
                        'EBITDA budget':st.column_config.NumberColumn(format='dollar'), 'EBITDA margin':st.column_config.NumberColumn(format='percent'),
                        'EBITDA vs budget':st.column_config.NumberColumn(format='percent'), 'Revenue vs budget':st.column_config.NumberColumn(format='percent')})


def footer():
    st.markdown('<div class="gp-note">Synthetic demonstration · Prepared assessments · For Investment Team Review · No new inference</div>', unsafe_allow_html=True)


def render_watchlist(companies, compact=False):
    from portfolio_watchlist import watchlist
    items = watchlist(companies)
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
    else:
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
    if compact:
        st.button('Open all investment issues →', on_click=navigate, args=('issues',))


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
