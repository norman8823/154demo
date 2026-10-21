"""The portable handoff page; no new normalization, approval or model workflow."""
import io
import json
import zipfile
from html import escape
import pandas as pd
import streamlit as st
from portfolio_foundation import foundation_records, export_foundation


@st.cache_data(show_spinner=False)
def foundation_package(companies):
    return export_foundation(companies)


def render_foundation(companies):
    from portfolio_ui import page_heading
    page_heading('Data Foundation','Approved Excel packages → Verified normalized records → Reusable data → Prepared AI review')
    st.caption('Synthetic company operating data · Existing approved Review contracts · 0 new model calls · Investment-ledger assumptions excluded')
    facts,lineage,quality=foundation_records(companies)
    items=[('Normalized observations',quality['normalized_observations'],'All retained history, scenarios and account roles'),
           ('Checked numeric observations',quality['source_observations_verified'],'Source values match retained verification records'),
           ('Unresolved mappings',quality['unresolved_mappings'],'Classification remains open despite source traceability'),
           ('Human-approved mappings',quality['human_approved_mappings'],'No explicit mapping sign-off evidence recorded')]
    st.markdown('<div class="gp-stats">'+''.join('<div class="gp-stat"><small>'+escape(label)+'</small><strong>'+str(value)+'</strong><small>'+escape(note)+'</small></div>' for label,value,note in items)+'</div>',unsafe_allow_html=True)
    st.info('Source verification, automatic mapping acceptance and human approval are distinct. This package preserves unresolved classifications, unknown accounting bases and '+str(quality['blank_observations'])+' blank observations. No persistent analyst-approved mapping reuse or fully automated reporting cycle is claimed.')
    data=foundation_package(companies)
    action,description=st.columns([1,2])
    action.download_button('↓ Download AI-ready data package',data,file_name='AI_Ready_Operating_Data_v1.zip',mime='application/zip',type='primary',width='stretch',key='gp_data_download')
    description.caption('Six CSV/JSON/Python/Markdown files · Standard library consumer · All three companies · Version hashes and source lineage · No workbooks or credentials required downstream')
    st.subheader('Normalized financial facts')
    st.caption('Default preview: the 12 reported revenue/EBITDA actual/budget operands selected by the existing company report adapter. Account detail and duplicate presentations are retained separately in the full package.')
    show_all=st.checkbox('Show all normalized observations, including unresolved mappings',key='foundation_all')
    options=['All companies']+[c.name for c in companies]
    selected=st.selectbox('Preview company',options,key='foundation_company')
    rows=[r for r in facts if (show_all or r['comparison_selected']) and (selected=='All companies' or r['company_name']==selected)]
    columns=['company_id','metric_id','period','period_grain','scenario','value','unit','currency','accounting_basis','source_fact_id','workbook_reference','verification_status','human_approval_status','mapping_status','metric_definition']
    st.dataframe(pd.DataFrame(rows,columns=columns),hide_index=True,width='stretch',column_config={'metric_definition':st.column_config.TextColumn('Metric definition',width='large')})
    st.caption(str(len(rows))+' preview records · Download always contains the full three-company package. Monthly, fiscal-quarter and annual records are never pooled.')
    with st.expander('Source lineage and package quality'):
        st.dataframe(pd.DataFrame(lineage[:12]),hide_index=True,width='stretch')
        st.json(quality,expanded=False)
    st.subheader('Independent reuse in another application')
    st.write('Extract the ZIP and run the included consumer. It builds a period-aware company comparison from CSV/JSON alone, with no application modules, original Excel files, network, credentials or AI model.')
    st.code('python3 example_consumer.py',language='sh')
    st.caption('The comparison uses explicitly selected reported totals and same-company periods. It never sums detail rows, duplicate statement presentations or monthly and annual financials.')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        with st.expander('Package contents and schema'):
            st.write(archive.namelist())
            st.json(json.loads(archive.read('metric_definitions.json')),expanded=False)
        with st.expander('Standalone consumer source'):
            st.code(archive.read('example_consumer.py').decode('utf8'),language='python')
