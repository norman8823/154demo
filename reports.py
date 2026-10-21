"""Editable Excel reports and explicit, formula-preserving template fill."""
import io
import re
from copy import copy
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.workbook.properties import CalcProperties
from engine import DRAFT, BASIS, InputError, NOT_AVAILABLE, company_name
from executive import present,briefing,report_findings
from excel_layout import executive_sheet, financial_table, style_performance, finding_rows, source_rows, link_reports, comparison_text

TOKEN = re.compile(r'\{\{([A-Z][A-Z0-9_]*)\}\}')
NAVY='18364A'; TEAL='17725D'

def fields(review):
    m=review.metrics
    summary=present(review)
    d={'ANALYSIS_MODE':review.narrative_mode,'COMPANY_NAME':company_name(review),'REPORT_PERIOD':review.report_period,'PLATFORM_REVENUE':m.get('revenue',NOT_AVAILABLE),'GROSS_MARGIN_ACTUAL':m.get('gm',NOT_AVAILABLE),'GROSS_MARGIN_BUDGET':m.get('gm_budget',NOT_AVAILABLE),'LEVERAGE_REPORTED':m.get('leverage_reported',NOT_AVAILABLE),'LEVERAGE_CAP_ONLY':m.get('leverage_cap',NOT_AVAILABLE),'COVENANT_MAX':m.get('covenant_max',NOT_AVAILABLE),'SUBCONTRACT_ACTUAL':m.get('subcontract',NOT_AVAILABLE),'SUBCONTRACT_BUDGET':m.get('subcontract_budget',NOT_AVAILABLE),'FINDING_COUNT':len(summary['cards']),'PARTNER_BRIEF':briefing(summary)}
    if review.package.get('skill_engine',{}).get('status')=='partial':d['PARTNER_BRIEF']='PARTIAL REVIEW — Only validated findings shown. '+d['PARTNER_BRIEF']
    d.update({f'FINDING_{i}':('No additional material finding.' if review.adaptive else NOT_AVAILABLE) for i in range(1,4)})
    d.update({f'CFO_Q{i}':'No additional finding-based question available.' for i in range(1,4)})
    d.update({f'FINDING_{i if review.adaptive or review.package.get("view") else f["id"]}':f['title']+': '+f['summary'] for i,f in enumerate(summary['cards'],1)})
    for token,key in [('REVENUE','revenue'),('GROSS_PROFIT','gross_profit'),('OPERATING_EXPENSES','operating_expenses'),('EBITDA','ebitda'),('NET_INCOME','net_income')]:d[token]=m.get(key,NOT_AVAILABLE)
    d['CURRENCY']=review.currency
    d['ACCOUNTING_BASIS']=review.basis_note
    d.update({f'CFO_Q{i}':q for i,q in enumerate(summary['questions'],1)})
    if review.adaptive and (review.currency=='unknown' or review.scale is None):
        for token in ['PLATFORM_REVENUE','REVENUE','GROSS_PROFIT','OPERATING_EXPENSES','EBITDA','NET_INCOME','SUBCONTRACT_ACTUAL','SUBCONTRACT_BUDGET']:
            if isinstance(d[token],(int,float)):d[token]=NOT_AVAILABLE+' Source currency/scale not confirmed.'
    from company_context import text as context_text
    d['INVESTMENT_SUMMARY']=context_text(review)
    return d


def write_cell(ws,row,col,value):
    c=ws.cell(row,col)
    c.value=value
    # Source-provided text must remain literal text, including formula prefixes.
    if isinstance(value,str): c.data_type='s'
    return c


