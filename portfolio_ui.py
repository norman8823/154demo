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


def navigate(page, company=None, finding=None):
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
        for label, destination in [('Portfolio Overview', 'overview'), ('Portfolio Watchlist', 'watchlist'), ('Company Detail', 'company'), ('Excel Reports', 'excel')]:
            st.button(label, key='nav_'+destination, type='primary' if page == destination else 'secondary', width='stretch',
                      on_click=navigate, args=(destination, st.query_params.get('company', companies[0].id)) if destination == 'company' else (destination,))
        st.divider()
        st.caption('Synthetic demonstration only')
        st.caption('Prepared results · 0 new model calls')
    names = {'overview': 'Overview', 'watchlist': 'Watchlist', 'company': 'Company Detail', 'excel': 'Excel Reports'}
    st.markdown('<div class="gp-breadcrumb">Portfolio / '+names.get(page, 'Overview')+'<span class="gp-tag">SYNTHETIC DATA &nbsp; · &nbsp; GP</span></div>', unsafe_allow_html=True)


def stats(companies):
    frequencies = [comparison(c)['frequency'] for c in companies]
    items = [('Investments', str(len(companies)), 'Independent portfolio companies'),
             ('Verified prepared reports', f'{len(companies)} / {len(companies)}', 'Source packages verified; interpretation requires review'),
             ('Reporting scope', f'{frequencies.count("Monthly")} monthly · {frequencies.count("Annual")} FY', 'Company figures shown separately')]
    st.markdown('<div class="gp-stats">'+''.join('<div class="gp-stat"><small>'+escape(a)+'</small><strong>'+escape(b)+'</strong><small>'+escape(c)+'</small></div>' for a,b,c in items)+'</div>', unsafe_allow_html=True)


def company_card(company):
    v = comparison(company)
    focus = company.review.package['ai_insights'][0]
    metric_html = ''
    for title, key in [('REVENUE', 'revenue'), ('REPORTED EBITDA', 'ebitda'), ('EBITDA MARGIN', 'margin')]:
        m = v[key]
        value = percent(m.actual) if key == 'margin' else money(m.actual, m.unit)
        delta = (percent(m.budget)+' budget' if m.budget is not None else 'Budget unavailable') if key == 'margin' else against_plan(m)
        color = '' if key == 'margin' or m.variance_pct is None else (' gp-adverse' if m.variance_pct < 0 else ' gp-favorable')
        metric_html += '<div class="gp-kpi"><small>'+title+'</small><strong>'+escape(value)+'</strong><div class="gp-delta'+color+'">'+escape(delta)+'</div></div>'
    with st.container(key='gp_company_'+company.id):
        st.markdown('<div class="gp-row"><div class="gp-company"><strong>'+escape(company.name)+'</strong><small>'+escape(company.sector)+'</small><div class="gp-period">'+escape(v['period_label'])+'</div><small>✓ Verified prepared review</small></div>'+metric_html+'<div class="gp-focus"><small>PRIORITY INVESTMENT ISSUE</small>'+escape(focus['title'])+'</div></div>', unsafe_allow_html=True)
        _, action = st.columns([4, 1.3])
        action.button('Open investment review →', key='open_'+company.id, width='stretch', on_click=navigate, args=('company', company.id))


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
    page_heading('Portfolio Overview', 'Three investments · September 2026 / FY2026 reporting · prepared company analyses', workbook_data)
    stats(companies)
    st.subheader('Company performance')
    for company in companies:
        company_card(company)
    st.markdown('<div class="gp-guard">'+escape(COMPARABILITY)+'</div>', unsafe_allow_html=True)


def footer():
    st.markdown('<div class="gp-note">Synthetic demonstration · Prepared assessments · For Investment Team Review · No new inference</div>', unsafe_allow_html=True)


def render_watchlist(companies, compact=False):
    from portfolio_watchlist import watchlist
    items = watchlist(companies)
    st.subheader('Portfolio watchlist')
    st.caption('Original analyst priority and disposition; high before medium, act now before investigate. Source order breaks ties. Findings may cite YTD, LTM or other periods beyond the headline reporting period.')
    if compact:
        # One original lead issue per company keeps the landing screen concise.
        items = [next(i for i in items if i.company_id == c.id and i.finding['id'] == c.review.package['ai_insights'][0]['id']) for c in companies]
    else:
        company_filter, priority_filter = st.columns(2)
        selected_company = company_filter.selectbox('Company', ['All companies']+[c.name for c in companies])
        selected_priority = priority_filter.selectbox('Original priority', ['All priorities', 'high', 'medium', 'low'])
        items = [i for i in items if (selected_company == 'All companies' or i.company_name == selected_company)
                 and (selected_priority == 'All priorities' or i.finding['priority'] == selected_priority)]
    st.caption(f'{len(items)} findings shown · company amounts and impacts are never summed')
    for item in items:
        f = item.finding
        with st.container(border=True):
            issue, action = st.columns([4, 1])
            issue.markdown('**'+item.company_name+' · '+f['title']+'**')
            issue.caption(item.report_period+' report · '+f['priority'].title()+' · '+f['disposition'].replace('_', ' ').title())
            if not compact:
                with issue:
                    literal_prose(f['conclusion'])
            action.button('View source evidence →', key=('lead_' if compact else 'watch_')+item.company_id+'_'+str(f['id']),
                          on_click=navigate, args=('company', item.company_id, f['id']), width='stretch')
            if not compact:
                with st.expander('Finding, management question & caveats'):
                    for label, key in [('Evidence', 'evidence'), ('Financial implication', 'financial_implication'), ('Investment assessment', 'assessment'),
                                       ('Next action', 'action'), ('Management question', 'management_question')]:
                        st.markdown('**'+label+'**')
                        literal_prose(f[key])
                    st.info(item.presentation['caveat'])
                    st.caption('Source IDs: '+', '.join(f['fact_ids']))
                    for quote in f.get('source_quotes', []):
                        literal_prose(quote['quote'])
                        st.caption('Original source quote · '+quote['source_id'])
    if compact:
        st.button('Open all portfolio findings →', on_click=navigate, args=('watchlist',))


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
