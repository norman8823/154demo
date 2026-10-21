"""Descriptive source-referenced company context; financial KPIs are local values."""
import re
from collections import defaultdict
from ingestion import digest,clean
from engine import Book,InputError


def source_texts(files):
    sheets=[]
    for name,data in files.items():
        if not name.lower().endswith('.xlsx'):continue
        for ws in list(Book(name,data).wb)[:30]:
            if ws.max_row>1000 or ws.max_column>80:continue
            texts=[(30,dict(id='context_'+digest(name+'|'+ws.title+'|title'),file=name,sheet=ws.title,ref="'"+ws.title+"'![worksheet title]",text=ws.title))]
            for row in ws.iter_rows(max_row=min(ws.max_row,250),max_col=min(ws.max_column,20)):
                for cell in row:
                    text=cell.value
                    if not isinstance(text,str) or text.startswith('=') or not text.strip():continue
                    # Source introductions, service captions, organizational headings,
                    # contract clauses and management assertions remain attributed.
                    score=(20 if cell.row<=4 else 0)+(12 if len(text.split())>=8 else 0)
                    if 4<cell.row<=7 and cell.column>1:score+=40
                    for header_row in range(cell.row-1,max(0,cell.row-15),-1):
                        header=ws.cell(header_row,cell.column).value
                        if isinstance(header,str) and re.fullmatch(r'(?:territory(?: / site)?|branch|practice|segment|subsidiary|division|business unit)',header.strip(),re.I):
                            score+=40;break
                    if re.search(r'territor|geograph|subsidiar|acqui|segment|service|collect|practice|route|industry|contract|business|basis',text,re.I):score+=10
                    texts.append((score,dict(id='context_'+digest(name+'|'+ws.title+'|'+cell.coordinate),file=name,sheet=ws.title,ref="'"+ws.title+"'!"+cell.coordinate,text=text[:500])))
            texts.sort(key=lambda x:(-x[0],x[1]['ref']));sheets.append([v for _,v in texts[:18]])
    result=[]
    while len(result)<120 and any(sheets):
        for queue in sheets:
            if queue and len(result)<120:result.append(queue.pop(0))
    return result


def schema(obj,string):
    citation=obj(dict(source_id=string,quote=string))
    segment=obj(dict(name=string,kind={'type':'string','enum':['geographic territory','operating branch','acquired business','acquired practice','subsidiary','service segment','independent company','unspecified operating unit']},description=string,citations={'type':'array','items':citation,'maxItems':3}))
    return obj(dict(description=string,citations={'type':'array','items':citation,'maxItems':5},segments={'type':'array','items':segment,'maxItems':5}))


def validate(proposal,sources,diagnostics):
    by_id={s['id']:s for s in sources}
    def citations(items):
        if not isinstance(items,list) or not items:raise InputError('Company context requires source citations.')
        accepted=[]
        for c in items:
            source=by_id.get(c.get('source_id')) if isinstance(c,dict) else None
            quote=c.get('quote') if isinstance(c,dict) else None
            if not isinstance(quote,str) or len(quote.strip())<3:raise InputError('Company context quote is absent.')
            if not source or quote not in source['text']:
                matches=[s for s in sources if quote in s['text'] and (not source or s['file']==source['file'])]
                # Exact extractive text can be rebound only when its location is
                # unique or duplicate cells contain identical complete source text.
                if not matches or (len(matches)>1 and len({s['text'] for s in matches})>1):raise InputError('Company context citation is not an unambiguous exact source excerpt.')
                source=sorted(matches,key=lambda s:s['id'])[0]
                diagnostics.append(dict(section='company_context',status='citation_corrected',original_id=c.get('source_id'),source_id=source['id'],reason='Exact quoted source text resolved to its actual supplied record.'))
            accepted.append(dict(source_id=source['id'],quote=quote))
        return accepted
    def prose(text,limit):
        if not isinstance(text,str) or not text.strip() or len(text.split())>limit:raise InputError('Company context exceeds its descriptive scope.')
        if re.search(r'\d|[$%]|\b(?:million|billion|profitable|outperform|underperform|leading|strong|weak)\b',text,re.I):raise InputError('Company context must omit figures and investment judgments; KPIs are supplied locally.')
        return text
    try:
        desc=prose(proposal['description'],55);refs=citations(proposal['citations']);segments=[]
        for item in proposal['segments'][:5]:
            try:
                cited=citations(item['citations']);name=prose(item['name'],9);description=prose(item['description'],20)
                text=' '.join(by_id[c['source_id']]['text'] for c in cited)
                if not re.search(r'\b'+re.escape(clean(name))+r'\b',clean(text)):
                    named=[s for s in sources if clean(s['text'])==clean(name)]
                    if not named:raise InputError('Operating-unit name is not established by its source.')
                    source=sorted(named,key=lambda s:s['id'])[0];cited.append(dict(source_id=source['id'],quote=source['text']));text+=' '+source['text']
                kind=item['kind'];patterns={'geographic territory':r'territor|geograph|region|division','operating branch':r'branch','acquired business':r'acq|acquisition','acquired practice':r'acq|acquisition','subsidiary':r'subsidiar','service segment':r'segment|service|recycl|collect|practice','independent company':r'independent|unrelated|separate portfolio|separate compan'}
                if kind!='unspecified operating unit' and not re.search(patterns.get(kind,r'(?!)'),text,re.I):raise InputError('Organizational relationship is not established by its source.')
                segments.append(dict(item,citations=cited,name=name,description=description))
            except (InputError,KeyError,TypeError) as exc:diagnostics.append(dict(section='company_context',status='rejected_segment',reason=str(exc)))
        return dict(description=desc,citations=refs,segments=segments)
    except (InputError,KeyError,TypeError) as exc:
        diagnostics.append(dict(section='company_context',status='rejected',reason=str(exc)));return {}