def table(wb,name,headers,rows,report=None):
    ws=wb[name] if name in wb.sheetnames else wb.create_sheet(name)
    start=ws.max_row+3 if ws.max_row>1 or ws['A1'].value is not None else 1
    for i,val in enumerate([name,company_name(report) if report else '',report.report_period if report else '']):
        c=write_cell(ws,start+i,1,val); c.font=Font(bold=True,color=NAVY,size=13 if i==1 else 10)
    head=start+4
    for j,h in enumerate(headers,1):
        c=write_cell(ws,head,j,h); c.fill=PatternFill('solid',fgColor=NAVY); c.font=Font(bold=True,color='FFFFFF'); c.alignment=Alignment(wrap_text=True,vertical='center')
    ws.row_dimensions[head].height=36
    for i,row in enumerate(rows,head+1):
        for j,val in enumerate(row,1):
            c=write_cell(ws,i,j,val); c.alignment=Alignment(vertical='top',wrap_text=True)
            if (i-head)%2: c.fill=PatternFill('solid',fgColor='EFF5F7')
            if isinstance(val,(int,float)): c.number_format='#,##0.00;(#,##0.00)'
        ws.row_dimensions[i].height=45 if any(isinstance(v,str) and len(v)>90 for v in row) else 28
    for j,h in enumerate(headers,1): ws.column_dimensions[ws.cell(head,j).column_letter].width=min(65,max(20,len(h)+3))
    ws.column_dimensions['A'].width=30
    if name=='Executive Summary': ws.column_dimensions['B'].width=115
    ws.freeze_panes=f'A{head+1}'
    if rows: ws.auto_filter.ref=f'A{head}:{ws.cell(head+len(rows),len(headers)).coordinate}'
    ws.sheet_view.showGridLines=False
    ws.sheet_properties.pageSetUpPr.fitToPage=True
    ws.page_setup.orientation='landscape'; ws.page_setup.paperSize=ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth=1; ws.page_setup.fitToHeight=0
    return ws,head


def performance_rows(r):
    m=r.metrics
    rows=[]
    specs=[('Platform A revenue','revenue','USD','Calculated / accrual','revenue'),('Revenue budget','revenue_budget','USD','Reported budget','revenue_budget'),('Revenue variance','revenue_variance','ratio','Calculated','revenue / revenue_budget − 1'),('Gross margin actual','gm','ratio','Calculated','gross_profit / revenue; gm_source'),('Gross margin budget','gm_budget','ratio','Calculated','gross_profit_budget / revenue_budget; gm_budget_source'),('Gross margin variance','gm_variance_pp','percentage points','Calculated','gm − gm_budget; × 100'),('Subcontract labor actual','subcontract','USD','Calculated / accrual','subcontract'),('Subcontract labor budget','subcontract_budget','USD','Reported budget','subcontract_budget'),('Subcontract labor variance','subcontract_variance','USD','Calculated','subcontract − subcontract_budget'),('Shift fill rate','fill','ratio','Calculated / event staffing only','filled / requested; fill'),('Reported leverage','leverage_reported','multiple','Reported; recomputed','net_debt / reported_ebitda'),('Cap-only leverage','leverage_cap','multiple','Illustrative sensitivity','net_debt / cap_ebitda'),('Before-synergy EBITDA','before_synergies','USD','Calculated / reported pro forma','base_platform + pre_acquisition + post_acquisition'),('Reported covenant EBITDA','reported_ebitda','USD','Reported; recomputed','reported_ebitda'),('Net debt','net_debt','USD','Reported; recomputed','net_debt'),('Synergy cap','synergy_cap','ratio','Reported agreement excerpt','synergy_cap'),('Allowed synergies','allowed_synergies','USD','Calculated','min(synergies, before_synergies × synergy_cap)'),('Synergies trimmed','synergy_trim','USD','Calculated','synergies − allowed_synergies'),('Cap-only EBITDA','cap_ebitda','USD','Illustrative sensitivity','before_synergies + allowed_synergies'),('Current covenant maximum','covenant_max','multiple','Reported','covenant_max'),('Reported headroom','headroom_reported','multiple','Calculated','covenant_max − leverage_reported'),('Cap-only headroom','headroom_cap','multiple','Illustrative sensitivity','covenant_max − leverage_cap'),('March 2027 maximum','future_max','multiple','Reported future threshold; no forecast','stepdown_terms'),('Uninvoiced worked hours value','unbilled','USD','Potential exception / unverified','billing_*; uninvoiced hours × contract rate'),('Invoiced rate differences','underbilled','USD','Potential exception / unverified','billing_*; invoiced hours × (contract − billed)'),('Potential billing exceptions','billing_total','USD','Requires reconciliation','unbilled + underbilled; disjoint groups'),('Add-on B total income','addon_cash_income','USD','Reported / cash basis; separate','addon_cash_income')]
    if r.adaptive: rows.extend(r.financial_rows)
    else:
        for label,key,unit,status,calc in specs:
            if key in m: rows.append([label,m[key],unit,status,calc])
    for item in r.package.get('facts',[]):
        rows.append([item['label']+' · '+item['period']+' · '+item['scenario']+' · '+item['entity'],item['value'],item['unit'],'Source schedule',item['id']+' · '+item['file']+' · '+item['ref']])
    for finding in r.package.get('findings',[]):
        rows.append(['Investment insight · '+finding['title'],comparison_text(finding['summary'],r,finding['refs']),'',finding['severity'],'; '.join(finding['refs'])])
    for claim in r.package.get('claims',[]):
        rows.append(['Commentary check · '+claim['status'],claim['quote'],'',claim['assessment'],'; '.join(claim['refs'])])
    for item in r.readiness:
        rows.append([item['Analysis'],item['Status'],'','Data readiness',item['Additional data'] or 'Required data available'])
    rows.append(['Analysis mode',r.narrative_mode,'','Inference disclosure','AI interpretations require investment-team review; limited fallback is not a full model investment assessment.'])
    rows.append(['Accounting limitation',r.basis_note,'','Review limitation','No consolidation'])
    for w in r.warnings: rows.append(['Data quality note',w,'','Review limitation','Source validation'])
    return rows


