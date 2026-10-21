"""Reporting layouts over validated reviews; no inference or source extraction."""
import calendar
import re
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from executive import present, briefing, report_findings
from engine import company_name
from card_presentation import card_metric

NAVY='18364A'; MUTED='60798A'; PALE='EDF2F5'; RED='AD6262'; GREEN='397A65'
MONEY='#,##0;(#,##0);"—"'
PERCENT='0.0%;(0.0%);"—"'


def period_label(value):
    if re.fullmatch(r'\d{4}-\d{2}',value or ''):
        return calendar.month_abbr[int(value[5:])]+ ' '+value[:4]
    from ingestion import period_label as label
    return label(value)


def shift_month(p,delta):
    if not re.fullmatch(r'\d{4}-\d{2}',p):return None
    total=int(p[:4])*12+int(p[5:])-1+delta
    return f'{total//12:04d}-{total%12+1:02d}'


def comparison_text(text,review,refs=()):
    """Replace ambiguous legacy period wording only when cited dates establish it."""
    if not re.search('prior available period|prior period',text,re.I):return text
    sources={e['Fact ID']:e for e in review.evidence}
    dates=sorted(set(p for ref in refs for p in re.findall(r'\b\d{4}-\d{2}\b',sources.get(ref,{}).get('Check / use',''))))
    if len(dates)==2:
        old,new=dates
        kind='month-over-month' if shift_month(new,-1)==old else ('year-over-year' if shift_month(new,-12)==old else 'period comparison')
        label=f'{period_label(old)} ({kind}; current {period_label(new)})'
    else:label='cited comparison period (dates not established)'
    return re.sub(r'prior available period|prior period',label,text,flags=re.I)


def _metadata(review,refs):
    records=[r for r in review.normalized if r.get('fact_id') in refs]
    return {(r.get('basis'),r.get('currency'),r.get('scale'),r.get('source_file')) for r in records}


def financial_table(review):
    """Pivot existing validated statement values; never sum or bridge new metrics."""
    groups={}
    for label,value,unit,definition,refs in review.financial_rows:
        parts=label.rsplit(' · ',3)
        if len(parts)!=4:continue
        company,p,scenario,metric=parts
        groups[(company,p,scenario,metric)]=dict(value=value,unit=unit,definition=definition,refs=refs.split('; '))
    names={'revenue':'Revenue','cogs':'Direct costs','gross_profit':'Gross profit','gm':'Gross margin','operating_expenses':'Operating expenses','ebitda':'EBITDA','operating_profit':'Operating income','net_income':'Net income','interest':'Interest','tax':'Income tax','depreciation':'Depreciation / amortization'}
    output=[]
    for company in dict.fromkeys(k[0] for k in groups):
        periods=sorted({k[1] for k in groups if k[0]==company and k[2]=='actual'})
        dated=[p for p in periods if re.fullmatch(r'\d{4}-(?:\d{2}|FY|F?Q[1-4])',p)]
        annual=[p for p in dated if p.endswith('-FY')]
        if annual:dated=annual
        if not dated:continue
        complete=[p for p in dated if (company,p,'actual','revenue') in groups]
        p=(complete or dated)[-1]
        for metric,label in names.items():
            a=groups.get((company,p,'actual',metric))
            if not a:continue
            def comparable(other):
                if not other or a['unit']!=other['unit'] or 'REQUIRES REVIEW' in a['definition']+other['definition']:return False
                current=_metadata(review,a['refs']); previous=_metadata(review,other['refs'])
                if not current or not previous:return False
                # Unknown basis is permitted only within the same source file, as in analysis.
                if any(c[1] in (None,'unknown') or c[2] is None for c in current|previous):return False
                return all(c[:3]==o[:3] and (c[0]!='unknown' and c[1]!='$' or c[3]==o[3]) for c in current for o in previous)
            b=groups.get((company,p,'budget',metric))
            y=groups.get((company,(str(int(p[:4])-1)+p[4:]),'prior_year',metric)) or groups.get((company,(str(int(p[:4])-1)+p[4:]),'actual',metric))
            m=groups.get((company,shift_month(p,-1),'actual',metric))
            b=b if comparable(b) else None;y=y if comparable(y) else None;m=m if comparable(m) else None
            val=lambda x:x['value'] if x else None
            change=lambda x: (a['value']-x['value']) if x else None
            relative=lambda x:(a['value']/x['value']-1) if x and x['value']>0 and metric!='gm' else None
            refs=list(dict.fromkeys(a['refs']+sum([x['refs'] for x in (b,y,m) if x],[])))
            output.append([label,a['value'],val(b),change(b),relative(b),val(y),relative(y),val(m),relative(m),a['unit'],period_label(p),company,'; '.join(refs),metric])
    if not output:
        # Existing known adapters expose validated values through compatibility aliases.
        m=review.metrics
        for label,key,unit in [('Platform A revenue','revenue',review.currency),('Gross profit','gross_profit',review.currency),('Gross margin','gm','ratio'),('EBITDA','ebitda',review.currency),('Subcontract labor','subcontract',review.currency),('Reported leverage','leverage_reported','multiple'),('Cap-only leverage','leverage_cap','multiple'),('Potential billing exceptions','billing_total',review.currency),('Add-on B total income (cash basis)','addon_cash_income',review.currency)]:
            if key not in m:continue
            a=m[key];b=m.get(key+'_budget')
            output.append([label,a,b,a-b if b is not None else None,(a/b-1) if b and b>0 and unit!='ratio' else None,None,None,None,None,unit if review.scale is not None else 'source units',review.report_period,'Separate acquired entity' if key=='addon_cash_income' else 'Platform / stated scope','',key])
    return output


