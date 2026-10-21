"""Financial checks over normalized records; no worksheet names or coordinates here."""
import calendar
from collections import defaultdict
from engine import Review, NOT_AVAILABLE
from ingestion import MappingRequired, normalized_records, clean,period_grain,period_label


def aggregate(records):
    """Use reported totals once; exclude subtotals from detail sums; expose reconciliation gaps."""
    values={};definitions={};checks=[];ids={}
    pending=[x for x in records if not x.get('accepted',True)]
    records=[x for x in records if x.get('accepted',True)]
    for category in ['revenue','cogs','gross_profit','operating_expenses','ebitda','operating_profit','net_income','interest','tax','depreciation']:
        if category in {'cogs','operating_expenses','interest','tax','depreciation'} and any(x.get('sign_uncertain') for x in records):continue
        total=[x for x in records if x['category']==category and x['role']=='total']
        detail=[x for x in records if x['category']==category and x['role']=='detail']
        if category=='operating_expenses':detail += [x for x in records if x['category']=='depreciation' and x['context']=='operating_expenses']
        if len(total)>1:
            checks.append((category,'Ambiguous duplicate totals; metric omitted.',total));continue
        selected=total or detail
        # An unclassified amount is never silently omitted from a detail-derived total.
        relevant=[x for x in pending if x['category']==category or x['context']==category or
                  (not x['context'] or x['context']=='other') or
                  (x['context']=='below_ebitda' and category in {'interest','tax','depreciation'})]
        if relevant and not total:continue
        if not selected or any(x['value'] is None for x in selected):continue
        values[category]=sum(x['value'] for x in selected)
        definitions[category]='reported: '+clean(total[0]['label']) if total else 'sum of mapped detail accounts'
        ids[category]=selected
        if total and relevant:definitions[category]+='; account-level reconciliation incomplete (unclassified items excluded)'
        if total and detail and not relevant and all(x['value'] is not None for x in detail):
            delta=total[0]['value']-sum(x['value'] for x in detail)
            if abs(delta)>max(.01,abs(total[0]['value'])*1e-6):checks.append((category,f'Reported total differs from mapped detail by {delta:,.2f}.',total+detail))
            else:definitions[category]+='; reconciled to source detail'
    # Defensible identity only when both components exist; never replace a reported metric silently.
    if 'revenue' in values and 'cogs' in values:
        computed=values['revenue']-values['cogs']
        if 'gross_profit' in values and abs(computed-values['gross_profit'])>max(.01,abs(computed)*1e-6):
            checks.append(('gross_profit',f'Revenue less direct costs ({computed:,.2f}) differs from reported gross profit ({values["gross_profit"]:,.2f}).',ids['revenue']+ids['cogs']+ids['gross_profit']))
        elif 'gross_profit' not in values:
            values['gross_profit']=computed;definitions['gross_profit']='calculated: revenue − direct costs';ids['gross_profit']=ids['revenue']+ids['cogs']
    if 'ebitda' not in values and all(k in values for k in ['net_income','interest','tax','depreciation']):
        values['ebitda']=sum(values[k] for k in ['net_income','interest','tax','depreciation'])
        definitions['ebitda']='calculated: net income + explicit interest + income tax + depreciation / amortization'
        ids['ebitda']=sum([ids[k] for k in ['net_income','interest','tax','depreciation']],[])
    elif all(k in values for k in ['ebitda','net_income','interest','tax','depreciation']):
        bridge=sum(values[k] for k in ['net_income','interest','tax','depreciation'])
        if abs(bridge-values['ebitda'])>max(.01,abs(bridge)*1e-6):
            checks.append(('ebitda',f'Reported EBITDA differs from the explicit net-income / interest / tax / D&A bridge by {values["ebitda"]-bridge:,.2f}.',sum([ids[k] for k in ['ebitda','net_income','interest','tax','depreciation']],[])))
        else:definitions['ebitda']+='; reconciled to explicit net-income / interest / tax / D&A bridge'
    bad={category for category,_,_ in checks}
    for category in bad:
        if category in definitions:definitions[category]+='; REQUIRES REVIEW: source reconciliation failed'
    if values.get('revenue',0)>0 and 'gross_profit' in values and not bad & {'revenue','cogs','gross_profit'}:
        values['gm']=values['gross_profit']/values['revenue'];definitions['gm']='calculated: gross profit / revenue';ids['gm']=ids['revenue']+ids['gross_profit']
    return values,definitions,checks,ids


