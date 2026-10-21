"""Presentation-only workflow page over the unchanged v3 data contracts."""
import json
from html import escape
from pathlib import Path
import pandas as pd
import streamlit as st
from portfolio_foundation import export_foundation
from portfolio_readiness import workflow_readiness
from portfolio_tables import responsive_table,json_records


@st.cache_data(show_spinner=False)
def foundation_package(companies):
    return export_foundation(companies)


def _value(row):
    if row['value'] is None:return 'Missing'
    if row['metric_id']=='unmapped.source_observation':return f"{row['value']:,.4g} (retained value)"
    if row['unit']=='ratio':return f"{row['value']:.2%}"
    separator='' if row['currency']=='$' else ' '
    return f"{row['currency']}{separator}{row['value']:,.0f}"


def _badge(text,kind='review'):
    return '<span class="foundation-badge '+kind+'">'+escape(text)+'</span>'


def _fields(items):
    return '<dl>'+''.join('<dt>'+escape(k)+'</dt><dd>'+escape(str(v))+'</dd>' for k,v in items)+'</dl>'


def render_foundation(companies):
    st.markdown('<style>'+Path(__file__).with_name('portfolio_foundation.css').read_text()+'</style>',unsafe_allow_html=True)
    view=workflow_readiness(companies)
    with st.container(key='foundation_page'):
        title,badge=st.columns([5,1])
        with title:
            st.title('AI Workflow Automation Readiness')
            st.markdown('<div class="foundation-subtitle">'+escape(view['model']['name'])+'</div>',unsafe_allow_html=True)
        badge.markdown('<span class="foundation-demo">ⓘ &nbsp; Synthetic Demo Data</span>',unsafe_allow_html=True)
        st.markdown('<div class="foundation-intro">Different company reports map to common financial definitions, with source checks and reusable structured output for other workflows.</div>',unsafe_allow_html=True)
        _render_summary(view)
        st.markdown('<div class="foundation-scope"><span class="foundation-scope-icon">i</span><div><strong>Scope: '+escape(view['model']['name'])+'</strong>Measured mapping coverage and source verification for this workflow; no company-wide AI maturity score.</div><a href="#foundation-model">View workflow configuration &nbsp; →</a></div>',unsafe_allow_html=True)
        with st.container(key='foundation_mapping_panel'):
            _render_mapping(companies,view)
        issues,export=st.columns([1.65,1],gap='small')
        with issues,st.container(key='foundation_issues'):
            _render_issues(companies,view['issues'])
        with export,st.container(key='foundation_export'):
            _render_export(companies,view['quality'])
        _render_methodology(view)


def _render_summary(view):
    a=view['assessment'];q=view['quality']
    coverage=f"{a['coverage']:.0%}" if a['coverage'] is not None else 'Not Evaluated'
    progress=100*a['coverage'] if a['coverage'] is not None else 0
    st.markdown('<div class="foundation-kpis">'
        '<div class="foundation-kpi"><div class="foundation-kpi-head"><span class="foundation-kpi-value">'+escape(a['score_status'])+'</span><span class="foundation-kpi-label">Workflow Readiness</span></div><div class="foundation-progress readiness"><span style="width:'+str(a['score'] or 0)+'%"></span></div><div class="foundation-kpi-note">Illustrative workflow assessment.</div><div class="foundation-kpi-foot">Weighted evidence checks · methodology below</div></div>'
        '<div class="foundation-kpi"><div class="foundation-kpi-head"><span class="foundation-kpi-value">'+coverage+'</span><span class="foundation-kpi-label">Monthly Intake Coverage</span></div><div class="foundation-progress"><span style="width:'+str(progress)+'%"></span></div><div class="foundation-kpi-note">'+str(a['monthly_slots'])+' of '+str(a['required_slots'])+' required monthly metric / scenario slots</div><div class="foundation-kpi-foot">'+str(a['mapped_slots'])+'/'+str(a['required_slots'])+' mapped at original source frequency</div></div>'
        '<div class="foundation-kpi"><div class="foundation-kpi-head"><span class="foundation-kpi-value issues">'+str(a['issue_groups'])+'</span><span class="foundation-kpi-label">Data Issues</span></div><div class="foundation-kpi-note" style="margin-top:9px">Evidence-backed review groups · remain open</div><div class="foundation-kpi-foot">'+str(q['unresolved_mappings'])+' unresolved mapping rows · '+str(q['blank_observations'])+' blanks retained</div></div></div>',unsafe_allow_html=True)