def fit_template_narratives(wb, cells):
    """Grow only mapped narrative rows; preserve cells, merges, widths and styles."""
    import math
    import textwrap
    from openpyxl.utils import get_column_letter
    for sheet,coord in cells:
        ws=wb[sheet];cell=ws[coord]
        if not isinstance(cell.value,str) or not cell.alignment.wrap_text:continue
        merged=next((m for m in ws.merged_cells.ranges if coord in m),None)
        left,right=(merged.min_col,merged.max_col) if merged else (cell.column,cell.column)
        top,bottom=(merged.min_row,merged.max_row) if merged else (cell.row,cell.row)
        width=sum((ws.column_dimensions.get(get_column_letter(c)).width if ws.column_dimensions.get(get_column_letter(c)) is not None else ws.sheet_format.defaultColWidth or 8.43) for c in range(left,right+1))
        font=cell.font.sz or 11
        chars=max(12,int((width-2)*11/font*.9))
        lines=sum(max(1,len(textwrap.wrap(p,width=chars))) for p in cell.value.splitlines())
        height=math.ceil((lines*(font*1.35)+10)/(bottom-top+1))
        for row in range(top,bottom+1):
            ws.row_dimensions[row].height=min(409,max(ws.row_dimensions[row].height or ws.sheet_format.defaultRowHeight or 15,height))


