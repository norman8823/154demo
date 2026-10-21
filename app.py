from html import escape
import hashlib
import io
import copy
import json
import os
from ai_runtime import load_environment
load_environment()
import streamlit as st
import pandas as pd
from engine import analyze, demo_files, InputError, ROOT, DRAFT, BASIS, NOT_AVAILABLE, company_name, is_known_package
from reports import export_report, fields
from executive import present, money as executive_money, pp
from card_presentation import finding_html
from package_analysis import analysis_findings
from ingestion import MappingRequired

st.set_page_config(page_title='Portfolio Intelligence Copilot', page_icon='📊', layout='wide', initial_sidebar_state='collapsed')
st.markdown('''<style>
.stApp {background:#f4f7f8;border-top:6px solid #183e56;}
.block-container {max-width:1440px;padding:1.5rem 3rem 3rem;}
header[data-testid="stHeader"] {background:transparent;height:0;}
h1,h2,h3 {color:#172c40;letter-spacing:-.035em;} h1 {font-size:2rem!important;padding:.2rem 0 .5rem!important;} h2 {font-size:1.2rem!important;padding:.5rem 0 .3rem!important;} h3 {font-size:1.08rem!important;padding:.4rem 0!important;}
p,li {line-height:1.65;} .stCaption {color:#708597;}
[data-testid="stVerticalBlockBorderWrapper"]>div {border-radius:12px;background:white;}
[data-testid="stMetric"] {background:#fff;border:1px solid #dbe5eb;border-radius:12px;padding:20px;min-height:142px;}
[data-testid="stMetricLabel"] {font-size:13px;color:#6c8191;font-weight:600;}
[data-testid="stMetricValue"] {font-size:30px;letter-spacing:-.04em;color:#152d42;font-weight:750;}
.stButton>button,.stDownloadButton>button {border-radius:7px;min-height:43px;font-weight:650;}
.stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"] {background:#173e57;border:1px solid #173e57;color:white;}
[data-testid="stFileUploader"] {border:1px dashed #b7ccda;border-radius:9px;padding:8px;}
[data-testid="stFileUploaderDropzone"] {background:#f7fafc;min-height:150px;}
.brand {display:flex;align-items:center;gap:12px;background:#fff;padding:0 0 22px;border-bottom:1px solid #dce6eb;margin-bottom:22px;}
.monogram {background:#14384f;color:#fff;font-size:23px;font-weight:750;padding:2px 12px;border-radius:10px;}
.brand-title {font-size:17px;font-weight:750;} .brand-title span {font-weight:400;color:#7d8d9c;}
.pill {margin-left:auto;background:#e8f4f6;border-radius:30px;color:#22748a;padding:7px 13px;font-size:10px;font-weight:800;letter-spacing:.05em;}
.eyebrow {font-size:11px;font-weight:750;letter-spacing:.12em;color:#678596;margin:16px 0 5px;}
.badge {display:inline-block;background:#edf2f5;color:#416173;padding:3px 8px;font-size:10px;font-weight:800;border-radius:3px;margin-bottom:10px;}
.badge.amber {background:#edf2f5;color:#416173;}
.finding {border-top:3px solid #a8b8c3;padding:18px 4px 12px;min-height:210px;}
.finding.amber {border-color:#a8b8c3;}
.finding h3 {padding:0!important;margin:4px 0 12px!important;line-height:1.3!important;}.indicator {font-size:29px;font-weight:750;color:#18364A;letter-spacing:-.03em;}.indicator.adverse {color:#18364A;}
.indicator small {font-size:12px;font-weight:500;color:#718799;letter-spacing:0;}
.finding p {font-size:15px;color:#536b7c;margin:14px 0 0;}
.chain {background:#f5f9fb;border:1px solid #dce7ee;border-radius:8px;padding:17px;min-height:155px;font-size:14px;}
.chain small {display:block;color:#668596;font-size:10px;letter-spacing:.06em;margin-bottom:10px;}
.deliverables {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;margin:12px 0 24px;} .deliverable {font-size:14px;} .deliverable small {color:#73889b;display:block;margin-top:5px;} @media(max-width:800px) {.deliverables {grid-template-columns:repeat(2,minmax(0,1fr));}}
.excel-bar {background:#16725b;color:white;padding:12px 18px;font-size:14px;font-weight:700;border-radius:8px 8px 0 0;}
.report-banner {background:#eaf4ef;padding:8px 18px;color:#4d7764;font-size:11px;}
div[class*="st-key-"][class*="_panel"] {background:white;border-radius:12px;}
.prose {font-size:15px;line-height:1.65;color:#536e83;}
[role="radiogroup"][aria-label="Review steps"] {background:white;display:inline-flex;border:1px solid #dbe5eb;border-radius:8px;padding:8px 16px;}
[data-testid="stToolbar"] {display:none;}
footer {visibility:hidden;}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="brand"><div class="monogram">P</div><div class="brand-title">Portfolio Intelligence <span>Copilot</span></div><div class="pill">LOCAL FINANCIAL REVIEW</div></div>', unsafe_allow_html=True)

if 'view' not in st.session_state: st.session_state.view='01  Upload & Setup'
if 'pending_view' in st.session_state: st.session_state.view=st.session_state.pop('pending_view')

def go(view, finding=None):
    st.session_state.view=view
    if finding is not None: st.session_state.selected=finding

nav=st.radio('Review steps',['01  Upload & Setup','02  Portfolio Review','03  Evidence & Excel'],horizontal=True,key='view',label_visibility='collapsed')

def compute(items,decisions=None,layouts=None,profiles=None,ai_authorized=False,engine_name=None):
    from report_cache import cache_key,ReportCache,successful,reused
    files=dict(items);cache=ReportCache();identity=None
    # Setup materializes every automatic layout even when the user edits nothing.
    # Remove only exact no-op defaults so unattended and interactive inputs share
    # a cache identity. Explicit edits and pending AI interpretations stay distinct.
    if engine_name=='skill' and layouts:
        from ingestion import inspect_files
        defaults={}
        for table in inspect_files(files,profiles).tables:
            defaults[table.file+'|'+table.sheet]=dict(header_row=table.header_row,label_column=table.label_column,
                company=table.company,basis=table.basis,currency=table.currency,scale=table.scale,expense_sign=table.expense_sign,
                columns=[{k:c[k] for k in ('column','header','period','scenario','reference')} for c in table.columns])
        def semantic_layout(value):
            if not value:return value
            # The setup derives a single header-cell reference, while automatic
            # recognition can retain multiple header rows. This provenance-only
            # difference is not a user edit; all meaningful mapping fields stay.
            value=dict(value)
            if 'columns' in value:value['columns']=[{k:v for k,v in c.items() if k!='reference'} for c in value['columns']]
            return value
        layouts={k:v for k,v in layouts.items() if semantic_layout(v)!=semantic_layout(defaults.get(k))}
    if ai_authorized and os.environ.get('OPENAI_API_KEY'):
        try:identity=cache_key(files,decisions,layouts,profiles,ai_authorized,engine_name)
        except InputError:pass  # Existing backend diagnostics handle invalid configuration.
    saved=st.session_state.get('analysis_cache')
    if identity and saved and saved[0]==identity and successful(saved[1],require_real=False):
        return reused(copy.deepcopy(saved[1]),'session')
    if identity:
        review=cache.load(identity)
        if review is not None:
            st.session_state.analysis_cache=(identity,copy.deepcopy(review))
            return review
    review=analyze(files,decisions,layouts,profiles,ai_authorized=ai_authorized,engine_name=engine_name)
    if identity and successful(review,require_real=False):
        st.session_state.analysis_cache=(identity,copy.deepcopy(review))
        cache.save(identity,review)
    return review

@st.cache_data(show_spinner=False)
def make_report(review, template):
    return export_report(review,template)


def download(key):
    data,name,warnings=st.session_state.export
    st.download_button('↓  Download Excel Report',data,file_name=name,mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key=key,type='primary',width='stretch')
    if warnings: st.caption('Template has unmapped fields; see warnings in Evidence & Excel.')


def invalidate_review():
    for name in ('review','export'):
        st.session_state.pop(name,None)

def source_changed(key):
    invalidate_review()
    st.session_state.pop('ai_authorized_source',None)
    for widget in list(st.session_state):
        if str(widget).startswith(('accounts_','columns_','company_','basis_','currency_','scale_','sign_','resolve_','accept_','ai_confirm_','manual_','ai_consent_')):st.session_state.pop(widget,None)
    st.session_state.account_decisions={}
    st.session_state.financial_layouts={}
    uploads=st.session_state[key]
    st.session_state.uploaded_inputs={u.name:u.getvalue() for u in uploads}
    st.session_state.duplicate_names=len(st.session_state.uploaded_inputs)!=len(uploads)
    st.session_state.demo=False

def use_demo():
    invalidate_review()
    st.session_state.pop('ai_authorized_source',None)
    st.session_state.demo=True
    st.session_state.uploaded_inputs={}
    st.session_state.duplicate_names=False
    st.session_state.upload_generation=st.session_state.get('upload_generation',0)+1

def use_skill_example(name):
    # Names come only from the local demo selector, never arbitrary upload paths.
    choices={p.name:p for p in (ROOT/'demo_workbooks').glob('*.xlsx')}
    if name not in choices:return
    use_demo()
    st.session_state.demo=False
    st.session_state.uploaded_inputs={name:choices[name].read_bytes()}
    st.session_state.account_decisions={}
    st.session_state.financial_layouts={}


def prose(text):
    st.markdown('<div class="prose">'+escape(text)+'</div>',unsafe_allow_html=True)

def template_changed():
    invalidate_review()
    if st.session_state.get('template_upload'):
        st.session_state.report_format='Use existing firm template'


# Reviewed bundled synthetic sources only. Changed files require upload consent.
SYNTHETIC_DEMO_HASHES=frozenset({
    '73d269f3914de054fc80a06448fe7e5e44e3fbc2cf4b53dddb2d126b14f7efed',  # AddOnB_QuickBooks_Export_Sep2026.xlsx
    '2423e1e0938905c981602155e4abb397946751cac735d2d442fdad90d2502d5d',  # PlatformA_Monthly_Package_Sep2026.xlsx
    'be206054aadaaf24ca4ba7d2f8685f1fb8fefb181e16bf4caecab933cfe7be8b',  # AddOnB_Sep2026_Schedule_Export.csv
    'd68a9265c32c60907b5254ebc8bcc0ae507d513fb7dbf443a88a9f5499999037',  # A_Northstar.xlsx
    '579c50633cc510c0eb0c72344125edc3826a125038a77cbc10607e598f270b2f',  # B_Harbor.xlsx
    '7c274c00ad7a6c66a3308e03c28f4d81fd257b948e35b17d98b87b82056f2d5f',  # C_Northgate.xlsx
    '52c66cf2c5b95fbfd68b4cbafcffd2d1c1fd4877cbc16a8fec75ff4eb90cbaf0',  # Summit_Home_Services_Sep2026.xlsx
    '197be0d0e0a34273206d61c47df3f63fbb22fca468a2d9c4fc497d030c49cd9b',  # Tallis_Brook_Accounting_Sep2026.xlsx
    'bdd9c427e57f4c55fa4a135a0126bd25f5fbdae5781b7c192067bbb937788efb',  # Harrow_Ridge_Environmental_FY2026.xlsx: explicitly trusted synthetic holdout
})


def synthetic_demo(files):
    return bool(files) and all(hashlib.sha256(data).hexdigest() in SYNTHETIC_DEMO_HASHES for data in files.values())


def upload_view():
    st.title('Generate a portfolio review')
    st.caption('Upload financials. Generate your review. Inspect findings and download Excel.')
    from skill_engine import selected_engine
    engine_name=selected_engine()
    if engine_name=='skill':
        engine_name=st.selectbox('Analytical engine',['skill','legacy'],format_func=lambda x:'Skill analyst v2 (experimental)' if x=='skill' else 'Legacy analyst (explicit fallback)')
        st.caption('Skill analysis supports one workbook. Failed or incomplete runs are disclosed; legacy is available as an explicit rerun.')
    decisions={};layouts={};profiles={}
    with st.container(border=True,key='source_panel'):
        st.subheader('1 — Upload Financial Files')
        left,right=st.columns([1.5,1],gap='large')
        with left:
            upload_key=f'financial_uploads_{st.session_state.get("upload_generation",0)}'
            st.file_uploader('Drag and drop financial files',type=['xlsx','csv'],accept_multiple_files=True,key=upload_key,on_change=source_changed,args=(upload_key,))
        files=st.session_state.get('uploaded_inputs') or (demo_files() if st.session_state.get('demo') else {})
        with right:
            if engine_name=='legacy':st.button('Use Demo Files',on_click=use_demo)
            if engine_name=='skill':
                examples=sorted(p.name for p in (ROOT/'demo_workbooks').glob('*.xlsx'))
                if examples:
                    example=st.selectbox('Company workbook',examples,format_func=lambda n:n.removesuffix('.xlsx').replace('_',' '))
                    st.button('Load company workbook',on_click=use_skill_example,args=(example,))
                    st.caption('Generate reuses a completed validated review when its workbook and engine configuration match.')
            for name in files: st.caption('✓  '+name)
            if not files: st.caption('Excel or CSV · One or multiple files')
            ai_authorized=bool(os.environ.get('OPENAI_API_KEY')) and synthetic_demo(files)
            if files and not synthetic_demo(files):
                consent_id=hashlib.sha256(b''.join(hashlib.sha256(data).digest() for _,data in sorted(files.items()))).hexdigest()[:18]
                with st.expander('External analysis permission',expanded=False):
                    st.write('AI analysis sends extracted financial facts, labels and commentary to OpenAI. Raw workbooks are not sent. Only authorize data you are permitted to share; you can generate a source-based review without external AI.')
                    ai_authorized=st.checkbox('Authorize external analysis of these uploads',value=st.session_state.get('ai_authorized_source')==consent_id,key='ai_consent_'+consent_id,disabled=not bool(os.environ.get('OPENAI_API_KEY')))
                if ai_authorized:st.session_state.ai_authorized_source=consent_id
                else:st.session_state.pop('ai_authorized_source',None)
            summary=st.container()
        if files:
            if engine_name=='skill':
                from skill_tools import preflight
                try:preflight(files)
                except InputError as exc:
                    st.error(str(exc))
                    return
            try:known=is_known_package(files)
            except InputError:known=False
            if known:
                with summary:
                    st.markdown('**Demonstration financial package recognized**')
                    st.caption('Supported checks will use the supplied files. Missing inputs are disclosed in the review.')
            else:
                from mapping_ui import prepare
                decisions,layouts,profiles,_=prepare(files,summary=summary,ai_authorized=ai_authorized)
    with st.container(border=True,key='template_panel'):
        st.subheader('2 — Choose Output Format')
        left,right=st.columns([1.5,1],gap='large')
        with left:
            t=st.file_uploader('Drag and drop an optional Excel template',type=['xlsx'],key='template_upload',on_change=template_changed)
        with right:
            choice=st.radio('Report format',['Standard Excel report','Use existing firm template'],key='report_format',label_visibility='collapsed')
            template=None
            if choice=='Use existing firm template':
                sample=st.checkbox('Use supplied sample template')
                if t: template=t.getvalue()
                elif sample: template=(ROOT/'sample_templates/Sample_Firm_Review_Template.xlsx').read_bytes()
                st.caption('Your layout, formulas and formatting are preserved.')
            else: st.caption('Ready to download in the standard Excel layout. No template needed.')
        with st.expander('Template guidance',expanded=False):
            st.caption('Existing firm templates use supported {{FIELD}} placeholders. Unmapped fields are disclosed in the report. Start with the sample to see supported fields.')
            st.download_button('Get sample Excel template',(ROOT/'sample_templates/Sample_Firm_Review_Template.xlsx').read_bytes(),file_name='Sample_Firm_Review_Template.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    with st.container(border=True,key='deliverable_panel'):
        st.subheader('3 — Generate Portfolio Review')
        descriptions=[('▥','Financial dashboard','Key metrics and variances'),('◇','Priority findings','Material risks and opportunities'),('≡','Investment Assessment','Executive commentary and Management Questions'),('↓','Excel report','Editable and downloadable')]
        st.markdown('<div class="deliverables">'+''.join(f'<div class="deliverable"><b>{icon} &nbsp; {title}</b><small>{detail}</small></div>' for icon,title,detail in descriptions)+'</div>',unsafe_allow_html=True)
        generate=st.button('Generate Portfolio Review  →',type='primary',width='stretch',disabled=not files)
        if generate:
            invalidate_review()
            try:
                if st.session_state.get('duplicate_names'): raise InputError('Duplicate uploaded filenames: use distinct source filenames.')
                if choice=='Use existing firm template' and not template: raise InputError('Upload an Excel template or select the supplied sample.')
                with st.spinner('Checking source facts and preparing your Excel report…'):
                    review=compute(tuple(files.items()),decisions,layouts,profiles,ai_authorized,engine_name)
                    exported=make_report(review,template)
                st.session_state.review=review
                st.session_state.export=exported
                st.session_state.source_names=list(files)
                st.session_state.custom=bool(template)
                st.session_state.pending_view='02  Portfolio Review'
                st.rerun()
            except MappingRequired as e:
                st.info(str(e))
                for issue in e.intake.unresolved:st.info(issue['File']+': '+issue['Reason'])
            except InputError as e: st.error(str(e))
            except Exception:
                st.error('The files could not be processed. Check the financial table, period columns and mapping review; source amounts must be numeric or supported formulas.')


def readiness(r,disclosures=False):
    missing=[item for item in r.readiness if item['Status']!= 'Available']
    st.caption(f'{len(r.readiness)-len(missing)} analyses available · {len(missing)} need additional data')
    with st.expander('Data Quality & Coverage' if disclosures else 'Data readiness',expanded=False):
        if disclosures:
            for warning in dict.fromkeys(r.warnings):st.write(warning.replace('$',r'\$'))
            st.caption('Accounting assumptions: '+r.basis_note)
            st.caption(r.package.get('mode',''))
            if r.package.get('inference'):st.json(r.package['inference'])
            if r.package.get('ai_validation'):st.json(r.package['ai_validation'])
            if r.package.get('skill_engine'):st.json(r.package['skill_engine'])
            if r.package.get('financial_extraction'):st.json(r.package['financial_extraction'])
            for limitation in r.package.get('limitations',[]):st.caption(limitation)
            if r.package.get('coverage'):st.dataframe(pd.DataFrame(r.package['coverage']),hide_index=True,width='stretch')
            st.caption('Custom-template fields and definitions are documented in the Excel report; unmapped fields are reported with the download.')
        for item in r.recognized: st.caption(item['File']+' → '+item['Recognized as'])
        st.dataframe(pd.DataFrame(r.readiness).drop(columns=['Analysis ID']),hide_index=True,width='stretch')
        st.caption('Unavailable checks are omitted from findings and financial exception totals.')
        if r.adaptive and r.financial_rows:
            st.dataframe(pd.DataFrame(r.financial_rows,columns=['Financial metric / period','Value','Unit','Definition','Fact IDs']),hide_index=True,width='stretch')


def money(r,value,signed=False):
    return executive_money(r,value,signed=signed)


def overview(r):
    if r.package.get('skill_engine',{}).get('status')=='failed':st.error(r.narrative_mode)
    elif r.package.get('skill_engine',{}).get('status')=='partial':st.warning(r.narrative_mode)
    elif r.package.get('engine_identity')=='skill':st.caption(r.narrative_mode)
    m=r.metrics
    summary=present(r)
    title,actions=st.columns([2.7,1])
    with title:
        st.markdown('<div class="eyebrow">PORTFOLIO MONITORING / FINANCIAL REVIEW</div>',unsafe_allow_html=True)
        st.title(r.report_period+' Portfolio Review')
        st.caption(f"{company_name(r)}  •  {len(summary['cards'])} material findings")
    with actions:
        st.button('View source evidence',on_click=go,args=('03  Evidence & Excel',),width='stretch')
        download('overview_download')
    profile=r.package.get('company_profile',{})
    st.subheader('Investment Summary')
    if profile.get('description'):prose(profile['description'])
    st.caption(company_name(r)+' · '+r.report_period)
    metrics=[]
    if 'revenue' in m: metrics.append(('Revenue' if r.adaptive else 'Platform A revenue',money(r,m['revenue']),f"{m['revenue_variance']:+.1%} vs. budget" if 'revenue_variance' in m else None,'normal'))
    if r.adaptive and 'ebitda' in m:metrics.append(('EBITDA',money(r,m['ebitda']),money(r,m['ebitda_variance'],signed=True).replace('−','-') + ' vs. budget' if 'ebitda_variance' in m else None,'normal'))
    if 'gm' in m: metrics.append(('Gross margin',f"{m['gm']:.1%}",pp(m['gm_variance_pp']).replace('−','-')+' vs. budget' if 'gm_variance_pp' in m else None,'normal'))
    if 'subcontract' in m: metrics.append(('Subcontracted labor',f"${m['subcontract']/1000:,.0f}K",f"${m['subcontract_variance']/1000:+,.0f}K vs. budget",'inverse'))
    if 'leverage_reported' in m: metrics.append(('Reported net leverage',f"{m['leverage_reported']:.2f}x",f"Current maximum {m['covenant_max']:.2f}x",'off'))
    if r.adaptive:
        if 'ebitda' not in m and 'operating_profit' in m:metrics.append(('Operating income',money(r,m['operating_profit']),None,'off'))
        if 'operating_expenses' in m:metrics.append(('Operating expenses',money(r,m['operating_expenses']),None,'off'))
        elif 'net_income' in m:metrics.append(('Net income',money(r,m['net_income']),None,'off'))
    if not metrics:
        if 'addon_cash_income' in m: metrics.append(('Add-on B total income · cash basis',f"${m['addon_cash_income']:,.0f}",None,'off'))
        if 'billing_total' in m: metrics.append(('Potential billing exceptions',f"${m['billing_total']:,.2f}",'Requires invoice reconciliation','off'))
        if 'schedule_rows' in m: metrics.append(('Unique schedule rows',str(m['schedule_rows']),None,'off'))
    metrics=metrics[:3]
    if metrics:
        for col,(label,value,delta,color) in zip(st.columns(len(metrics)),metrics):
            col.metric(label,value,delta,delta_color=color)
    if profile.get('segments'):
        st.caption(' · '.join(s['name']+' ('+s['kind']+'): '+s['description'] for s in profile['segments']))
    if r.package.get('ai_briefing'):st.caption(r.narrative_mode)
    elif r.package.get('engine_identity')!='skill':
        diagnostic=r.package.get('ai_validation',{})
        if diagnostic.get('status')=='not_requested':
            reason='External AI was not authorized.' if diagnostic.get('reason')=='not_authorized' else 'AI analysis was unavailable.'
        elif diagnostic.get('status')=='validation_failure':reason='AI findings did not pass source checks.'
        else:reason='AI analysis could not complete.'
        st.warning(reason+' Your source-based review and Excel report are ready.')
    if r.package.get('inference',{}).get('reused'):st.caption('Reused the prior analysis for these files; no new model request.')
    if summary['notice']:st.warning(summary['notice'])
    st.subheader('Priority findings')
    if not summary['cards']: st.info('No completed assessment is available.' if r.package.get('skill_engine',{}).get('status')=='failed' else 'No material findings were established from the available data. Unavailable analyses are listed in Data Quality & Coverage.')
    columns=st.columns(len(summary['cards'])) if summary['cards'] else []
    for col,card in zip(columns,summary['cards']):
        with col,st.container(border=True,key=f'finding_panel_{card["id"]}'):
            st.markdown(finding_html(card,r),unsafe_allow_html=True)
            st.button('View Evidence  →',key=f'evidence_{card["id"]}',on_click=go,args=('03  Evidence & Excel',card['id']),width='stretch')
    left,right=st.columns([1.4,1])
    with left,st.container(border=True,key='brief_panel'):
        st.subheader('Investment Assessment')
        st.caption('For Investment Team Review')
        for label,text in summary['paragraphs']:
            st.markdown('**'+label+'**')
            prose(text)
    with right,st.container(border=True,key='question_panel'):
        st.subheader('Management Questions')
        for q in summary['questions']: prose('• '+q)
        if not summary['questions']: st.caption('Finding-based questions will appear when the required data is available.')
        st.button('Open source evidence  →',on_click=go,args=('03  Evidence & Excel',),width='stretch')
    if summary.get('secondary') or r.package.get('claims'):
        with st.expander('Additional insights & commentary',expanded=False):
            for card in summary.get('secondary',[]):
                st.markdown('**'+escape(card['title'])+' · '+escape(card['impact'])+'**')
                prose(card['summary'])
                if card.get('why'):prose(card['why'])
                st.button('View evidence',key='secondary_'+str(card['id']),on_click=go,args=('03  Evidence & Excel',card['id']))
            for claim in r.package.get('claims',[]):
                st.markdown('**'+claim['status'].upper()+' · Management claim**')
                prose(claim['quote']);prose(claim['assessment'])
                st.caption(claim['file']+' · '+claim['ref']+' · Scope: '+claim['tested_assertion'])
    readiness(r,disclosures=True)


def evidence_view(r):
    head,dl=st.columns([3,1])
    with head:
        st.markdown('<div class="eyebrow">SOURCE EVIDENCE / FINANCIAL LINEAGE</div>',unsafe_allow_html=True)
        st.title('See where every conclusion came from')
        st.caption('Inspect the calculation, original source cells, and review limitations.')
    with dl: download('evidence_top_download')
    readiness(r)
    all_findings=analysis_findings(r)
    if not all_findings:
        st.info('No finding evidence is available yet. Recognized sources and readiness are included in the downloadable report.')
    else:
        sidebar,detail=st.columns([.8,2.8])
        with sidebar,st.container(border=True,key='selector_panel'):
            by_id={f['id']:f for f in all_findings}
            if st.session_state.get('selected') not in by_id: st.session_state.selected=next(iter(by_id))
            selected=st.radio('Select a finding',list(by_id),format_func=lambda n:f'0{n}  {by_id[n]["title"]}',key='selected')
        f=by_id[selected]
        view=present(r)
        group=next((c for c in view['cards']+view.get('secondary',[]) if c['id']==selected),None)
        ids=group['ids'] if group else [selected]
        ev=[e for e in r.evidence if e['Finding'] in ids]
        if len(ids)>1:
            f=dict(f,calculation=' '.join(item['calculation'] for item in all_findings if item['id'] in ids))
        with detail,st.container(border=True,key='evidence_panel'):
            st.subheader(f['title'])
            st.caption(f['severity'])
            prose(f['summary'])
            chain=st.columns([1,1.5,1])
            source='; '.join(dict.fromkeys(e['Reference'] for e in ev[:3]))
            for col,label,text in zip(chain,['ORIGINAL SOURCE →','DETERMINISTIC CHECK →','BUSINESS CONCLUSION'],[source,f['calculation'],f['conclusion']]):
                col.markdown(f'<div class="chain"><small>{label}</small>{escape(text)}</div>',unsafe_allow_html=True)
            st.write('')
            evidence_frame=pd.DataFrame(ev)
            for column in ['Validated value','Original value / formula']: evidence_frame[column]=evidence_frame[column].map(str)
            st.dataframe(evidence_frame,hide_index=True,width='stretch',column_order=['Fact ID','File','Reference','Validated value','Original value / formula','Check / use'],column_config={'Validated value':st.column_config.TextColumn('Validated value')})
            st.info(f['caveat'])
            st.markdown('**Next action:** '+f['action'])
            if selected==1 and 'ceo_claim' in r.metrics:
                st.markdown('**Management commentary check**')
                st.write('“'+r.metrics['ceo_claim']+'”')
                st.caption('Compare the quoted assertion to the fill rate and margin facts above. Discrepancies remain visible for management review.')
            if selected==3:
                st.markdown('**Invoice-level reconciliation list**')
                st.dataframe(pd.DataFrame(r.billing),hide_index=True,width='stretch')
                for w in r.warnings: st.caption(w)
    with st.expander('Raw → standardized · acquired-company mapping preview',expanded=False):
        st.caption('A small judgment-based classification preview. No automatic accounting entries or consolidation.')
        if r.mapping: st.dataframe(pd.DataFrame(r.mapping),hide_index=True,width='stretch')
        else: st.caption('Mapping preview '+NOT_AVAILABLE+' Add the Add-on B cash-basis Profit and Loss sheet.')
    st.subheader('Downloadable Excel report')
    preview,export=st.columns([2.5,1])
    with preview,st.container(border=True,key='preview_panel'):
        name=st.session_state.export[1]
        st.markdown(f'<div class="excel-bar">▦ &nbsp; {escape(name)}</div><div class="report-banner">{escape(r.report_period.upper())} &nbsp; / &nbsp; FOR INVESTMENT TEAM REVIEW &nbsp; / &nbsp; EDITABLE EXCEL</div>',unsafe_allow_html=True)
        st.subheader('Portfolio Monitoring — Investment Assessment')
        preview_findings=all_findings if r.package.get('engine_identity')=='skill' else r.findings
        st.dataframe(pd.DataFrame([{'Finding':f['title'],'Indicator':f['indicator'],'Status':f['severity']} for f in preview_findings],columns=['Finding','Indicator','Status']),hide_index=True,width='stretch')
        st.caption('Custom template + supporting sheets' if st.session_state.custom else 'Executive Summary  /  Financial Performance  /  Exceptions  /  Source Evidence')
    with export,st.container(border=True,key='export_panel'):
        st.subheader('Ready for investment team review')
        st.write('Populated values, editable commentary, exact evidence and source calculations. The workbook is reopened and checked before download.')
        st.caption('Custom templates preserve existing formulas and formatting. Unknown placeholders remain visible and are reported below. The Template Guide remains documentation.')
        download('evidence_bottom_download')
    for warning in st.session_state.export[2]: st.warning(warning)
    st.caption('For Investment Team Review · No sending or sharing')

if nav=='01  Upload & Setup': upload_view()
elif 'review' not in st.session_state:
    st.info('Start with Upload & Setup, select your files, and generate a review.')
    st.button('Go to Upload & Setup',on_click=go,args=('01  Upload & Setup',))
elif nav=='02  Portfolio Review': overview(st.session_state.review)
else: evidence_view(st.session_state.review)