def _render_mapping(companies,view):
    from portfolio_catalog import catalog_entries,catalog_detail,GRAINS
    entries=catalog_entries(view['facts'],view['lineage'],view['model'])
    index={e['metric_id']:e for e in entries}
    st.subheader('Data Catalog & Dictionary')
    st.caption('Data Foundation: the broader reusable asset. Monthly Portfolio Operating Review: one workflow requesting Revenue and Reported EBITDA actual / budget at monthly frequency.')
    st.markdown('<div class="foundation-flow"><div><strong>Company Inputs</strong><span>Summit · Tallis · Harrow</span>Different reporting packages, worksheets and labels; original extraction evidence retained.</div><div><strong>Standardization &amp; Validation</strong><span>GP dictionary + source mappings</span>Periods, scenarios, units, source checks and unresolved classifications remain explicit.</div><div><strong>Structured Data</strong><span>'+format(len(view['facts']),',')+' normalized observations</span>Versioned CSV / JSON, original provenance and independent downstream reuse.</div></div>',unsafe_allow_html=True)
    identity=st.selectbox('Data element',list(index),format_func=lambda k:index[k]['label']+' · '+str(index[k]['observations'])+' observations',key='foundation_metric')
    entry=index[identity]
    with st.expander('Browse catalog · '+str(len(entries))+' data elements'):
        responsive_table(pd.DataFrame([{'Data element':e['label'],'Observations':e['observations'],'Accepted automatic mappings':str(e['accepted'])+'/'+str(e['observations']),'Numeric source checks':str(e['verified'])+'/'+str(e['observations'])} for e in entries]),key='foundation_catalog',page_size=10,details=False)
        st.caption('Retained financial categories include account detail, subtotals and repeated presentations; they must not be summed blindly. Source checking does not establish semantic mapping acceptance.')
    st.markdown('<div class="foundation-definition"><strong>'+escape(entry['label'])+'</strong><p>'+escape(entry['definition'])+'</p><small>'+escape(entry['metric_id'])+' · '+escape(entry['category'])+'</small></div>',unsafe_allow_html=True)
    if entry['workflow_definition']:st.caption('GP workflow requirement: '+entry['workflow_definition'])
    with st.expander('Dictionary conventions and stewardship'):
        latest='; '.join(GRAINS.get(g,g)+': '+periods[-1] for g,periods in entry['periods'].items())
        st.markdown(_fields([('Retained units / currency',', '.join(entry['units'])+' / '+', '.join(entry['currencies'])),('Source scaling',', '.join(entry['scales'])+' ×; retained sign adjustments shown in source detail'),('Measurement basis','; '.join(entry['basis'])),('Most recent period by grain',latest),('Data owner',entry['owner']),('Expected delivery / refresh cadence',entry['refresh_cadence']),('Approval authority',entry['approval_authority']),('Source lineage',str(entry['lineage_available'])+'/'+str(entry['observations'])+' records'),('Source packages','; '.join(entry['packages']))]),unsafe_allow_html=True)
        st.caption('Reporting frequency describes the package; measurement basis describes the observation. Neither establishes a delivery schedule. Original unit tags are retained, including unknowns; unmapped supporting measures have no common approved unit or meaning. No LTM, YTD or annualization is inferred from monthly grain.')
    sources=[]
    for company in companies:
        own=[r for r in entry['rows'] if r['company_id']==company.id]
        if not own:continue
        selected=[r for r in own if r['comparison_selected'] and r['scenario']=='actual']
        labels=sorted({r['source_label'] for r in selected or own})
        headline=[r for r in view['facts'] if r['company_id']==company.id and r['comparison_selected']]
        frequency=', '.join(sorted({GRAINS.get(r['period_grain'],r['period_grain']) for r in headline}))
        bases=sorted({GRAINS.get(r['period_grain'],r['period_grain']) for r in own})
        sources.append({'Company':company.name,'Reported as':'; '.join(labels),'Reporting conventions':frequency+' package · observations: '+', '.join(bases)})
    responsive_table(pd.DataFrame(sources),key='foundation_sources',page_size=3,details=False,css_class='gp-catalog-sources')
    st.caption(f"{entry['observations']} observations · {entry['accepted']} accepted automatic mappings · {entry['verified']} numeric source checks · Human approval: not recorded")
    with st.expander('Inspect company mapping and source evidence',expanded=True):
        company_filter,scenario_filter,period_filter=st.columns([2,1,1.4])
        owners=[c.name for c in companies if any(r['company_id']==c.id for r in entry['rows'])]
        if st.session_state.get('foundation_company') not in ['All companies']+owners:st.session_state.foundation_company='All companies'
        selected=company_filter.selectbox('Company',['All companies']+owners,key='foundation_company')
        scenario=scenario_filter.selectbox('Scenario',['All scenarios','actual','budget'],key='foundation_scenario')
        periods=['All periods']+sorted({r['period'] for r in entry['rows']},reverse=True)
        if st.session_state.get('foundation_period') not in periods:st.session_state.foundation_period='All periods'
        period=period_filter.selectbox('Period',periods,key='foundation_period')
        rows=[r for r in entry['rows'] if (selected=='All companies' or r['company_name']==selected) and (scenario=='All scenarios' or r['scenario']==scenario) and (period=='All periods' or r['period']==period)]
        rows.sort(key=lambda r:(not r['comparison_selected'],r['scenario']!='actual',next(i for i,c in enumerate(companies) if c.id==r['company_id'])))
        if not rows:st.info('No source observations match these filters.')
        else:
            by_id={r['fact_key']:r for r in rows}
            if st.session_state.get('foundation_mapping') not in by_id:st.session_state.foundation_mapping=next(iter(by_id))
            fact=st.selectbox('Mapping source',list(by_id),format_func=lambda key:by_id[key]['company_name']+' · '+by_id[key]['source_label']+' · '+by_id[key]['period']+' · '+by_id[key]['scenario']+' · '+by_id[key]['workbook_reference'],key='foundation_mapping')
            _render_detail(catalog_detail(by_id[fact],view['lineage'],view['model']))


