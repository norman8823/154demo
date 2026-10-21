"""Bounded source-cell ledger for model interpretation; never feeds financial aggregation."""
import re
from collections import defaultdict
from engine import Book,InputError
from ingestion import amount,metadata,period,clean,digest,column_period,period_grain


def materiality(fact):
    """Selection relevance only; not a financial conclusion or severity decision."""
    label=str(fact.get('label','')).lower()
    entity=str(fact.get('entity','')).lower()
    context=' '.join(str(v) for v in fact.get('row_context',{}).values()).lower()
    score=4 if fact.get('selection_current') else 0
    if re.search(r'ebitda|net (?:fee )?revenue|gross profit|net income|operating (?:income|profit)|contribution',label):score+=18
    if re.search(r'retention|realization|write.down|work in process|receivable|working capital|normaliz|adjust|pre.acquisition|integration|transaction|compensation',label):score+=14
    if re.search(r'over .*days|overdue|aged|clients lost|departures|utilization|cash flow|capital|lease|fleet|downtime|rental|renewal|price|pricing|per ton|per route',label):score+=12
    if re.search(r'total|consolidated|firm',label+' '+entity):score+=16
    if '$' in label:score+=3
    if re.search(r'departed|notice given|effective|reset|fixed.fee|RFP|below current pricing|competitor|out of service|non.cash|contractual|temporary',context):score+=3
    if fact.get('unit')=='ratio':score+=2
    if fact.get('value')==0:score-=5
    return score


def balanced_select(facts,limit,required=()):
    """Round-robin worksheets and source rows, ranked by financial relevance.

    Financial magnitudes never compete across incompatible currencies or units.
    Repeated monthly rows cannot exhaust the budget before later worksheets.
    """
    unique={f['id']:f for f in facts}
    selected=[unique[k] for k in dict.fromkeys(required) if k in unique][:limit]
    used={f['id'] for f in selected}
    sheets=defaultdict(lambda:defaultdict(list))
    for f in unique.values():
        if f['id'] in used:continue
        row=re.sub(r'\$?[A-Z]+(?=\$?\d+$)','',f.get('ref',''))
        sheets[(f.get('file',''),f.get('sheet',''))][row].append(f)
    queues={}
    for sheet,rows in sorted(sheets.items()):
        ordered=sorted(rows.values(),key=lambda row:(-max(materiality(f) for f in row),min(f.get('ref','') for f in row)))
        for row in ordered:
            numeric_order={}
            compatible=len({(clean(f.get('label')),f.get('unit'),f.get('currency'),f.get('scale')) for f in row})==1
            if compatible and row[0].get('unit') in {'money','ratio'}:
                values=sorted(row,key=lambda f:f['value'])
                if row[0]['unit']=='ratio':
                    extremes=[]
                    while values:
                        extremes.append(values.pop(0))
                        if values:extremes.append(values.pop())
                    numeric_order={f['id']:index for index,f in enumerate(extremes)}
                else:numeric_order={f['id']:index for index,f in enumerate(sorted(row,key=lambda f:-abs(f['value'])))}
            row.sort(key=lambda f:(-materiality(f),not bool(re.search(r'total|firm|consolidated',str(f.get('entity','')),re.I)),numeric_order.get(f['id'],0),f['id']))
        # Diminishing priority within a row balances coherent totals with breadth.
        # A high-value total keeps related operating columns ahead of repetitive detail.
        queue=[(materiality(f)-4*index,f) for row in ordered for index,f in enumerate(row)]
        queue.sort(key=lambda entry:(-entry[0],entry[1]['id']))
        queues[sheet]=[fact for score,fact in queue]
    while len(selected)<limit and any(queues.values()):
        for sheet,queue in queues.items():
            if queue and len(selected)<limit:selected.append(queue.pop(0))
    return selected