def analyze_intake(intake):
    if not any(any(c.get('period') and c['scenario']!='ignore' and not c.get('invalid') for c in t.columns) and t.accounts for t in intake.tables):raise MappingRequired(intake)
    r=Review();r.adaptive=True;r.currency='unknown';r.scale=None
    r.company=' & '.join(dict.fromkeys(t.company for t in intake.tables))
    r.banner='DRAFT — Source-linked financial review; limitations and investment team review apply'
    r.basis_note='Companies are analyzed separately. Amounts use stated or user-confirmed units; unknown basis or units remain labeled. EBITDA is reported or bridged from explicit net income, interest, tax and depreciation/amortization; operating profit is not treated as EBITDA.'
    groups={};source_counter=0
    r.warnings.extend(intake.warnings)
    for issue in intake.unresolved:r.warnings.append(issue['File']+': '+issue['Reason']+' Other supported statements remain available.')
    for table in intake.tables:
        if table.issues:r.warnings.extend(table.company+': '+issue for issue in dict.fromkeys(table.issues))
        r.evidence.append({'Fact ID':'metadata_'+table.id,'Finding':0,'File':table.file,'Reference':'; '.join(ref for ref,_ in table.metadata_refs) or f"'{table.sheet}' header row {table.header_row}",'Original value / formula':'; '.join(text for _,text in table.metadata_refs),'Validated value':f'{table.company}; {table.basis}; {table.currency}; scale {table.scale}', 'Check / use':'Stated / reviewed table metadata. Unknown metadata is not inferred.'})
        records=normalized_records(table)
        records=[x for x in records if x['period'] and x['scenario']!='ignore']
        pending=[a for a in table.accounts if not (a.confirmed or a.status.startswith('Auto'))]
        if pending:r.warnings.append(f'{table.company} · {table.sheet}: {len(pending)} unconfirmed account(s) excluded from calculated metrics. Reported totals remain source-linked; affected detail-based metrics require review.')
        for record in records:
            source_counter+=1;record['fact_id']=f'financial_{source_counter}'
            r.evidence.append({'Fact ID':record['fact_id'],'Finding':0,'File':table.file,'Reference':record['source_ref'],'Original value / formula':record['raw'],'Validated value':record['value'],'Check / use':f'{record["category"]} / {record["role"]}; {record["period"]} {record["scenario"]}; header {record["header_ref"]}; basis {table.basis}; currency {table.currency}; scale {table.scale if table.scale is not None else "not stated (source units)"}; account {record["label"]}; {record["mapping_status"]}'+(' — excluded from calculations' if not record['accepted'] else '')})
        if any(record['value'] is None for record in records):r.warnings.append(table.company+': missing or dashed source cells remain unavailable; no zero values were inferred. Detail-based metrics omit incomplete categories.')
        r.normalized.extend(records)
        r.recognized.append({'File':table.file,'Recognized as':f'{table.company} · financial statement · {table.sheet}'})
        r.mapping.extend([{'Source account':a.label,'Proposed treatment':a.category,'Role':a.role,'Status':a.status,'Source':table.file+' · '+a.reference} for a in table.accounts])
        by_period=defaultdict(list)
        for record in records:by_period[(record['period'],record['scenario'])].append(record)
        for (period,scenario),rows in by_period.items():
            key=(table.company,period,scenario)
            values,definitions,checks,ids=aggregate(rows)
            entry={'table':table,'values':values,'definitions':definitions,'checks':checks,'ids':ids,'records':rows}
            if key in groups:
                old=groups[key]
                # Prefer the more complete reported statement, never sum overlapping statements.
                score=lambda g:(sum(c['scenario']=='budget' for c in g['table'].columns),sum(x['role']=='total' for x in g['records']))
                primary,secondary=(entry,old) if score(entry)>score(old) else (old,entry)
                basis_conflict=any('Accounting basis conflicts' in issue for item in [old['table'],table] for issue in item.issues)
                same_units=not basis_conflict and (old['table'].currency,old['table'].scale)==(table.currency,table.scale) and (old['table'].basis==table.basis or (old['table'].file==table.file and 'unknown' in {old['table'].basis,table.basis}))
                conflicts={k for k in old['values'].keys()&values.keys() if not same_units or abs(old['values'][k]-values[k])>max(.01,abs(values[k])*1e-6)}
                conflicts|=old.get('blocked_metrics',set())|entry.get('blocked_metrics',set())
                if not same_units:conflicts|=old['values'].keys()|values.keys()
                primary['blocked_metrics']=set(conflicts)
                for metric in conflicts:
                    primary['values'].pop(metric,None)
                    primary['checks'].append((metric,f'Overlapping statements disagree for {metric}; metric omitted pending source review.',old['ids'].get(metric,[])+ids.get(metric,[])))
                if conflicts & {'revenue','cogs','gross_profit'}:primary['values'].pop('gm',None)
                for metric,value in secondary['values'].items():
                    if metric not in primary['values'] and metric not in conflicts and not (metric=='gm' and conflicts & {'revenue','cogs','gross_profit'}):
                        primary['values'][metric]=value;primary['definitions'][metric]=secondary['definitions'][metric];primary['ids'][metric]=secondary['ids'][metric]
                primary['checks'].extend(secondary['checks'])
                groups[key]=primary
                notice=f'{table.company}: overlapping statement periods are not added together; agreeing reported metrics are used once'+(', conflicting metrics require review.' if conflicts else '.')
                if conflicts:
                    if notice not in r.warnings:r.warnings.append(notice)
                elif not any(x['Recognized as']==notice for x in r.recognized):
                    r.recognized.append({'File':table.file,'Recognized as':notice})
            else:groups[key]=entry
    for (company,p,scenario),group in groups.items():
        t=group['table']
        for metric,value in group['values'].items():
            unit='ratio' if metric=='gm' else (t.currency if t.currency!='unknown' and t.scale is not None else 'source units — currency/scale not fully stated')
            r.financial_rows.append([f'{company} · {p} · {scenario} · {metric}',value,unit,group['definitions'][metric],'; '.join(x['fact_id'] for x in group['ids'][metric])])
    companies=list(dict.fromkeys(t.company for t in intake.tables))
    candidates=[];narrative=[];latest_periods=[]
    def candidate(title,summary,indicator,source,priority=2,calculation='',caveat='Comparisons use available mapped statement data. Confirm classification and reporting definitions.',action='Discuss the variance and supporting account detail with the controller.'):
        candidates.append(dict(title=title,summary=summary,indicator=indicator,unit='',source=source,priority=priority,calculation=calculation or summary,caveat=caveat,action=action,conclusion=title,severity='HIGH PRIORITY' if priority==0 else 'REVIEW'))
    for company in companies:
        periods=sorted(p for c,p,s in groups if c==company and s=='actual')
        if not periods:
            r.readiness.append({'Analysis ID':company+'actual','Analysis':company+' · Actual performance','Status':NOT_AVAILABLE,'Additional data':'At least one dated actual statement column is required.'});continue
        # Blank future/template columns do not displace a complete reported period.
        # Populated but contradictory totals remain current and surface their checks.
        def complete(p):
            rows=groups[(company,p,'actual')]['records']
            headlines=[row for row in rows if row.get('accepted') and row['role']=='total' and row['category'] in {'revenue','ebitda'}]
            return bool(headlines) and all(row['value'] is not None for row in headlines)
        completed=[p for p in periods if complete(p)]
        annual=[p for p in completed if period_grain(p)=='annual']
        latest=annual[-1] if annual else (completed[-1] if completed else periods[-1])
        if latest!=periods[-1]:r.warnings.append(company+': later actual columns contain incomplete reported headline values; defaulting to the latest complete actual period, '+latest+'.')
        latest_periods.append(latest);current=groups[(company,latest,'actual')];m=current['values'];t=current['table']
        bad_current={category for category,_,_ in current['checks']}
        prior_periods=[p for p in periods if p<latest and period_grain(p)==period_grain(latest)]
        prior=groups.get((company,prior_periods[-1],'actual')) if prior_periods else None
        # Never combine months across accounting bases, currencies, scales or distinct definitions.
        def comparable(other):
            if any('Accounting basis conflicts' in issue for item in [t,other['table'] if other else t] for issue in item.issues):return False
            return other is not None and other['table'].basis==t.basis and (t.basis!='unknown' or other['table'].file==t.file) and other['table'].currency==t.currency and t.currency!='unknown' and (t.currency!='$' or other['table'].file==t.file) and other['table'].scale==t.scale and t.scale is not None
        budget=groups.get((company,latest,'budget'));budget=budget if comparable(budget) else None
        bad_budget={category for category,_,_ in budget['checks']} if budget else set()
        prior=prior if comparable(prior) else None
        prior_year_period=f'{int(latest[:4])-1:04d}'+latest[4:]
        prior_year=groups.get((company,prior_year_period,'prior_year')) or groups.get((company,prior_year_period,'actual'))
        prior_year=prior_year if comparable(prior_year) else None
        def money(value):return f'{t.currency} {value:,.2f}' if t.currency!='unknown' and t.scale is not None else f'{value:,.2f} source units (currency/scale not fully stated)'
        if len(companies)==1:
            # Compatibility aliases for existing dashboard/template tokens; not consolidation.
            r.metrics.update(m)
            if budget:
                for key in ['revenue','gross_profit','gm','ebitda','operating_expenses']:
                    if key in budget['values']:r.metrics[key+'_budget']=budget['values'][key]
            if prior:
                for key in ['revenue','gm','ebitda']:
                    if key in prior['values']:r.metrics[key+'_prior']=prior['values'][key]
            if prior_year and 'revenue' in prior_year['values']:r.metrics['revenue_prior_year']=prior_year['values']['revenue']
            if m.get('revenue') is not None and budget and budget['values'].get('revenue') and 'revenue' not in bad_current|bad_budget:
                r.metrics['revenue_variance']=m['revenue']/budget['values']['revenue']-1
            if 'gm' in m and budget and 'gm' in budget['values']:r.metrics['gm_variance_pp']=100*(m['gm']-budget['values']['gm'])
            r.currency=t.currency;r.scale=t.scale
        facts=current['ids']
        if 'revenue' in m:narrative.append(f'{company}, {latest}: revenue {money(m["revenue"])} on {t.basis if t.basis!="unknown" else "unstated"} basis.')
        if 'gm' in m:narrative.append(f'Gross margin {m["gm"]:.2%}.')
        if 'ebitda' in m:narrative.append(f'EBITDA {money(m["ebitda"])} ({current["definitions"]["ebitda"]}).')
        bad_current={category for category,_,_ in current['checks']}
        bad_budget={category for category,_,_ in budget['checks']} if budget else set()
        if bad_current:r.warnings.append(company+': source reconciliation requires review for '+', '.join(sorted(bad_current))+'. Reported figures are not repaired; dependent conclusions are limited.')
        if budget and 'ebitda' in m and 'ebitda' in budget['values'] and budget['values']['ebitda'] and 'ebitda' not in bad_current|bad_budget:
            gap=m['ebitda']-budget['values']['ebitda']
            if len(companies)==1:r.metrics['ebitda_variance']=gap
            if abs(gap)>=.05*abs(budget['values']['ebitda']):
                baseline={clean(x['label']):x for x in budget['records'] if x.get('accepted',True) and x['role']=='detail'}
                adverse=[]
                for row in current['records']:
                    old=baseline.get(clean(row['label']))
                    if row.get('accepted',True) and row['category'] in {'cogs','operating_expenses'} and row['role']=='detail' and old and row['value'] is not None and old['value'] is not None and row['value']>old['value']:
                        adverse.append((row['value']-old['value'],row,old))
                drivers=sorted(adverse,key=lambda x:-x[0])[:2]
                summary=f'{latest} EBITDA {money(m["ebitda"])} vs budget {money(budget["values"]["ebitda"])}; variance {money(gap)} ({gap/abs(budget["values"]["ebitda"]):+.1%}). Revenue '+('is above budget despite the earnings miss.' if gap<0 and m.get('revenue',0)>budget['values'].get('revenue',float('inf')) else 'and cost drivers require review.')
                if gap<0 and drivers:summary+=' Largest adverse cost variances: '+'; '.join(x['label']+' '+money(delta) for delta,x,_ in drivers)+'.'
                candidate(company+' · EBITDA '+('below' if gap<0 else 'above')+' budget',summary,money(gap),facts['ebitda']+budget['ids']['ebitda']+sum(([x,y] for _,x,y in drivers),[]),priority=0,action='Reconcile the earnings miss to direct-cost and operating-expense variances; test the recovery assumptions.')
        for aux in intake.auxiliary:
            if (aux['company'],aux['file'],aux['currency'],aux['scale'])!=(company,t.file,t.currency,t.scale):continue
            differences=[];sources=[]
            for row in aux['entries']:
                category=row['category']
                if row['period']!=latest or row['scenario']!='actual' or category not in m:continue
                delta=row['value']-m[category]
                if abs(delta)<=max(.01,abs(m[category])*1e-6):continue
                ref='aux_'+str(len(r.evidence));record=dict(row,fact_id=ref)
                r.evidence.append({'Fact ID':ref,'Finding':0,'File':aux['file'],'Reference':row['source_ref'],'Original value / formula':row['raw'],'Validated value':row['value'],'Check / use':'Dimensional total compared to consolidated statement; no allocation or correction inferred.'})
                sources.extend([record]+facts[category]);differences.append(f'{category}: {money(row["value"])} vs consolidated {money(m[category])} (difference {money(delta)})')
            if differences:
                summary=aux['sheet']+' totals do not reconcile: '+'; '.join(differences)+'. Do not silently allocate the difference to a branch.'
                r.warnings.append(summary)
                candidate(company+' · Branch/entity reconciliation requires review',summary,'Reconcile',sources,priority=0,action='Ask the controller to reconcile branch/entity totals to the consolidated statement before judging branch performance.')
        for category,description,records in current['checks']:
            candidate(company+' · Financial reconciliation requires review',description,'Reconcile',records,priority=0,action='Reconcile the reported subtotal and account mappings to the source statement before relying on derived performance.')
        if budget and m.get('revenue') is not None and budget['values'].get('revenue') and 'revenue' not in bad_current|bad_budget:
            variance=m['revenue']/budget['values']['revenue']-1
            if abs(variance)>=.05:
                candidate(company+' · Revenue '+('below' if variance<0 else 'above')+' budget',f'{latest} revenue {money(m["revenue"])} vs budget {money(budget["values"]["revenue"])} ({variance:+.2%}).',f'{variance:+.1%}',facts['revenue']+budget['ids']['revenue'],priority=1)
        comparison=budget or prior
        if comparison and 'gm' in m and 'gm' in comparison['values']:
            delta=100*(m['gm']-comparison['values']['gm']);label='budget' if budget else 'prior period'
            if abs(delta)>=1:
                candidate(company+' · Gross margin '+('below' if delta<0 else 'above')+' '+label,f'{latest} gross margin {m["gm"]:.2%} vs {label} {comparison["values"]["gm"]:.2%}; {delta:+.2f} percentage points.',f'{delta:+.2f} pp',facts['gm']+comparison['ids']['gm'],priority=1)
        if prior and m.get('revenue') is not None and prior['values'].get('revenue') and 'revenue' not in bad_current and not any(c=='revenue' for c,_,_ in prior['checks']):
            growth=m['revenue']/prior['values']['revenue']-1
            if abs(growth)>1e-10:candidate(company+' · Revenue '+('increased' if growth>0 else 'declined'),f'{latest} revenue {money(m["revenue"])} vs prior available period {money(prior["values"]["revenue"])} ({growth:+.2%}).',f'{growth:+.1%}',facts['revenue']+prior['ids']['revenue'],priority=3)
        ebitda_comparable=bool(prior and 'ebitda' in m and 'ebitda' in prior['values'] and current['definitions']['ebitda']==prior['definitions']['ebitda'])
        if ebitda_comparable:
            change=m['ebitda']-prior['values']['ebitda']
            if abs(change)>1e-10:candidate(company+' · EBITDA '+('increased' if change>0 else 'declined'),f'{latest} EBITDA {money(m["ebitda"])} vs prior available period {money(prior["values"]["ebitda"])}; change {money(change)}. Definition held consistent.',money(change),facts['ebitda']+prior['ids']['ebitda'],priority=4)
        expense_comparable=False
        if comparison:
            baseline={clean(x['label']):x for x in comparison['records'] if x.get('accepted',True) and x['category'] in {'cogs','operating_expenses'} and x['role']=='detail'}
            expense_comparable=any(clean(x['label']) in baseline for x in current['records'] if x.get('accepted',True) and x['category'] in {'cogs','operating_expenses'} and x['role']=='detail')
            for row in current['records']:
                old=baseline.get(clean(row['label']))
                if not row.get('accepted',True) or row['category'] not in {'cogs','operating_expenses'} or row['role']!='detail' or not old or old['value'] is None or row['value'] is None or old['value']<=0:continue
                increase=row['value']-old['value']
                if increase/old['value']>=.25 and increase>=.01*max(abs(m.get('revenue',0)),1):
                    candidate(company+' · Expense outlier: '+row['label'],f'{row["label"]}: {money(row["value"])} vs {money(old["value"])} comparison; increase {money(increase)} ({increase/old["value"]:+.1%}).',money(increase),[row,old],priority=2)
        recon_supported=bool(current['checks']) or any(any(x['category']==category and x['role']=='total' for x in current['records']) and any(x['category']==category and x['role']=='detail' for x in current['records']) for category in ['revenue','cogs','operating_expenses']) or all(key in m for key in ['revenue','cogs','gross_profit'])
        for analysis,ready,need in [
            ('Revenue / financial performance','revenue' in m,'Mapped revenue accounts or a reported revenue total.'),
            ('Gross margin','gm' in m,'Revenue and gross profit or complete direct costs, with reconciled totals.'),
            ('Actual vs. budget',bool(budget and set(m)&set(budget['values'])),'A dated budget column on the same accounting basis and units.'),
            ('Revenue trends',bool(prior and 'revenue' in m and 'revenue' in prior['values']),'Two dated actual revenue periods with stated comparable basis and units.'),
            ('Expense outliers',expense_comparable,'Comparable expense detail in budget or a prior actual period.'),
            ('Accounting reconciliation',recon_supported,'Mapped financial totals and underlying detail.'),
            ('EBITDA trend',ebitda_comparable,'Comparable reported EBITDA definitions, or net income plus explicit interest, income tax and D&A, for two periods.'),
            ('Covenant sensitivity',False,'Debt balances, covenant EBITDA definition, add-back caps and covenant thresholds in a supported covenant schedule.'),
            ('Billing exceptions',False,'Mapped schedule/invoice hours and matched contractual venue/position rates.')]:
            r.readiness.append({'Analysis ID':company+analysis,'Analysis':company+' · '+analysis,'Status':'Available' if ready else NOT_AVAILABLE,'Additional data':'' if ready else need})
        if t.basis=='unknown' and not any('Accounting basis conflicts' in issue for issue in t.issues):r.warnings.append(company+': accounting basis not stated; within-workbook comparisons are as reported, not an independent accounting-basis validation. Cross-workbook comparisons require stated comparable basis.')
        if t.currency=='$':r.warnings.append(company+': dollar units are stated, but the currency jurisdiction is not; no USD identity or FX conversion is inferred.')
        if t.scale is None or t.currency=='unknown':r.warnings.append(company+': units are not fully stated; amounts remain in source units. Confirm currency and scale to enable monetary comparisons.')
    covered={(t.file,t.sheet) for t in intake.tables}|{(a['file'],a['sheet']) for a in intake.auxiliary}
    other=[s['sheet'] for s in intake.text_samples if (s['file'],s['sheet']) not in covered]
    if other:r.warnings.append('Supplementary sheets not interpreted by the financial-statement reader: '+', '.join(dict.fromkeys(other))+'. Narrative, operating-KPI and receivables conclusions are not established by this report.')
    for i,f in enumerate(sorted(candidates,key=lambda f:f['priority'])[:3],101):
        f['id']=i
        source_ids={record['fact_id'] for record in f.pop('source')}
        r.evidence.extend([dict(e,Finding=i) for e in r.evidence[:] if e['Finding']==0 and e['Fact ID'] in source_ids])
        r.findings.append(f)
    r.questions=[f['action'] for f in r.findings]
    if not r.findings:narrative.append('No priority exceptions were established from available mapped records; unavailable checks are not evidence of absence of risk.')
    narrative.extend(f['summary'] for f in r.findings)
    narrative.extend(r.warnings)
    r.memo=' '.join(narrative)+' '+r.basis_note
    if len(set(latest_periods))>1:r.report_period='Multiple reporting periods'
    elif latest_periods:
        latest=max(latest_periods);r.report_period=period_label(latest)
    else:r.report_period='Period requires mapping'
    return r
