"""Reuse the frozen monolithic app's presentation functions without its entrypoint.

app.py is hash-pinned by prepared verification and executes setup at import time.
Compile only these allowlisted UI function definitions from that verified source;
never execute its module body, credential loader, compute or upload functions.
This small compatibility boundary can become normal imports after the freeze.
"""
import ast
from functools import lru_cache
from html import escape
import pandas as pd
import streamlit as st
from engine import ROOT, NOT_AVAILABLE, company_name
from executive import present, money as executive_money, pp
from card_presentation import finding_html, card_metric
from package_analysis import analysis_findings
from portfolio_comparison import comparison
from portfolio_ui import navigate, company_selector
from portfolio_tables import CompanyPresentation

UI_FUNCTIONS = frozenset({'download', 'prose', 'readiness', 'money', 'overview', 'evidence_view'})


def company_go(view, finding=None):
    page = 'evidence' if view == '03  Evidence & Excel' else 'summary'
    st.session_state.gp_company_tab = page
    params = dict(st.query_params)
    if finding is not None:
        params['finding'] = str(finding)
        st.session_state.selected = finding
        st.session_state.gp_selected_finding = finding
    elif st.session_state.get('gp_selected_finding') is not None:
        params['finding'] = str(st.session_state.gp_selected_finding)
        st.session_state.selected = st.session_state.gp_selected_finding
    # Preserve an existing finding route for generic evidence actions. Removing
    # it makes render_company interpret the action as a fresh summary route.
    st.query_params.from_dict(params)


@lru_cache(maxsize=1)
def existing_views():
    path = ROOT / 'app.py'
    tree = ast.parse(path.read_text(), filename=str(path))
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in UI_FUNCTIONS]
    if {d.name for d in definitions} != UI_FUNCTIONS:
        raise ValueError('Frozen company presentation contract changed.')
    namespace = dict(st=CompanyPresentation(), pd=pd, escape=escape, NOT_AVAILABLE=NOT_AVAILABLE, company_name=company_name,
                     present=present, executive_money=executive_money, pp=pp, finding_html=finding_html,
                     analysis_findings=analysis_findings, go=company_go)
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def render_company(company, companies=None, perf=None):
    r = company.review
    v = comparison(company)
    if companies:
        company_selector(companies, company.id)
    # Reset widget state only when the company/finding route changes.
    route = (company.id, st.query_params.get('finding'))
    if st.session_state.get('gp_company_route') != route:
        st.session_state.gp_company_route = route
        st.session_state.gp_company_tab = 'summary'
        try:
            requested = int(route[1]) if route[1] else None
        except ValueError:
            requested = None
        valid_ids = {f['id'] for f in analysis_findings(r)}
        st.session_state.selected = requested if requested in valid_ids else next(iter(valid_ids))
        st.session_state.gp_selected_finding = st.session_state.selected
    # CSS chooses the existing complete report or the concise phone view.
    # Both share the exact company/route; resizing never changes navigation state.
    with st.container(key='desktop_company_detail'):
        _render_desktop_company(company,r,v,companies or (company,),perf=perf)
    from portfolio_mobile_detail import render_mobile_detail
    render_mobile_detail(company)


def _render_desktop_company(company,r,v,companies,perf=None):
    st.button('← Portfolio Overview', on_click=navigate, args=('overview',))
    st.title('Investment Detail')
    st.markdown('<h2 class="investment-company-name">'+escape(company.name)+'</h2>',unsafe_allow_html=True)
    st.caption(company.sector+' · '+v['period_label']+' · Verified prepared review')
    from portfolio_outlook import render_outlook
    render_outlook(company)
    render_company_summary(company)
    # The portfolio demo exposes only the standard, prepared company report.
    from portfolio_report_assets import report_asset
    if perf is None:
        data_bytes, filename, warnings = report_asset(company.id, companies)
    else:
        with perf.measure('company_report_asset_verification_and_disk_read'):
            data_bytes, filename, warnings = report_asset(company.id, companies)
    st.session_state.export = (data_bytes, filename, warnings)
    for warning in warnings: st.caption(warning)
    from portfolio_ui import generated_excel_download
    generated_excel_download('Download Excel',data_bytes,filename,'company_download')


def render_company_summary(company):
    """Prepared summary/findings only; original-cell inspection stays contextual."""
    from portfolio_ui import literal_prose
    from portfolio_document_ui import evidence_actions
    r=company.review;summary=present(r)
    st.subheader('Investment Summary')
    description=r.package.get('company_profile',{}).get('description')
    if description: literal_prose(description)
    metrics=r.metrics
    values=[('Revenue',executive_money(r,metrics['revenue'])),
            ('EBITDA',executive_money(r,metrics['ebitda'])),
            ('Gross margin',f"{metrics['gm']:.1%}")]
    for column,(label,value) in zip(st.columns(3),values): column.metric(label,value)
    st.subheader('Priority findings')
    originals={f['id']:f for f in r.package['ai_insights']}
    cards=summary['cards']+summary.get('secondary',[])
    for card in cards:
        finding=originals[card['id']]
        with st.container(border=True,key='finding_panel_'+str(card['id'])):
            impact,_=card_metric(card,r)
            st.markdown('<div class="finding-brief"><div class="finding-labels"><span class="finding-priority">'+escape(finding['priority'].title())+' priority</span><span class="badge">'+escape(card['kind'])+'</span></div><div class="finding-title-row"><h3>'+escape(card['title'])+'</h3>'+('<strong class="finding-impact">'+escape(impact)+'</strong>' if impact else '')+'</div></div>',unsafe_allow_html=True)
            with st.container(key='finding_analysis_'+str(card['id'])):
                literal_prose(card['summary'])
            with st.container(key='finding_followup_'+str(card['id'])):
                st.markdown('**Follow Up**')
                literal_prose(finding['action'])
                st.markdown('**Question for management**')
                literal_prose(finding['management_question'])
            evidence_actions(company,finding['fact_ids'],
                'company_source_'+company.id+'_'+str(card['id']),
                show_calculations=False,show_picker=False,show_notices=False)
