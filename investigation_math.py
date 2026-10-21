"""Deterministic, source-linked calculations for one bounded investigation pass.

No model-generated expressions, inferred recoveries, valuation assumptions or forecasts.
"""
import re,math
from collections import defaultdict
from ingestion import clean,digest,period,column_period,propose,period_grain
from ai_evidence import grid_facts

TOTAL=re.compile(r'^(?:firm total|company total|total branches|consolidated|company ebitda|amount|total company)',re.I)
TOPICS=r'revenue|ebitda|margin|profit|cost|compensation|normaliz|adjust|retention|client|wip|receivable|overdue|realization|utilization|synerg|leverage|headroom|invoice|billing|cash|debt|callback|aging|\bar\b'


def canonical(f,report_period):
    f=dict(f);f.setdefault('basis','unknown');f.setdefault('scenario','actual')
    header=str(f.get('column_label',''));label=str(f.get('label',''))
    scope=' '.join(str(v) for v in f.get('sheet_context',{}).values())
    end=f.get('period') or period(scope) or report_period
    explicit=column_period(header)
    if explicit:end=explicit
    f['scenario']='budget' if re.search(r'\bbudget\b',header,re.I) else f['scenario']
    if re.search(r'pre.acquisition',label,re.I):grain='source_specific_preownership_period'
    elif explicit and period_grain(explicit)!='month':grain=period_grain(explicit)
    elif f.get('grain') in {'annual','fiscal_quarter'}:grain=f['grain']
    elif re.search(r'\bQ[1-4]\b|quarter',header+' '+label,re.I):grain='quarter'
    elif re.search(r'\bannual\b',header,re.I):grain='annual_rate'
    elif re.search(r'\bytd\b|year.to.date',header+' '+label,re.I):grain='ytd'
    elif re.search(r'\bltm\b|twelve.month',header+' '+label+' '+scope,re.I):grain='ltm'
    else:grain='month' if explicit or f.get('period') else 'snapshot'
    if re.search(r'\bytd\b',header,re.I):
        year=re.search(r'20\d{2}',header)
        if year and end:end=year[0]+end[4:]
    if re.search(r'^(?:total (?:wip|ar|receivables)|(?:wip|ar|receivables) over \d+ days)$',label,re.I):grain='snapshot'
    f.update(period=end,grain=grain)
    if TOTAL.search(header) or clean(header) in {'actual','budget'} and not f.get('parent_entity'):f['entity']='Company total'
    if f.get('parent_entity'):f['entity']=f['parent_entity']
    # Financial captions in a stated-currency schedule establish money, not counts.
    if f['unit']=='unknown' and f.get('currency') not in {'unknown',None} and f.get('scale') is not None:
        category=propose(label,'',True)[0]
        if category in {'revenue','cogs','gross_profit','operating_expenses','ebitda','operating_profit','net_income','interest','tax','depreciation'} or re.search(r'\bcontribution\b',label,re.I):
            f['unit']='money';f['value']*=f['scale']
    if f['unit']=='money' and f.get('currency') not in {'unknown',None} and f.get('scale') is not None:
        f['source_scale']=f['scale'];f['scale']=1
    return f