def export_report(r,template=None):
    original_formulas={}; original_sheets=[]; original_styles={}; filled={}; warnings=[]; narrative_cells=[]
    d=fields(r)
    if template:
        try: wb=load_workbook(io.BytesIO(template))
        except Exception as e: raise InputError('Cannot open report template. Upload a valid .xlsx file without macros.') from e
        original_sheets=wb.sheetnames[:]
        supported_count=0
        for ws in wb:
            if ws.title == 'Template Guide': continue
            for row in ws:
                for c in row:
                    key=(ws.title,c.coordinate)
                    if c.data_type=='f': original_formulas[key]=c.value; continue
                    if not isinstance(c.value,str): continue
                    c.value=re.sub(r'draft partner briefing|questions for the cfo',lambda m:'Investment Assessment' if 'briefing' in m[0].lower() else 'Management Questions',c.value,flags=re.I)
                    c.value=re.sub(r'DRAFT — Requires Investment Team Review|^DRAFT$','For Investment Team Review',c.value)
                    tokens=TOKEN.findall(c.value)
                    if not tokens: continue
                    if r.package.get('skill_engine') and any(re.fullmatch(r'PARTNER_BRIEF|INVESTMENT_SUMMARY|FINDING_\d+|CFO_Q\d+',t) for t in tokens):narrative_cells.append(key)
                    raw=c.value
                    for token in tokens:
                        if token not in d: warnings.append(f'{ws.title}!{c.coordinate}: unsupported {{{{{token}}}}}')
                    exact=TOKEN.fullmatch(raw)
                    if exact and exact[1] in d:
                        val=d[exact[1]]; supported_count+=1
                        original_styles[key]=copy(c._style)
                        c.value=val
                        if r.adaptive and isinstance(val,(int,float)) and '$' in c.number_format and r.currency not in ('USD','unknown'):
                            c.number_format=c.number_format.replace('$','"'+r.currency+' "')
                            original_styles[key]=copy(c._style)
                            warnings.append('Explicit USD number formats in mapped cells were relabeled '+r.currency+'; no currency conversion was performed. Other template formatting and formulas are preserved.')
                        if isinstance(val,str): c.data_type='s'
                        # Existing supplied template formats are preserved exactly.
                        filled[key]=val
                    else:
                        c.value=TOKEN.sub(lambda m:str(d[m[1]]) if m[1] in d else m[0],raw)
                        c.data_type='s'
                        supported_count+=sum(t in d for t in tokens)
        if not supported_count: warnings.append('No supported report fields found. This layout requires a one-time field mapping; see the supplied sample template.')
        filename=r.report_period.replace(' ','_')+'_Custom_Portfolio_Review.xlsx'
    else:
        wb=Workbook(); wb.remove(wb.active)
        executive_sheet(wb,r)
        filename=r.report_period.replace(' ','_')+'_Portfolio_Review.xlsx'
    if 'Executive Summary' not in wb.sheetnames:executive_sheet(wb,r)
    financial=financial_table(r)
    financial_headers=['Financial metric','Actual','Budget','Variance vs budget / pp','Variance vs budget %','Prior year actual','Year-over-year %','Prior month actual','Month-over-month %','Units','Actual period','Company / scope','Source fact IDs']
    periods={row[10] for row in financial}
    if len(periods)==1:
        from datetime import datetime
        label=next(iter(periods))
        p=None
        for fmt in ('%b %Y','%B %Y'):
            try:p=datetime.strptime(label,fmt).strftime('%Y-%m');break
            except ValueError:pass
        if p:
            from excel_layout import period_label,shift_month
            for col,role,offset in [(1,'Actual',0),(2,'Budget',0),(5,'Prior year actual',-12),(7,'Prior month actual',-1)]:
                comparison=p if offset==0 else ((str(int(p[:4])-1)+p[4:]) if offset==-12 else shift_month(p,offset))
                financial_headers[col]=role+(' · '+period_label(comparison) if comparison else ' (not applicable)')
    perf,head=table(wb,'Financial Performance', financial_headers,
        [row[:13] for row in financial],r)
    style_performance(perf,head,financial)
    detail,detail_head=table(wb,'Extracted Detail',['Metric / source item','Validated value','Unit','Definition / status','Source fact IDs'],performance_rows(r),r)
    for row in detail.iter_rows(min_row=detail_head+1):
        if row[2].value=='ratio':row[1].number_format='0.00%'
        if row[2].value=='multiple':row[1].number_format='0.00"x"'
    from company_context import text as context_text
    context=context_text(r)
    if context:
        profile=r.package['company_profile']
        profile_rows=[['Business',profile.get('description',''),'; '.join(c['source_id'] for c in profile.get('citations',[]))],['Reporting period',r.report_period,'']]
        profile_rows += [[s['name']+' · '+s['kind'],s['description'],'; '.join(c['source_id'] for c in s['citations'])] for s in profile.get('segments',[])]
        profile_rows += [[row[0],row[1],row[9]+'; '+row[12]] for row in financial_table(r) if row[13] in {'revenue','ebitda','gm'}][:3]
        cs,ch=table(wb,'Investment Summary',['Company context','Source-referenced description / financial value','Evidence / units'],profile_rows,r)
        cs.column_dimensions['A'].width=35;cs.column_dimensions['B'].width=115
        cs.row_dimensions[ch+1].height=120
    selected=report_findings(r)
    findings,fh=table(wb,'Findings',['Finding ID','Priority','Finding / conclusion','Investment significance','Supporting metric','Management action','Evidence references','Classification'],finding_rows(r),r)
    evidence,eh=table(wb,'Source Evidence',['Fact ID','Finding ID','Original filename','Worksheet','Cell / source location','Source value / formula','Validated value','Definition / source use','Finding link','Original reference'],source_rows(r,selected),r)
    link_reports(findings,fh,evidence,eh)
    finding_locations={findings.cell(row,1).value:row for row in range(fh+1,findings.max_row+1)}
    if 'Executive Summary' not in original_sheets:
        for index,card in enumerate(present(r)['cards'][:3]):
            target=finding_locations.get(card['id'])
            if target:wb['Executive Summary'].cell(11+index*2,2).hyperlink=f"#'Findings'!A{target}"
    evidence_locations={}
    for row in range(eh+1,evidence.max_row+1):evidence_locations.setdefault(evidence.cell(row,1).value,row)
    for row in range(head+1,perf.max_row+1):
        ref=str(perf.cell(row,13).value or '').split('; ')[0]
        if ref in evidence_locations:perf.cell(row,13).hyperlink=f"#'Source Evidence'!A{evidence_locations[ref]}"
    limitations=[['Accounting basis / scope',r.basis_note],['Comparison availability','Blank comparisons indicate missing periods, incompatible reporting units or basis, or source reconciliation limitations. Gross margin variances are percentage points. Other relative changes use positive comparison balances; no missing figures are inferred.']]
    limitations.extend(['Source limitation',w] for w in dict.fromkeys(r.warnings))
    limitations.extend([item['Analysis'],item['Additional data']] for item in r.readiness if item['Status']!= 'Available')
    quality,qh=table(wb,'Data Quality',['Area','Material limitation / required follow-up'],limitations,r)
    quality.column_dimensions['A'].width=38;quality.column_dimensions['B'].width=115
    exrows=[]
    for f in r.findings:
        ids='; '.join(x['Fact ID'] for x in r.evidence if x['Finding']==f['id'])
        exrows.append([f['id'],f['severity'],f['title'],comparison_text(f['summary'],r,ids.split('; ')),comparison_text(f['calculation'],r,ids.split('; ')),f['action'],ids,f['caveat']])
    checks,checks_head=table(wb,'Exceptions',['Finding','Severity','Description','Result','Calculation','Next action','Evidence / fact IDs','Caveat'],exrows,r)
    # Keep the legacy checks as a clearly separated supporting appendix.
    checks.cell(checks_head-3,1,'Supporting financial checks — primary conclusions are on Findings')
    if 'Extracted Detail' not in original_sheets:wb.move_sheet('Extracted Detail',offset=4 if context else 3)
    # If no exception was detected, source lineage still explains the billing check.
    if r.package.get('skill_engine'):
        import json
        state=r.package['skill_engine']
        rows=[[k,json.dumps(state.get(k),default=str,ensure_ascii=False)] for k in ('engine','status','reason','identity','runtime_seconds','rounds','tool_calls','measurement','pricing_assumptions','coverage','validation','formula_errors','offline_replay')]
        rows.append(['Assurance','Numerical/source checks do not prove narrative explanations, legal enforceability or future outcomes.'])
        execution,execution_head=table(wb,'Analyst Execution',['Measurement','Result'],rows,r)
        execution.column_dimensions['B'].width=115
        # Longer supported reasoning must be readable in generated sheets.
        # Supplied template styles/merges/formulas stay intact; only mapped
        # narrative row heights grow to accommodate supported reasoning.
        import textwrap
        for sheet,first in [(execution,execution_head+1),(wb['Findings'],6)]:
            if sheet.title in original_sheets:continue
            for row in sheet.iter_rows(min_row=first):
                lines=max((sum(max(1,len(textwrap.wrap(part,width=max(10,int(sheet.column_dimensions[c.column_letter].width)-3)))) for part in str(c.value or '').splitlines()) for c in row),default=1)
                sheet.row_dimensions[row[0].row].height=min(409,max(28,lines*14+12))
        fit_template_narratives(wb,narrative_cells)
    wb.calculation=CalcProperties(calcId=191029,fullCalcOnLoad=True)
    out=io.BytesIO(); wb.save(out); data=out.getvalue()
    validate_export(data,r,original_sheets,original_formulas,original_styles,filled)
    check=load_workbook(io.BytesIO(data))
    unresolved=[]
    for ws in check:
        if ws.title == 'Template Guide': continue
        for row in ws:
            for c in row:
                if isinstance(c.value,str) and TOKEN.search(c.value): unresolved.append(f'{ws.title}!{c.coordinate}')
    if unresolved: warnings.append('Unresolved placeholders remain at '+', '.join(unresolved)+'. Output is a draft with unmapped fields, not a completed template.')
    return data,filename,list(dict.fromkeys(warnings))