def _render_detail(row):
    origin=row['lineage'];formula=json.loads(origin['original_formula_json'])
    source=_fields([('Workbook',Path(origin['canonical_workbook']).name),('Worksheet',origin['source_sheet']),('Cell',origin['source_cell']),('Source label',row['source_label']),('Original value',str(row['raw_source_value']))])
    if formula:source+='<div style="margin-top:8px"><code>'+escape(formula)+'</code></div>'
    transformation=_fields([('GP target',row['target_label']),('Metric ID',row['metric_id']),('Period',row['period']+' · '+row['period_grain']),('Measurement basis',row.get('measurement_basis',row['period_grain'])),('Scenario',row['scenario']),('Scale / sign',str(row['source_scale'])+' × '+str(row['sign_adjustment'])),('Unit / currency',row['unit']+' / '+row['currency'])])
    status=_badge('Source checked','checked') if row['verification_status']=='source_observation_verified' else _badge('Source review required')
    mapping=_badge('Auto-mapped','checked') if row['mapping_accepted'] else _badge('Mapping review required')
    output='<div class="foundation-output">'+escape(_value(row))+'</div>'+status+' '+mapping
    if row['metric_id']=='unmapped.source_observation':output+=' '+_badge('No canonical financial meaning')
    if not row['monthly_scope_matches']:output+=' '+_badge('Outside monthly workflow scope')
    output+='<div class="foundation-export-copy" style="margin-top:8px">'+escape(row['target_definition'])+'</div>'
    st.markdown('<div class="foundation-detail-grid"><div class="foundation-detail"><h4>Original company input</h4>'+source+'</div><div class="foundation-detail"><h4>Normalization &amp; transformation</h4>'+transformation+'</div><div class="foundation-detail"><h4>GP-standardized output</h4>'+output+'</div></div>',unsafe_allow_html=True)
    st.caption('Entity: '+row['entity_name']+' · Accounting basis: '+row['accounting_basis']+' · Human approval: '+row['human_approval_status'])
    with st.expander('Full lineage and formula provenance'):
        st.caption('Source: '+row['verification_status']+' · Mapping: '+row['mapping_status'])
        st.caption('Source ID: '+row['fact_key']+' · Workbook SHA-256: '+row['workbook_sha256'])
        st.caption('Original workbook: '+origin['canonical_workbook']+' · '+origin['source_reference'])
        st.caption('Retained normalization: original value × '+str(row['source_scale'])+' × sign '+str(row['sign_adjustment'])+'. No FX or period conversion. Formula text is provenance only and is not executed.')