class Calculations:
    def __init__(self,facts):self.facts={f['id']:f for f in facts};self.derived=[];self.skipped=[]
    def compatible(self,items,*,periods=False,entities=False,scenarios=False):
        if not items or any(f.get('unit') not in {'money','ratio','multiple','pp','count'} or not f.get('period') or f.get('grain') not in {'month','quarter','fiscal_quarter','annual','ytd','ltm','snapshot','covenant_ltm'} for f in items):return False
        if len({(f['unit'],f.get('company'),f['grain']) for f in items})!=1:return False
        if items[0]['unit']=='money' and (any(f.get('currency') in {None,'unknown'} or f.get('scale') is None for f in items) or len({(f['currency'],f['scale']) for f in items})!=1):return False
        if not periods and len({f['period'] for f in items})!=1:return False
        if not entities and len({clean(f.get('entity')) for f in items})!=1:return False
        if not scenarios and len({f.get('scenario') for f in items})!=1:return False
        bases={f.get('basis','unknown') for f in items}
        if len(bases)!=1 or ('unknown' in bases and len({f['file'] for f in items})!=1):return False
        return True
    def make(self,op,ids,label,*,scope='same',unit=None,illustrative=False,notes=(),tags=()):
        if len(self.derived)>=120:return None
        items=[self.facts[k] for k in ids]
        if not self.compatible(items,periods=scope=='yoy',entities=scope=='components',scenarios=scope=='budget'):
            self.skipped.append(dict(label=label,reason='Incompatible or unconfirmed units, basis, entity, period, grain or scenario.'));return None
        if scope=='yoy':
            ps=sorted({f['period'] for f in items})
            if len(ps)!=2 or not all(re.fullmatch(r'\d{4}-(?:\d{2}|FY|F?Q[1-4])',p) for p in ps) or int(ps[1][:4])-int(ps[0][:4])!=1 or ps[1][5:]!=ps[0][5:]:return None
        values=[f['value'] for f in items]
        if op=='sum':value=sum(values)
        elif op=='difference' and len(values)==2:value=values[0]-values[1]
        elif op=='ratio' and len(values)==2 and values[1]>0:value=values[0]/values[1]
        elif op=='growth' and len(values)==2 and values[1]>0:value=values[0]/values[1]-1
        elif op=='pp_difference' and len(values)==2:value=(values[0]-values[1])*100
        else:return None
        if not math.isfinite(value):return None
        base=items[0];identity='calc_'+digest(op+'|'+label+'|'+'|'.join(ids))
        f=dict(base,id=identity,label=label,value=value,unit=unit or ('ratio' if op in {'ratio','growth'} else ('pp' if op=='pp_difference' else base['unit'])),ref='Python '+op,raw=op+'('+', '.join(ids)+')',sheet='Source-linked calculations',source_kind='calculation',inputs=list(ids),source_refs=list(notes),operation=op,illustrative=illustrative,tags=list(tags))
        if scope in {'budget','yoy'}:f['scenario']='comparison'
        if scope=='components':f['entity']='Reported component group'
        if scope=='yoy':f['period']=max(i['period'] for i in items)
        self.facts[identity]=f;self.derived.append(f);return f


def retrieve(review,files):
    """Re-read relevant source grids with a separate finite retrieval budget."""
    from engine import Book
    books={name:Book(name,data).wb for name,data in files.items() if name.lower().endswith('.xlsx')}
    required={k for i in review.package.get('ai_insights',[]) for k in i['fact_ids']}
    raw,_=grid_facts(files,2400,per_sheet_limit=400,include_dated=True,predicate=None)
    records=[]
    for f in raw:
        ws=books[f['file']][f['sheet']];cell=ws[f['ref'].split('!')[-1]]
        # Recover the parent dimension of stacked Actual/Budget headers.
        if clean(f.get('column_label')) in {'actual','budget'}:
            head_ref=f['context_refs'][-1].split('!')[-1];h=ws[head_ref].row
            for r in range(h-1,max(0,h-4),-1):
                candidates=[c for c in ws[r][:cell.column] if isinstance(c.value,str) and c.value.strip() and not c.value.startswith('=')]
                if candidates and candidates[-1].column>=max(2,cell.column-1):
                    f['parent_entity']=str(candidates[-1].value);break
        # Preserve exact field labels/statuses, including tables below the first header.
        numeric_row=cell.row
        for r in range(numeric_row-1,max(0,numeric_row-80),-1):
            values=[c.value for c in ws[r]]
            if sum(isinstance(v,str) and not v.startswith('=') for v in values)>=2 and not any(isinstance(v,(int,float)) or isinstance(v,str) and v.startswith('=') for v in values):
                f['fields']={str(ws.cell(r,c).value):dict(value=str(ws.cell(numeric_row,c).value),ref="'"+ws.title+"'!"+ws.cell(numeric_row,c).coordinate) for c in range(1,ws.max_column+1) if ws.cell(r,c).value is not None and isinstance(ws.cell(numeric_row,c).value,str) and not ws.cell(numeric_row,c).value.startswith('=')};break
        records.append(canonical(f,period(review.report_period)))
    # Existing financial reader remains authoritative for mapped statement values.
    for r in review.normalized:
        if not r.get('accepted') or r['value'] is None:continue
        f=dict(id=r['fact_id'],file=r['source_file'],sheet=r['source_sheet'],ref=r['source_ref'],label=r['label'],unit='money',currency=r['currency'],scale=r['scale'],value=r['value'],raw=r.get('raw',r.get('raw_value')),period=r['period'],grain=r.get('grain',period_grain(r['period'])),scenario=r['scenario'],entity='Company total',company=r.get('company',review.company),basis=r['basis'],category=r['category'],role=r['role'])
        if r['currency']=='unknown' or r['scale'] is None:f['unit']='unknown'
        else:f['source_scale']=f['scale'];f['scale']=1
        records.append(f)
    for f in review.package.get('facts',[]):
        if f.get('grain')=='reported_month':
            record=canonical(f,period(review.report_period));record['grain']='month';records.append(record)
    return list({f['id']:f for f in records}.values())