def style_performance(ws,head,rows):
    widths=[27,18,18,18,17,18,17,18,17,17,18,35,32]
    for col,width in enumerate(widths,1):ws.column_dimensions[get_column_letter(col)].width=width
    for i,row in enumerate(rows,head+1):
        unit,metric=row[9],row[13]
        fmt=PERCENT if unit=='ratio' else ('0.00"x"' if unit=='multiple' else MONEY)
        for col in (2,3,4,6,8):ws.cell(i,col).number_format=fmt
        if metric=='gm':
            if ws.cell(i,4).value is not None:ws.cell(i,4).value*=100
            ws.cell(i,4).number_format='0.0" pp";(0.0" pp")'
        for col in (5,7,9):ws.cell(i,col).number_format=PERCENT
        ws.cell(i,2).font=Font(bold=True,color=NAVY)
        for col in (4,5,7,9):
            c=ws.cell(i,col)
            if isinstance(c.value,(float,int)) and c.value:
                adverse=c.value>0 if metric in {'cogs','operating_expenses','subcontract','interest'} else c.value<0
                c.font=Font(color=RED if adverse else GREEN)
        ws.row_dimensions[i].height=38
    ws.print_options.horizontalCentered=True
    ws.print_title_rows=f'1:{head}'
    ws.print_area=f'A1:M{head+len(rows)}'