def _render_issues(companies,all_issues):
    from portfolio_ui import literal_prose,navigate
    st.subheader('Data Issues')
    st.caption('Mapping ambiguities, reconciliation differences and missing information')
    for company in companies:
        issues=[i for i in all_issues if i['company_id']==company.id]
        if not issues:continue
        blocked=any(i['status']=='Blocked' for i in issues)
        st.markdown('<div class="foundation-company">'+escape(company.name)+_badge('Blocked for monthly intake' if blocked else 'Review Required','blocked' if blocked else 'review')+'</div>',unsafe_allow_html=True)
        for issue in issues:
            label=issue['status']+' · '+issue['title']
            if issue.get('impact'):label+=' · '+issue['impact']
            with st.expander(label):
                literal_prose(issue['problem'])
                st.markdown('**Why it matters**');literal_prose(issue['why'])
                st.markdown('**Next investigation**');literal_prose(issue['action'])
                st.caption(issue['caveat'])
                evidence=[]
                for e in issue['evidence']:
                    value=e.get('Validated value',e.get('standardized_value'))
                    evidence.append({'Source ID':e.get('Fact ID',e.get('source_id')),'Reference / calculation':e.get('Reference',e.get('reference')),
                                     'Checked value':'Missing' if value is None else f'{value:,.2f}',
                                     'Original value / formula':str(e.get('Original value / formula',e.get('original_value'))),
                                     'Mapping / check':e.get('Check / use',e.get('mapping_status'))})
                st.caption('Source workbook: '+str(issue['evidence'][0].get('File',issue['evidence'][0].get('workbook'))))
                responsive_table(pd.DataFrame(evidence),key='issue_records_'+issue['id'],page_size=10,details=True)
                if issue['finding_id'] is not None:
                    st.button('Open original finding & evidence',key='foundation_issue_'+issue['id'],on_click=navigate,args=('company',company.id,issue['finding_id']))
    st.caption('Known review groups, not a complete audit. Overlapping groups are not additive observation counts.')


def _render_export(companies,quality):
    st.subheader('Structured Data Export')
    st.markdown('<div class="foundation-export-copy">Consume the structured data independently of this dashboard, without original workbooks, network access or an AI model.</div>',unsafe_allow_html=True)
    files=[('financial_facts.csv',f"{quality['normalized_observations']:,} observations"),('metric_definitions.json','Versioned semantic definitions'),('source_lineage.csv','Workbook / cell lineage'),('quality_report.json','Verification & mapping states'),('example_consumer.py','Standalone comparison'),('README.md','Usage & limitations')]
    st.markdown('<div class="foundation-files">'+''.join('<b>▤ &nbsp;'+escape(name)+'</b><span>'+escape(note)+'</span>' for name,note in files)+'</div>',unsafe_allow_html=True)
    st.download_button('↓ Download AI-ready data package',foundation_package(companies),file_name='AI_Ready_Operating_Data_v1.zip',mime='application/zip',type='primary',key='gp_data_download',width='stretch')
    st.caption(f"{quality['source_observations_verified']:,} numeric source checks · {quality['unresolved_mappings']} unresolved mapping rows · {quality['blank_observations']} blanks preserved")
    st.markdown('<div class="foundation-uses"><strong>Potential Downstream Uses</strong>Investment Monitoring · Underwriting · Due Diligence · Portfolio Operations · Expense Benchmarking · Compliance</div>',unsafe_allow_html=True)
    with st.expander('Independent reuse and package contents'):
        st.code('python3 example_consumer.py',language='sh')
        st.caption('The unchanged six-file v3 package preserves historical periods, supporting observations, unresolved classifications, blanks and lineage. Investment-ledger assumptions are excluded.')
        st.caption('These are potential uses, not implemented downstream workflows. New reporting cycles, persistent approved mappings and exhaustive source extraction are not automated. Collect once, structure carefully, reuse across workflows.')


def _render_methodology(view):
    from portfolio_ui import literal_prose
    model=view['model'];a=view['assessment']
    st.markdown('<div id="foundation-model"></div>',unsafe_allow_html=True)
    with st.expander('GP data model and assessment methodology'):
        st.caption('JSON configuration · '+model['model_id']+' · version '+model['version']+' · requested '+model['target_period']+' / '+model['period_grain'])
        responsive_table(pd.DataFrame([{'GP target':m['label'],'Stable ID':m['metric_id'],'Required':m['required'],'Scenarios':', '.join(m['scenarios']),'Definition':m['definition']} for m in model['metrics']]),key='foundation_model')
        components=pd.DataFrame(a['components'])
        responsive_table(components,key='foundation_score',formatters={'Points':lambda v:f'{v:.2f}' if v is not None else 'Not Evaluated'},details=False)
        st.caption('Total '+str(a['score'])+'/100 · Sum unrounded component points, then round to the nearest integer (exact halves up).')
        responsive_table(pd.DataFrame(a['checks']),key='foundation_checks')
        literal_prose(a['limitation'])
        st.caption('One slot = company × required metric × scenario. Coverage requires the configured period and frequency, accepted mapping, checked numeric source and required context. Accounting basis is optional; unknowns and original currency labels remain unchanged.')
        st.caption('Source verification, automatic mapping acceptance and documented human approval are separate. Human mapping approval: not recorded. The illustrative weighted score covers only the listed evidence checks; comprehensive reconciliation remains incomplete. Known issues remain visible regardless of score.')
        json_records(model,key='foundation_model_json')