def calculate(review,records):
    c=Calculations(records);end=period(review.report_period)
    # Statement aliases are already validated aggregates, never fresh inferred totals.
    statements={}
    for label,value,unit,definition,refs in review.financial_rows:
        parts=label.rsplit(' · ',3)
        if len(parts)!=4 or 'REQUIRES REVIEW' in definition:continue
        company,p,scenario,metric=parts;ids=refs.split('; ');sources=[c.facts[i] for i in ids if i in c.facts]
        if not sources or len(sources)!=len(set(ids)):continue
        f=dict(sources[0],id='statement_'+digest(label),label=label,value=value,unit='ratio' if metric=='gm' else sources[0]['unit'],period=p,grain=period_grain(p),scenario=scenario,entity='Company total',company=company,source_kind='validated_statement',inputs=list(dict.fromkeys(ids)),operation='existing_validated_statement',raw=definition,ref='Validated financial statement',sheet='Source-linked calculations')
        c.facts[f['id']]=f;statements[(company,p,scenario,metric)]=f
    for company in {k[0] for k in statements}:
        metrics={}
        for metric in ['revenue','cogs','gross_profit','operating_expenses','ebitda','gm']:
            a=statements.get((company,end,'actual',metric));b=statements.get((company,end,'budget',metric))
            if a and b:
                delta=c.make('pp_difference' if metric=='gm' else 'difference',[a['id'],b['id']],metric+' variance versus budget',scope='budget',tags=['earnings'])
                if delta:metrics[metric]=delta
            prior=f'{int(end[:4])-1:04d}'+end[4:] if end else ''
            y=statements.get((company,prior,'prior_year',metric)) or statements.get((company,prior,'actual',metric))
            if a and y and metric=='revenue':c.make('growth',[a['id'],y['id']],'Reported revenue comparable-period year-over-year change' if period_grain(end)!='month' else 'Reported revenue same-month year-over-year change',scope='yoy',tags=['growth'])
        if all(k in metrics for k in ['revenue','cogs','ebitda']):
            # Negative cost movement is an accounting bridge contribution, not a cause.
            cost=c.make('difference',[metrics['revenue']['id'],metrics['cogs']['id']],'EBITDA variance bridge: revenue less direct-cost movement',tags=['earnings'])
            if cost:
                residual=c.make('difference',[metrics['ebitda']['id'],cost['id']],'Residual EBITDA variance after revenue and direct costs; unattributed',tags=['earnings'])
                if residual:residual['limitation']='Residual is not allocated to a business unit or inferred operating cause.'
        # Only accepted, explicitly classified costs can enter detail contributions.
        pairs=defaultdict(dict)
        for f in records:
            if f.get('category') in {'cogs','operating_expenses'} and f.get('role')=='detail' and f['period']==end and f['company']==company:
                pairs[(f['file'],f['sheet'],clean(f['label']))][f['scenario']]=f
        for pair in sorted(pairs.values(),key=lambda p:-abs(p.get('actual',{}).get('value',0)-p.get('budget',{}).get('value',0)))[:12]:
            if 'actual' in pair and 'budget' in pair:
                c.make('difference',[pair['actual']['id'],pair['budget']['id']],pair['actual']['label']+' cost variance versus budget',scope='budget',tags=['earnings','cost'])
    # Explicitly scoped unit actual/budget comparisons; no allocation of a company miss.
    pairs=defaultdict(dict)
    for f in records:
        if f.get('parent_entity') and f['unit']=='money' and f['period']==end:
            pairs[(f['file'],f['sheet'],f['entity'],f['label'],f['grain'])][f['scenario']]=f
    for pair in pairs.values():
        if 'actual' in pair and 'budget' in pair:
            a,b=pair['actual'],pair['budget']
            if re.search(r'revenue|cost|contribution|gross profit|ebitda',a['label'],re.I):
                c.make('difference',[a['id'],b['id']],a['entity']+' '+a['label']+' variance versus budget',scope='budget',tags=['unit'])
    # Reconciled row components: unit contribution and aged-balance concentration.
    rows=defaultdict(list)
    for f in records:
        if f['id'].startswith('grid_') and f['unit']=='money' and f['scenario']=='actual':rows[(f['file'],f['sheet'],re.sub(r'[A-Z]+(?=\d+$)','',f['ref']),f['period'])].append(f)
    for entries in rows.values():
        totals=[f for f in entries if f['entity']=='Company total'];parts=[f for f in entries if f['entity']!='Company total']
        if len(totals)!=1 or not parts:continue
        total=totals[0]
        if not c.compatible([total]+parts,entities=True) or not math.isclose(sum(f['value'] for f in parts),total['value'],rel_tol=1e-8,abs_tol=.02):continue
        if not re.search(r'revenue|ebitda|contribution|over \d+ days|total wip|total ar',total['label'],re.I):continue
        for f in sorted(parts,key=lambda f:-abs(f['value']))[:6]:
            share=c.make('ratio',[f['id'],total['id']],f['entity']+' share of reported '+total['label'],scope='components',tags=['working_capital' if re.search('wip|ar|receivable',total['label'],re.I) else 'unit'])
            if share:share['reconciliation_refs']=[p['id'] for p in parts];share['source_refs']=[p['id'] for p in parts]
        # Like-for-like proxy needs an explicit same-month legacy-only scope note.
        legacy=[f for f in parts if re.search(r'\blegacy\b',f['entity'],re.I)]
        acquired=[f for f in parts if re.search(r'\bacq(?:uired|uisition)?\b',f['entity'],re.I)]
        if re.search('revenue',total['label'],re.I) and len(legacy)==1 and acquired and total['period']==end and total['grain']=='month':
            year=f'{int(end[:4])-1:04d}'+end[4:]
            notes=[q for q in review.package.get('narratives',[]) if q['file']==total['file'] and period(q['text'])==year and re.search(r'legacy\)?\s+only',q['text'],re.I) and clean(re.sub(r'\s*\(.*','',legacy[0]['entity'])) in clean(q['text'])]
            prior=next((f for (co,p,s,m),f in statements.items() if co==total['company'] and p==year and s in {'actual','prior_year'} and m=='revenue'),None)
            other=[f for f in parts if f not in legacy+acquired and abs(f['value'])>.01]
            if notes and prior and not other:
                proxy=dict(prior,id='scope_'+digest(prior['id']+legacy[0]['entity']),entity=legacy[0]['entity'],inputs=[prior['id']],source_refs=[q['id'] for q in notes],operation='source_scope_alias');c.facts[proxy['id']]=proxy
                growth=c.make('growth',[legacy[0]['id'],proxy['id']],'Source-described legacy revenue same-month YoY proxy; not a full organic growth bridge',scope='yoy',notes=[q['id'] for q in notes],tags=['growth'])
                if growth:
                    growth['limitation']='Comparable perimeter is described by the source note; pricing, disposals and wider organic-growth definitions remain unverified.'
                    c.make('sum',[f['id'] for f in acquired],'Revenue from acquired practices in the current reporting month',scope='components',notes=[q['id'] for q in notes],tags=['growth'])
    # Reported-to-adjusted bridge and an expressly illustrative exclusion sensitivity.
    by_sheet=defaultdict(list)
    for f in records:
        if f['id'].startswith('grid_'):by_sheet[(f['file'],f['sheet'])].append(f)
    for entries in by_sheet.values():
        reported=[f for f in entries if re.search(r'^(?:ltm )?(?:reported ebitda|ebitda[ ,]*(?:as )?reported)$',f['label'],re.I)]
        adjusted=[f for f in entries if re.search(r'^(?:ltm(?: pro forma)? )?(?:pro forma )?adjusted ebitda$',f['label'],re.I)]
        if len(reported)==len(adjusted)==1:
            delta=c.make('difference',[adjusted[0]['id'],reported[0]['id']],'Reported-to-adjusted LTM EBITDA uplift',tags=['earnings_quality'])
            if delta:c.make('ratio',[delta['id'],reported[0]['id']],'Adjusted EBITDA uplift relative to reported LTM EBITDA',tags=['earnings_quality'])
            for item in entries:
                if re.search(r'compensation normalization',item['label'],re.I):
                    c.make('difference',[adjusted[0]['id'],item['id']],'Illustrative adjusted EBITDA excluding the stated compensation normalization',illustrative=True,tags=['earnings_quality'])
        # Listed customer fees are historical exposure indicators, never forecast losses.
        grouped=defaultdict(list)
        for f in entries:
            if not re.search(r'ltm fees',f['label'],re.I) or f['unit']!='money':continue
            fields={clean(k):v for k,v in f.get('fields',{}).items()}
            status=next((v['value'] for k,v in fields.items() if k=='status'),'')
            practice=next((v['value'] for k,v in fields.items() if k in {'practice','business unit','branch'}),None)
            state='departed' if re.search(r'^departed',status,re.I) else ('notice_or_nonrenewal' if re.search(r'notice|nonrenew',status,re.I) else None)
            if state and practice:
                f['entity']=practice;grouped[(practice,state)].append(f)
        for (practice,state),items in grouped.items():
            fee=c.make('sum',[f['id'] for f in items],practice+' listed '+state.replace('_',' ')+' relationships: historical LTM fees',tags=['retention'])
            if fee:fee['limitation']='Listed relationships only; historical fees are not an assumed future revenue loss or recovery.'
    # Same-period cash-flow bridge. Explicit cash-flow captions and source signs
    # are required; noncash finance leases are shown separately from cash capex.
    for entries in by_sheet.values():
        def one(pattern):
            candidates=[f for f in entries if f['unit']=='money' and f.get('grain') in {'annual','ltm','month'} and f['period']==end and re.fullmatch(pattern,f['label'],re.I)]
            return candidates[0] if len(candidates)==1 else None
        ops=one(r'cash flow from operations|net cash (?:provided by|from) operating activities')
        maintenance=one(r'maintenance capital expenditures(?: \(cash\))?')
        growth=one(r'growth capital expenditures(?: \(cash\))?')
        leases=one(r'finance lease principal payments')
        additions=one(r'.*acquired under new finance leases')
        if ops and maintenance and growth and maintenance['value']<=0 and growth['value']<=0:
            investment=c.make('sum',[maintenance['id'],growth['id']],'Signed cash capital expenditure outflows',tags=['cash_investment'])
            if investment:
                after=c.make('sum',[ops['id'],investment['id']],'Cash from operations after cash capital expenditures; before financing',tags=['cash_investment'])
                if after and leases and leases['value']<=0:
                    c.make('sum',[after['id'],leases['id']],'Cash after operations, cash capital expenditures and finance-lease principal; before other financing',tags=['cash_investment'])
                if additions:c.make('difference',[additions['id'],investment['id']],'Cash capital expenditure plus noncash finance-lease additions; total investment, not cash spending',tags=['cash_investment','assets_operations'])
    # Reuse existing validated known-adapter sensitivities; never mix the two companies.
    if not review.adaptive:
        aliases=[('gross_profit','money','Platform monthly gross profit'),('gross_profit_budget','money','Platform monthly budget gross profit'),('subcontract_variance','money','Platform monthly subcontract labor cost variance'),('synergy_trim','money','Illustrative synergy amount excluded under the stated cap'),('cap_ebitda','money','Illustrative cap-only covenant EBITDA'),('reported_ebitda','money','Reported covenant EBITDA'),('headroom_cap','multiple','Illustrative current covenant headroom under cap-only EBITDA'),('billing_total','money','Potential billing exceptions requiring invoice reconciliation')]
        for key,unit,label in aliases:
            if key not in review.metrics:continue
            dependencies={'gross_profit':['gross_profit'],'gross_profit_budget':['gross_profit_budget'],'subcontract_variance':['subcontract','subcontract_budget'],'reported_ebitda':['reported_ebitda'],'synergy_trim':['synergies','synergy_cap','base_platform','pre_acquisition','post_acquisition'],'cap_ebitda':['synergies','synergy_cap','base_platform','pre_acquisition','post_acquisition'],'headroom_cap':['net_debt','covenant_max','synergies','synergy_cap','base_platform','pre_acquisition','post_acquisition']}
            evidence=dependencies.get(key,[e['Fact ID'] for e in review.evidence if e['Fact ID'].startswith('billing_') and type(e.get('Validated value')) in (int,float)])
            if not set(evidence)<={e['Fact ID'] for e in review.evidence}:continue
            if not evidence:continue
            f=dict(id='calc_known_'+key,file='Known validated reporting package',sheet='Source-linked calculations',ref='Existing validated '+key,label=label,value=review.metrics[key],unit=unit,currency='USD',scale=1,period=end,grain='covenant_ltm' if key in {'synergy_trim','cap_ebitda','reported_ebitda','headroom_cap'} else 'month',scenario='budget' if key=='gross_profit_budget' else 'actual',entity='Separate acquired company' if key=='billing_total' else 'Platform',company='Separate acquired company' if key=='billing_total' else 'Platform',basis='separate stated basis',raw='Existing validated adapter metric '+key,source_kind='calculation',inputs=[],source_refs=evidence,operation='existing_validated_adapter',illustrative=key in {'synergy_trim','cap_ebitda','headroom_cap'},tags=['financing' if key in {'synergy_trim','cap_ebitda','reported_ebitda','headroom_cap'} else 'cost'])
            c.facts[f['id']]=f;c.derived.append(f)
        a=c.facts.get('calc_known_gross_profit');b=c.facts.get('calc_known_gross_profit_budget')
        if a and b:c.make('difference',[a['id'],b['id']],'Platform monthly gross-profit variance versus budget',scope='budget',tags=['earnings'])
    return c
