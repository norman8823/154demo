"""One workflow-readiness page over the unchanged portable v3 data package."""
import json
from html import escape
import pandas as pd
import streamlit as st
from portfolio_foundation import export_foundation
from portfolio_readiness import workflow_readiness


@st.cache_data(show_spinner=False)
def foundation_package(companies):
    return export_foundation(companies)


def _value(row):
    if row['value'] is None:
        return 'Missing'
    return f"{row['currency']} {row['value']:,.0f}"


def render_foundation(companies):
    from portfolio_ui import literal_prose
    view=workflow_readiness(companies)
    model=view['model']; assessment=view['assessment']; quality=view['quality']
    st.markdown('<style>.readiness-stats{grid-template-columns:repeat(3,minmax(0,1fr));}.readiness-stats .score-text{font-size:23px;}@media(max-width:650px){.readiness-stats{grid-template-columns:1fr;}}</style>',unsafe_allow_html=True)
    st.title('AI Workflow Automation Readiness')
    st.markdown('**'+model['name']+'**')
    st.markdown('**Flexible company inputs → GP-defined model → Source-linked structured data → Multiple applications**')
    st.caption('Synthetic company data · Existing verified Review records · No new extraction or model calls')
    coverage=f"{assessment['coverage']:.0%}" if assessment['coverage'] is not None else 'Not Evaluated'
    items=[('Readiness Score',assessment['score_status'],'Partial evidence; comprehensive reconciliation not evaluated'),
           ('Mapping Coverage',coverage,f"{assessment['monthly_slots']}/{assessment['required_slots']} required monthly slots · {assessment['mapped_slots']}/{assessment['required_slots']} mapped at source frequency"),
           ('Data Issues',str(assessment['issue_groups']),f"Review groups · {quality['unresolved_mappings']} unresolved rows / {quality['blank_observations']} blanks retained")]
    st.markdown('<div class="gp-stats readiness-stats">'+''.join('<div class="gp-stat"><small>'+escape(a)+'</small><strong class="'+('score-text' if a=='Readiness Score' else '')+'">'+escape(b)+'</strong><small>'+escape(c)+'</small></div>' for a,b,c in items)+'</div>',unsafe_allow_html=True)
    with st.expander('GP data model and assessment methodology'):
        st.caption('JSON configuration · '+model['model_id']+' · version '+model['version']+' · requested '+model['target_period']+' / '+model['period_grain'])
        st.dataframe(pd.DataFrame([{'GP target':m['label'],'Stable ID':m['metric_id'],'Required':m['required'],'Scenarios':', '.join(m['scenarios']),'Definition':m['definition']} for m in model['metrics']]),hide_index=True,width='stretch')
        st.dataframe(pd.DataFrame(assessment['checks']),hide_index=True,width='stretch')
        literal_prose(assessment['limitation'])
        st.caption('A slot is one company × required metric × scenario. Coverage additionally requires the configured period, grain, accepted mapping, checked numeric source and required context. Accounting basis is optional and unknowns are retained. Original currency labels are not FX-standardized.')
        st.caption('Source verification, automatic mapping acceptance and documented human approval are separate states. Human mapping approval: not recorded. Known issues are a curated, non-exhaustive queue; overlapping groups are not additive observation counts.')
        st.json(model,expanded=False)

    st.subheader('Data Mapping')
    st.caption('Different company reports → Common financial definitions')
    company_filter,metric_filter,scenario_filter,period_filter=st.columns([2,1.2,1,1])
    selected=company_filter.selectbox('Company',['All companies']+[c.name for c in companies],key='foundation_company')
    metric=metric_filter.selectbox('Metric',['All metrics']+[m['label'] for m in model['metrics']],key='foundation_metric')
    scenario=scenario_filter.selectbox('Scenario',['All scenarios','actual','budget'],key='foundation_scenario')
    period=period_filter.selectbox('Period',['All periods']+list(dict.fromkeys(r['period'] for r in view['mappings'])),key='foundation_period')
    rows=[r for r in view['mappings'] if (selected=='All companies' or r['company_name']==selected) and (scenario=='All scenarios' or r['scenario']==scenario) and (metric=='All metrics' or r['target_label']==metric) and (period=='All periods' or r['period']==period)]
    table=[{'Company':r['company_name'],'Original Source':r['lineage']['source_reference'],
            'GP Target Metric':r['target_label'],'Period':r['period']+' · '+r['period_grain']+' · '+r['scenario'],
            'Standardized Value':_value(r),'Status':r['status']} for r in rows]
    st.dataframe(pd.DataFrame(table,columns=['Company','Original Source','GP Target Metric','Period','Standardized Value','Status']),hide_index=True,width='stretch',height=38+28*len(rows),row_height=28)
    st.caption(f"{len(rows)} source-backed mappings shown · Annual Harrow values remain annual and do not satisfy the monthly requirement. No pooled financial total.")
    if rows:
        with st.expander('Inspect a mapping and its source evidence'):
            by_id={r['fact_key']:r for r in rows}
            # Filter changes may remove the previously selected fact.
            if st.session_state.get('foundation_mapping') not in by_id:
                st.session_state.pop('foundation_mapping',None)
            identity=st.selectbox('Mapping source',list(by_id),format_func=lambda key:by_id[key]['company_name']+' · '+by_id[key]['target_label']+' · '+by_id[key]['scenario']+' · '+by_id[key]['workbook_reference'],key='foundation_mapping')
            row=by_id[identity]; origin=row['lineage']
            source,target=st.columns(2)
            with source:
                st.markdown('**Original company input**')
                literal_prose(origin['canonical_workbook'])
                literal_prose(origin['source_reference']+' · '+row['source_label'])
                literal_prose('Original value: '+str(row['raw_source_value'])+' · Source scale: '+str(row['source_scale']))
                formula=json.loads(origin['original_formula_json'])
                if formula:
                    st.code(formula,language=None)
                st.caption('Original formula text is provenance only; it is not executed.')
            with target:
                st.markdown('**GP-standardized output**')
                literal_prose(row['metric_id']+' · '+_value(row)+' · unit: '+row['unit'])
                literal_prose(row['target_definition'])
                literal_prose('Retained normalization: original value × '+str(row['source_scale'])+' × sign '+str(row['sign_adjustment'])+'. No FX or period conversion.')
            st.caption('Entity: '+row['entity_name']+' · '+row['period']+' / '+row['period_grain']+' / '+row['scenario']+' · Accounting basis: '+row['accounting_basis'])
            st.caption('Source: '+row['verification_status']+' · Mapping: '+row['mapping_status']+' · Human approval: '+row['human_approval_status'])
            st.caption('Source ID: '+identity+' · Workbook SHA-256: '+row['workbook_sha256'])

    issues_column,export_column=st.columns([1.5,1],gap='large')
    with issues_column:
        _render_issues(companies,view['issues'])
    with export_column:
        _render_export(companies,quality)