def executive_sheet(wb,review):
    ws=wb.create_sheet('Executive Summary')
    summary=present(review)
    for col in range(1,9):ws.column_dimensions[get_column_letter(col)].width=14
    def merged(row,label,text,height):
        ws.cell(row,1,label);ws.merge_cells(start_row=row,start_column=2,end_row=row,end_column=8)
        c=ws.cell(row,2,text);c.data_type='s';c.alignment=Alignment(wrap_text=True,vertical='top')
        ws.cell(row,1).font=Font(bold=True,color=NAVY,size=10)
        ws.cell(row,1).alignment=Alignment(wrap_text=True,vertical='top')
        ws.row_dimensions[row].height=height
    for row,text in [(1,'PORTFOLIO FINANCIAL REVIEW'),(2,company_name(review)),(3,review.report_period),(4,('Skill analyst · '+review.package['skill_engine']['status'].upper()+' · For Investment Team Review') if review.package.get('skill_engine') else 'For Investment Team Review')]:
        ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=8)
        c=ws.cell(row,1,text);c.font=Font(name='Calibri',size=18 if row==1 else (13 if row==2 else 10),bold=row<3,color=NAVY if row<3 else MUTED)
        ws.row_dimensions[row].height=26 if row<3 else 18
    rows=financial_table(review)
    selected=[next((r for r in rows if r[13]==key),None) for key in ('revenue','ebitda','gm','leverage_reported')]
    selected=[r for r in selected if r is not None]
    if not selected:selected=rows[:4]
    for index,row in enumerate(selected[:4]):
        col=1+index*2
        for line in (6,7,8):ws.merge_cells(start_row=line,start_column=col,end_row=line,end_column=col+1)
        ws.cell(6,col,row[0]).font=Font(color=MUTED,size=10)
        c=ws.cell(7,col,row[1]);c.font=Font(color=NAVY,bold=True,size=20)
        unit=row[9];c.number_format=PERCENT if unit=='ratio' else ('0.00"x"' if unit=='multiple' else MONEY)
        context=row[9]+' · '+row[10]
        if row[4] is not None:context=f'{row[4]:+.1%} vs budget · '+row[9]
        elif row[3] is not None and unit=='ratio':context=f'{row[3]*100:+.1f} pp vs budget'
        ws.cell(8,col,context).font=Font(color=MUTED,size=9)
        ws.cell(8,col).alignment=Alignment(wrap_text=True)
    ws.row_dimensions[7].height=32;ws.row_dimensions[8].height=28
    from company_context import text as context_text
    context=context_text(review)
    if context:
        profile=review.package['company_profile']
        compact=profile.get('description','')
        if profile.get('segments'):compact+=' Structure: '+'; '.join(s['name']+' ('+s['kind']+')' for s in profile['segments'])+'.'
        merged(9,'Investment Summary',compact,70)
    merged(10,'Priority findings','',20)
    for index,card in enumerate(summary['cards'][:3]):
        row=11+index*2
        merged(row,f'Finding {index+1}',card['title'],19)
        text=comparison_text(card['summary'],review,card.get('refs',[]))
        merged(row+1,'',text,47)
    text=briefing(summary)
    text=comparison_text(text,review,[ref for c in summary['cards'] for ref in c.get('refs',[])])
    merged(18,'Investment Assessment',text,135)
    merged(20,'Management Questions','',20)
    for index,question in enumerate(summary['questions'][:3]):merged(21+index,f'Question {index+1}',question,35)
    merged(25,'Review notes','See Data Quality for material limitations, Findings for actions, and Source Evidence for supporting records.',30)
    mode='Accepted AI investment analysis' if review.package.get('ai_insights') else 'Limited offline analysis — no accepted AI investment assessment'
    if review.package.get('skill_engine'):mode=review.package['mode']
    merged(26,'Analysis coverage',mode,40 if review.package.get('skill_engine') else 25)
    for row in ws:
        for c in row:
            if isinstance(c.value,str):c.data_type='s'
            if c.font.name is None:c.font=Font(name='Calibri',size=10,color=NAVY)
    ws.sheet_view.showGridLines=False
    ws.page_setup.orientation='portrait';ws.page_setup.paperSize=ws.PAPERSIZE_A4
    ws.sheet_properties.pageSetUpPr.fitToPage=True
    ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=1
    if review.package.get('skill_engine'):
        import textwrap
        for row in (12,14,16,18,21,22,23,26):
            text=str(ws.cell(row,2).value or '')
            lines=sum(max(1,len(textwrap.wrap(part,width=88))) for part in text.splitlines())
            ws.row_dimensions[row].height=min(409,max(ws.row_dimensions[row].height or 20,lines*13+10))
        ws.page_setup.fitToHeight=0
    ws.print_area='A1:H26';ws.page_margins.left=.3;ws.page_margins.right=.3;ws.page_margins.top=.35;ws.page_margins.bottom=.35
    return ws