def publish(review,profile,sources):
    review.package['company_profile']=profile
    ids={c['source_id'] for item in [profile]+profile.get('segments',[]) for c in item.get('citations',[])}
    for s in sources:
        if s['id'] in ids:review.evidence.append({'Fact ID':s['id'],'Finding':0,'File':s['file'],'Reference':s['ref'],'Original value / formula':s['text'],'Validated value':'Source-referenced business description; not a financial conclusion','Check / use':'Investment Summary company context'})


def text(review):
    p=review.package.get('company_profile',{});description=p.get('description','')
    segments='; '.join(s['name']+' — '+s['kind']+': '+s['description'] for s in p.get('segments',[]))
    return description+(' Operating structure: '+segments if segments else '')


def ensure_context(review,files):
    """Fill descriptive gaps from explicitly mapped source labels, not hypotheses.

    A failed profile citation cannot invent business attributes or erase a usable
    company overview. This fallback never creates an AI investment assessment.
    """
    from ingestion import period
    from investigation_math import retrieve
    profile=dict(review.package.get('company_profile') or {});sources=[]
    books={name:Book(name,data).wb for name,data in files.items() if name.lower().endswith('.xlsx')}
    def source(file,sheet,ref,value):
        record=dict(id='context_'+digest(file+'|'+sheet+'|'+ref),file=file,sheet=sheet,ref="'"+sheet+"'!"+ref,text=str(value));sources.append(record)
        return dict(source_id=record['id'],quote=record['text'])
    if not profile.get('description'):
        activities=[];cited=[];seen=set();current=period(review.report_period)
        for row in review.normalized:
            if not row.get('accepted') or row.get('category')!='revenue' or row.get('role')!='detail' or row.get('scenario')!='actual' or row.get('period')!=current:continue
            if row.get('source_file') not in books:continue
            label=row['label'].strip()
            if clean(label) in {'income','revenue','sales','turnover'} or clean(label) in seen:continue
            seen.add(clean(label));activities.append(label)
            ws=books[row['source_file']][row['source_sheet']];cell=ws[row['source_ref'].split('!')[-1]]
            labelcell=next((c for c in ws[cell.row] if str(c.value).strip()==label),None)
            if labelcell:cited.append(source(row['source_file'],row['source_sheet'],labelcell.coordinate,label))
            if len(activities)==5:break
        if activities:profile.update(description='Reported revenue activities include '+', '.join(activities)+'.',citations=cited,description_basis='mapped source revenue captions')
    if not profile.get('segments'):
        units=[];seen=set()
        for f in retrieve(review,files):
            entity=str(f.get('entity','')).strip();scope=' '.join(str(v) for v in f.get('sheet_context',{}).values())
            if entity in {'','Company total','Reported component group'} or len(entity)>100 or re.match(r'^(?:total|consolidated|company total)\b',entity,re.I):continue
            if re.search(r'\bacq(?:uired|uisition)?\b',entity,re.I):kind='acquired practice' if re.search('practice',f['sheet'],re.I) else 'acquired business'
            elif re.search(r'branch',f['sheet'],re.I) and f.get('parent_entity'):kind='operating branch'
            elif re.search(r'\bterritor',scope,re.I) and f.get('column_label') and re.search(r'\bQ[1-4]\b',f['column_label'],re.I):kind='geographic territory'
            else:continue
            name=re.sub(r'\s*\(acq[^)]*\)','',entity,flags=re.I).strip()
            if not name or clean(name) in seen:continue
            ws=books[f['file']][f['sheet']]
            matches=[c for row in ws.iter_rows(max_row=min(8,ws.max_row)) for c in row if isinstance(c.value,str) and (clean(c.value)==clean(entity) or re.match(r'^'+re.escape(name)+r'\s+Q[1-4]\b',c.value,re.I))]
            if not matches:continue
            c=matches[0];citations=[source(f['file'],f['sheet'],c.coordinate,c.value),source(f['file'],f['sheet'],'[worksheet title]',f['sheet'])]
            if kind=='geographic territory':
                scope_cell=next((c for row in ws.iter_rows(max_row=4) for c in row if isinstance(c.value,str) and re.search(r'\bterritor',c.value,re.I)),None)
                if not scope_cell:continue
                citations.append(source(f['file'],f['sheet'],scope_cell.coordinate,scope_cell.value))
            units.append(dict(name=name,kind=kind,description={'geographic territory':'Geographic operating unit in the territory reporting.','operating branch':'Operating branch identified in branch reporting.','acquired practice':'Acquired practice identified in practice reporting.','acquired business':'Acquired business identified in the source reporting.'}[kind],citations=citations));seen.add(clean(name))
            if len(units)==5:break
        if units:profile['segments']=units
    if profile.get('description') or profile.get('segments'):publish(review,profile,sources)