def _render_issues(companies,all_issues):
    from portfolio_ui import literal_prose, navigate
    st.subheader('Data Issues')
    st.caption('Mapping ambiguities, reconciliation differences and missing information. Known review groups; not a complete audit.')
    for company in companies:
        issues=[i for i in all_issues if i['company_id']==company.id]
        if not issues:
            continue
        st.markdown('**'+company.name+'**')
        for issue in issues:
            label=issue['status']+' · '+issue['title']
            if issue.get('impact'):
                label+=' · '+issue['impact']
            with st.expander(label):
                literal_prose(issue['problem'])
                st.markdown('**Why it matters**')
                literal_prose(issue['why'])
                st.markdown('**Next investigation**')
                literal_prose(issue['action'])
                st.caption(issue['caveat'])
                # Put the operands and values before long filenames so the
                # calculation is readable in the compact issues column.
                evidence=[]
                for e in issue['evidence']:
                    value=e.get('Validated value',e.get('standardized_value'))
                    evidence.append({'Source ID':e.get('Fact ID',e.get('source_id')),
                                     'Reference / calculation':e.get('Reference',e.get('reference')),
                                     'Checked value':'Missing' if value is None else f'{value:,.2f}',
                                     'Original value / formula':str(e.get('Original value / formula',e.get('original_value'))),
                                     'Mapping / check':e.get('Check / use',e.get('mapping_status'))})
                st.caption('Source workbook: '+str(issue['evidence'][0].get('File',issue['evidence'][0].get('workbook'))))
                st.dataframe(pd.DataFrame(evidence),hide_index=True,width='stretch',height=min(290,38+28*len(evidence)),row_height=28)
                if issue['finding_id'] is not None:
                    st.button('Open original finding & evidence',key='foundation_issue_'+issue['id'],on_click=navigate,args=('company',company.id,issue['finding_id']))



def _render_export(companies,quality):
    st.subheader('Structured Data Export')
    st.write('This structured data package can be consumed independently of the investment dashboard, without application modules, original workbooks, network access or an AI model.')
    st.download_button('↓ Download AI-ready data package',foundation_package(companies),file_name='AI_Ready_Operating_Data_v1.zip',mime='application/zip',type='primary',key='gp_data_download')
    st.caption(f"Unchanged six-file v3 package · {quality['normalized_observations']:,} observations · {quality['source_observations_verified']:,} checked numeric values · {quality['unresolved_mappings']} unresolved mapping rows · {quality['blank_observations']} blanks · Investment ledger excluded")
    st.caption('Potential Downstream Uses: Investment Monitoring · Underwriting · Due Diligence · Portfolio Operations · Expense Benchmarking · Compliance')
    st.caption('financial_facts.csv · metric_definitions.json · source_lineage.csv · quality_report.json · example_consumer.py · README.md')
    with st.expander('Independent reuse and package contents'):
        st.code('python3 example_consumer.py',language='sh')
        st.write('financial_facts.csv · metric_definitions.json · source_lineage.csv · quality_report.json · example_consumer.py · README.md')
        st.write('The workflow-standardized subset above serves this reporting intake. The broader package preserves historical periods, supporting observations, unresolved classifications, blanks and original lineage for other consumers.')
        st.caption('Potential uses are not implemented or validated downstream workflows. New reporting cycles, persistent approved mappings and exhaustive source extraction are not automated. Collect once, structure carefully, reuse across workflows.')