def finding_rows(review):
    summary=present(review);findings=report_findings(review)
    order={c['id']:index for index,c in enumerate(summary['cards']+summary.get('secondary',[]))}
    findings=sorted(findings,key=lambda f:order.get(f['id'],999))
    rows=[]
    for f in findings:
        card=next((c for c in summary['cards']+summary.get('secondary',[]) if c['id']==f['id']),None)
        metric=card_metric(card,review)[0] if card else ''
        refs=f.get('refs') or list(dict.fromkeys(e['Fact ID'] for e in review.evidence if e['Finding']==f['id']))
        summary_text=comparison_text(f['summary'],review,refs)
        why=f.get('why') or (card or {}).get('why') or 'Review the reported exposure; financial impact is not independently quantified.'
        rows.append([f['id'],order[f['id']]+1 if f['id'] in order else '',f['title']+'\n'+summary_text,why,metric,f.get('action',''),'; '.join(refs),f.get('severity','Review')])
    return rows


def source_rows(review,findings):
    primary={f['id'] for f in findings}
    entries=[];seen=set()
    for f in findings:
        refs=set(f.get('refs',[]))
        matched=[e for e in review.evidence if e['Finding']==f['id']]
        found={e['Fact ID'] for e in matched}
        matched+= [dict(e,Finding=f['id']) for e in review.evidence if e['Fact ID'] in refs-found]
        entries.extend(matched)
    entries.extend(review.evidence)
    rows=[]
    for e in entries:
        key=(e['Fact ID'],e['Finding'],e['File'],e['Reference'])
        if key in seen:continue
        seen.add(key)
        reference=e['Reference'];match=re.match(r"^(?:'((?:[^']|'')+)'|([^!]+))!(.*)$",reference)
        sheet=(match[1] or match[2]).replace("''", "'") if match else ''
        cell=match[3] if match else reference
        rows.append([e['Fact ID'],e['Finding'],e['File'],sheet,cell,e['Original value / formula'],e['Validated value'],e['Check / use'], 'Return to finding' if e['Finding'] in primary else 'Supporting source record',reference])
    return rows


def link_reports(findings_ws,findings_head,evidence_ws,evidence_head):
    targets={}
    for row in range(evidence_head+1,evidence_ws.max_row+1):
        identity=evidence_ws.cell(row,2).value
        targets.setdefault(identity,row)
    for row in range(findings_head+1,findings_ws.max_row+1):
        identity=findings_ws.cell(row,1).value
        if identity not in targets:continue
        c=findings_ws.cell(row,7)
        c.hyperlink=f"#'{evidence_ws.title.replace(chr(39),chr(39)*2)}'!A{targets[identity]}"
        c.font=Font(color='315F7A',underline='single')
        for erow in range(evidence_head+1,evidence_ws.max_row+1):
            if evidence_ws.cell(erow,2).value!=identity:continue
            back=evidence_ws.cell(erow,9);back.hyperlink=f"#'{findings_ws.title.replace(chr(39),chr(39)*2)}'!A{row}"
            back.font=Font(color='315F7A',underline='single')
    findings_ws.column_dimensions['A'].width=12;findings_ws.column_dimensions['B'].width=12
    for col,width in {'C':62,'D':50,'E':22,'F':52,'G':32,'H':30}.items():findings_ws.column_dimensions[col].width=width
    for row in range(findings_head+1,findings_ws.max_row+1):findings_ws.row_dimensions[row].height=115
    for col,width in {'A':30,'B':12,'C':42,'D':26,'E':24,'F':40,'G':30,'H':65,'I':22,'J':36}.items():evidence_ws.column_dimensions[col].width=width