def grid_facts(files,limit=350,*,per_sheet_limit=80,predicate=None,include_dated=False):
    facts=[];limitations=[]
    for name,data in files.items():
        if not name.lower().endswith('.xlsx'):continue
        book=Book(name,data);book.strict_sum=False # Explicit Excel SUM semantics, like the financial reader.
        for ws in list(book.wb)[:30]:
            if ws.max_row>1000 or ws.max_column>80:continue
            headers=[]
            for row in range(1,min(ws.max_row,60)+1):
                cells=[ws.cell(row,c).value for c in range(1,ws.max_column+1)]
                if sum(isinstance(v,str) and not v.startswith('=') and amount(v) is None for v in cells)>=2 and not any(amount(v) is not None or (isinstance(v,str) and v.startswith('=')) for v in cells):headers.append(row)
            if not headers:continue
            h=headers[0];company,basis,currency,scale,meta=metadata(ws,h)
            ps={period(c.value) for row in ws.iter_rows(max_row=max(1,h-1)) for c in row if period(c.value)}
            p=next(iter(ps)) if len(ps)==1 else ''
            prefix=' '.join(str(c.value or '') for row in ws.iter_rows(max_row=max(1,h-1)) for c in row)
            if re.search(r'\bltm\b|twelve.month|year.to.date|\bytd\b',prefix,re.I):p='' # Keep multi-period schedules outside monthly claim verification.
            # Read numeric cells before collecting all text context: notes to the right
            # of an amount must never hide that amount.
            entries=[]
            for row in range(h+1,min(ws.max_row,250)+1):
                header=max((r for r in headers if r<row),default=h)
                left=[ws.cell(row,c) for c in range(1,min(ws.max_column,3)+1) if isinstance(ws.cell(row,c).value,str) and not ws.cell(row,c).value.startswith('=') and amount(ws.cell(row,c).value) is None]
                if not left:continue
                row_label=str(left[0].value);label_header=clean(ws.cell(header,left[0].column).value)
                row_metrics=label_header in {'metric','measure','kpi','key performance indicator','account','line','item','description','line item'} or not label_header
                for col in range(left[0].column+1,ws.max_column+1):
                    cell=ws.cell(row,col);head=ws.cell(header,col)
                    if cell.value is None or head.value is None:continue
                    try:value=amount(book.value(ws.title,cell.coordinate))
                    except (InputError,ArithmeticError,ValueError,TypeError,SyntaxError,RecursionError):continue
                    if value is None:continue
                    label=row_label if row_metrics else str(head.value)
                    entity=str(head.value) if row_metrics else ' · '.join(str(c.value) for c in left)
                    unit='ratio' if '%' in cell.number_format else 'unknown'
                    monetary=bool(re.search(r'\$|\b(?:USD|GBP|EUR|CAD|AUD)\b',cell.number_format+' '+label))
                    if unit!='ratio' and monetary and currency!='unknown' and scale is not None:unit='money';value*=scale
                    # Dated headers belong to the existing time-series ledger, not this grid.
                    if not include_dated and row_metrics and re.fullmatch(r'20\d{2}-\d{2}',column_period(head.value)):continue
                    row_context={ws.cell(row,c).coordinate:str(ws.cell(row,c).value)[:240] for c in range(1,ws.max_column+1) if isinstance(ws.cell(row,c).value,str) and not ws.cell(row,c).value.startswith('=') and amount(ws.cell(row,c).value) is None}
                    sheet_context={c.coordinate:str(c.value)[:240] for rr in ws.iter_rows(max_row=h) for c in rr if isinstance(c.value,str) and not c.value.startswith('=') and (c.row==header or c.row<=4)}
                    # Preserve explicit row units and section scopes in mixed grids.
                    unit_cell=next((ws.cell(row,c).value for c in range(1,col) if clean(ws.cell(header,c).value) in {'unit','units','uom'}),'')
                    row_unit=str(unit_cell or '')
                    source_currency,source_scale=currency,scale
                    if row_unit:
                        if row_unit in {'#','count','units','tons','years','days'}:unit={'#':'count','units':'count'}.get(row_unit,row_unit)
                        elif '$' in row_unit:
                            unit='money' if re.fullmatch(r'\$\s*(?:000|in thousands)?',row_unit) else 'money_per_unit'
                            source_currency='$';source_scale=1000 if '000' in row_unit else 1
                            if unit=='money' and not monetary:value*=source_scale
                    if unit=='unknown' and currency!='unknown' and scale is not None and (re.search(r'revenue|ebitda|profit|income|cost|cash|capital|capex|payment|interest|tax|assets?|liabilit|receivable|payable|debt|lease',label,re.I) or re.search(r'income statement|adjusted ebitda|cash flow|balance sheet',prefix,re.I)) and not re.search(r'per |margin|rate|ratio|units|count|days|years|months',label,re.I):
                        unit='money';value*=scale
                    if unit=='unknown' and re.search(r'unit counts',prefix,re.I) and not re.search(r'age|years',label,re.I):unit='count'
                    section=''
                    for prior_row in range(row-1,h,-1):
                        nonempty=[c for c in ws[prior_row] if c.value is not None]
                        if len(nonempty)==1 and isinstance(nonempty[0].value,str) and not nonempty[0].value.startswith('='):
                            section=nonempty[0].value;break
                    exact=column_period(head.value)
                    scope_period=period(section) or p
                    fy=re.match(r'(20\d{2})',scope_period or p or '')
                    quarter=re.search(r'\bQ([1-4])\b',label+' '+str(head.value),re.I)
                    actual_period=exact or (fy[1]+'-FQ'+quarter[1] if fy and quarter else scope_period)
                    scenario='budget' if re.search(r'\bbudget\b',label+' '+section,re.I) and not re.search(r'\(actual\)',label,re.I) else 'actual'
                    if exact:entity='Company total' if row_metrics else entity
                    elif quarter:entity=re.sub(r'\s*Q[1-4].*$','',entity,flags=re.I).strip() or entity
                    if re.search(r'single site',section,re.I):entity=section
                    if re.search(r'\bcompany\b|\bcompanywide\b|\bconsolidated\b',section,re.I):
                        entity='Company total'
                        if period(row_label):actual_period=period(row_label)
                    row_context['section']=section
                    identity='grid_'+digest(name+'|'+ws.title+'|'+cell.coordinate)
                    entries.append(dict(id=identity,file=name,sheet=ws.title,ref="'"+ws.title+"'!"+cell.coordinate,label=label,entity=entity,company=company,period=actual_period,grain=period_grain(actual_period) if actual_period else 'source_schedule',scenario=scenario,basis=basis,unit=unit,currency=source_currency,scale=source_scale,value=value,raw=cell.value,
                                        row_context=row_context,sheet_context=sheet_context,column_label=str(head.value),context_refs=["'"+ws.title+"'!"+coord for coord in dict.fromkeys([*row_context,head.coordinate])],assurance='Source cell evaluated locally; metric meaning/scope require interpretation; no independent financial validation'))
            if predicate is not None:entries=[f for f in entries if predicate(f)]
            facts.extend(balanced_select(entries,per_sheet_limit))
            if len(entries)>per_sheet_limit:limitations.append(name+' · '+ws.title+': AI grid selected up to '+str(per_sheet_limit)+' financially relevant source cells across rows and entities; remaining detail is outside the model context.')
    if len(facts)>limit:limitations.append('AI source grid sampled across worksheets within its '+str(limit)+'-cell bound; remaining detail is outside the model context.')
    return balanced_select(facts,limit),limitations