def validate_export(data,r,original_sheets=(),formulas=None,styles=None,filled=None):
    wb=load_workbook(io.BytesIO(data))
    required=list(original_sheets) if original_sheets else ['Executive Summary','Financial Performance','Findings','Source Evidence','Extracted Detail','Data Quality','Exceptions']
    required+=['Exceptions','Source Evidence','Financial Performance','Findings','Extracted Detail','Data Quality']
    if not set(required)<=set(wb.sheetnames): raise InputError('Export validation failed: missing report sheets.')
    for (sheet,coord),value in (formulas or {}).items():
        if wb[sheet][coord].value!=value or wb[sheet][coord].data_type!='f': raise InputError('Export validation failed: template formula changed.')
    for (sheet,coord),value in (filled or {}).items():
        actual=wb[sheet][coord].value
        equal=math_close(actual,value) if isinstance(actual,(int,float)) and isinstance(value,(int,float)) else actual==value
        if not equal: raise InputError('Export validation failed: mapped value mismatch.')
        if wb[sheet][coord]._style!=(styles or {})[(sheet,coord)]: raise InputError('Export validation failed: template formatting changed.')
    metrics={row[0].value:row[1].value for row in wb['Extracted Detail'] if len(row)>1}
    if r.adaptive:
        for label,value,_,_,_ in r.financial_rows:
            if label not in metrics or not isinstance(metrics[label],(int,float)) or not math_close(metrics[label],value):raise InputError('Export validation failed: normalized financial value mismatch.')
    for label,key in ([] if r.adaptive else [('Platform A revenue','revenue'),('Gross margin actual','gm'),('Reported leverage','leverage_reported'),('Cap-only leverage','leverage_cap')]):
        if key not in r.metrics:
            if label in metrics: raise InputError('Export validation failed: unavailable headline was reported.')
            continue
        if label not in metrics or not isinstance(metrics[label],(int,float)) or not math_close(metrics[label],r.metrics[key]):
            raise InputError('Export validation failed: headline metric mismatch.')
    rows=list(wb['Exceptions'].values)
    for f in r.findings:
        found=[row for row in rows if row[0]==f['id'] and row[2]==f['title']]
        if not found or found[-1][3]!=comparison_text(f['summary'],r,found[-1][6].split('; ')) or not found[-1][6]: raise InputError('Export validation failed: missing finding or evidence.')
    findings={row[0].value:row for row in wb['Findings'] if isinstance(row[0].value,int)}
    sources=list(wb['Source Evidence'].values)
    source_index={}
    for row in sources:
        source_index.setdefault((row[0],row[1],row[2],row[9]),[]).append(row)
    for finding in report_findings(r):
        row=findings.get(finding['id'])
        if row is None or finding['title'] not in str(row[2].value) or not row[6].hyperlink:
            raise InputError('Export validation failed: accepted finding or evidence link missing.')
        if not any(e[1]==finding['id'] for e in sources):raise InputError('Export validation failed: finding source records missing.')
    for e in r.evidence:
        if not any(row[0]==e['Fact ID'] and row[1]==e['Finding'] and row[2]==e['File'] and row[5]==e['Original value / formula'] and (math_close(row[6],e['Validated value']) if isinstance(row[6],(float,int)) and isinstance(e['Validated value'],(float,int)) else row[6]==e['Validated value']) and row[9]==e['Reference'] for row in source_index.get((e['Fact ID'],e['Finding'],e['File'],e['Reference']),[])):
            raise InputError('Export validation failed: original source evidence changed.')
    if not wb['Source Evidence']['A6'].value: raise InputError('Export validation failed: evidence missing.')


def math_close(a,b):
    return abs(a-b)<=max(1e-9,abs(b)*1e-12)
