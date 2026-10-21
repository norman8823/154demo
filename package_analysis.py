"""Deterministic trends, concentrations, claim tests and evidence-backed investment findings."""
import re
from collections import defaultdict
from ingestion import clean,digest,period
from executive import money,_financial_present

# Broad business concepts; unknown measures remain direction-neutral unless AI maps them.
CONCEPTS=[('retention',r'renewal rate|retention|repeat purchase rate',-1),('churn',r'churn|attrition|cancellation',1),('quality',r'callback|repeat visit|defect|return rate|rework',1),('cost',r'equipment cost|material cost|overtime|cost.*%',1),('utilization',r'utilization|productivity|conversion rate',-1),('pipeline',r'backlog|bookings|order intake',-1),('volume',r'calls completed|systems installed|units sold|shipments|transactions',-1),('ticket',r'average.*ticket|average revenue|average selling price',-1),('collections',r'over 90|past due|overdue|dso|days sales outstanding',1)]


def classify(label):
    for theme,pattern,bad in CONCEPTS:
        if re.search(pattern,label,re.I):return theme,bad
    return 'unknown',0


def series_stats(series):
    points=[p for p in series['points'] if p['scenario']=='actual']
    # Duplicate/conflicting dates are not a valid time series.
    if len({p['period'] for p in points})!=len(points):return None
    points=sorted(points,key=lambda p:p['period'])
    if len(points)<2:return None
    values=[p['value'] for p in points];direction=1 if values[-1]>values[-2] else (-1 if values[-1]<values[-2] else 0)
    streak=0
    for a,b in reversed(list(zip(points,points[1:]))):
        ya,ma=map(int,a['period'].split('-'));yb,mb=map(int,b['period'].split('-'))
        if yb*12+mb-(ya*12+ma)!=1 or direction==0 or (b['value']-a['value'])*direction<=0:break
        streak+=1
    start=points[-streak-1] if streak else points[-2]
    change=values[-1]-start['value'];relative=change/abs(start['value']) if start['value'] else None
    theme,bad=classify(series['label'])
    return dict(series_id=series['id'],label=series['label'],company=series['company'],file=series['file'],sheet=series['sheet'],unit=series['unit'],explicit_unit=series.get('explicit_unit',False),currency=series['currency'],scale=series['scale'],theme=theme,bad_direction=bad,direction=direction,streak=streak,change=change,relative=relative,start=start,latest=points[-1],points=points)


def render(stat,value):
    if stat['unit']=='ratio':return f'{value:.1%}'
    if stat['unit']=='days':return f'{value:.1f} days'
    if stat['unit']=='money':
        class Units:pass
        units=Units();units.currency=stat['currency'];units.scale=stat['scale']
        return money(units,value)
    return f'{value:,.0f}'+(' source units' if stat['unit']=='unknown' else '')


def build(package,review,semantic=None):
    semantic=semantic or {};facts={f['id']:f for f in package['facts']};findings=[]
    stats=[s for series in package['series'] if (s:=series_stats(series))]
    for s in stats:
        proposal=semantic.get('metrics',{}).get(s['series_id'])
        if proposal:s.update(theme=proposal['theme'],bad_direction=proposal['bad_direction'],semantic_proposal=True)
    def add(key,title,summary,impact,refs,theme,action,materiality=0,persistence=0,positive=False,quality=False,entity=''):
        refs=list(dict.fromkeys(refs));identity=2000+len(findings)
        if not refs:return None
        score_parts=dict(materiality=min(40,materiality),persistence=min(20,persistence*3),significance=30 if theme in {'retention','collections','cost','financial'} else 20,evidence_quality=25 if len(refs)>1 else 15)
        item=dict(id=identity,key=key,title=title,summary=summary,indicator=impact,unit='',severity='OPPORTUNITY' if positive else ('DATA QUALITY' if quality else 'INVESTMENT RISK'),calculation=summary,conclusion=summary,caveat='Observed association is not demonstrated causation. Figures cover only the cited periods, units and source definitions.',action=action,refs=refs,theme=theme,positive=positive,quality=quality,entity=entity,score=sum(score_parts.values()),score_components=score_parts)
        findings.append(item);return item
    # Retention/quality/cost trends: require 3 consecutive changes across 4 months.
    for s in stats:
        if s['unit']=='unknown' or not s['bad_direction']:continue
        long_pipeline=s['theme']=='pipeline' and len(s['points'])>=4 and s['points'][0]['value']>0 and s['latest']['value']/s['points'][0]['value']>=1.2
        if s['streak']<3 and not long_pipeline:continue
        if long_pipeline and s['streak']<3:
            s=dict(s,start=s['points'][0],change=s['latest']['value']-s['points'][0]['value'],relative=s['latest']['value']/s['points'][0]['value']-1)
        significant=(abs(s['change'])>=.03 or (abs(s['change'])>=.01 and s['relative'] is not None and abs(s['relative'])>=.2)) if s['unit']=='ratio' else (s['relative'] is not None and abs(s['relative'])>=.1)
        if not significant:continue
        adverse=s['direction']==s['bad_direction'];label=s['label']
        if len(label.split())>7:label=' '.join(label.split()[:7])
        summary=f'{s["label"]} moved from {render(s,s["start"]["value"])} to {render(s,s["latest"]["value"])} across {s["streak"]} consecutive monthly changes.'
        if long_pipeline and s['streak']<3:summary=f'{s["label"]} increased from {render(s,s["start"]["value"])} to {render(s,s["latest"]["value"])} over {len(s["points"])} reported months, with intervening fluctuations.'
        theme=s['theme'];action=f'What explains the change in {s["label"].lower()}, and which customer or operating cohorts should management address first?'
        impact=(f'{s["change"]*100:+.1f} pp' if s['unit']=='ratio' else f'{s["relative"]:+.1%}')
        item=add('trend_'+s['series_id'],label+(' deteriorating' if adverse else ' improving'),summary,impact,[p['id'] for p in s['points'][-s['streak']-1:]],theme,action,materiality=min(30,abs(s['change'])*100) if s['unit']=='ratio' else min(30,abs(s['relative'])*30),persistence=s['streak'],positive=not adverse)
        if item:
            item['series_id']=s['series_id'];item['semantic_proposal']=s.get('semantic_proposal',False)
            if item['semantic_proposal']:item['caveat']+=' The business meaning/direction is an AI interpretation requiring domain confirmation, not numerical validation.'
    # Cohort/base roll-forward is accepted only when the count identity reconciles.
    series_groups=defaultdict(list)
    for st in stats:series_groups[(st['file'],st['sheet'],st['company'])].append(st)
    for group in series_groups.values():
        def one(pattern):
            matches=[st for st in group if st['unit']=='count' and re.search(pattern,st['label'],re.I)]
            return matches[0] if len(matches)==1 else None
        due=one(r'up for renewal|eligible.*renewal|renewals? due')
        renewed=one(r'agreements? renewed|contracts? renewed|subscriptions? renewed|memberships? renewed')
        new=one(r'new.*(agreements?|contracts?|subscriptions?|memberships?).*(sold|added)|gross additions')
        active=one(r'active.*(agreements?|contracts?|subscriptions?|memberships?)')
        if not all([due,renewed,new,active]) or len(active['points'])<2:continue
        latest=active['latest'];opening=active['points'][-2]
        if len({st['latest']['period'] for st in [due,renewed,new,active]})!=1:continue
        lost=due['latest']['value']-renewed['latest']['value'];net=new['latest']['value']-lost
        if lost<0 or abs(opening['value']+net-latest['value'])>.001:continue
        target=next((f for f in findings if f['theme']=='retention' and f.get('series_id') in {st['series_id'] for st in group} and not f['positive']),None)
        if target:
            target['summary']+=f' Latest cohort losses of {lost:,.0f} versus {new["latest"]["value"]:,.0f} additions reconcile to a {net:+,.0f} active-base change.'
            target['refs'] +=[st['latest']['id'] for st in [due,renewed,new,active]]+[opening['id']]
            target['roll_forward']=dict(lost=lost,new=new['latest']['value'],net=net,opening=opening['value'],closing=latest['value'])
            target['score']+=8;target['score_components']['reconciled_cohort']=8

    # Aging calculations use reconciled source buckets, never narrative assertions.
    for aging in package['aging']:
        if not aging['valid']:continue
        total=aging['reported'][0]['total'];buckets=aging['buckets'];col=aging['total_col'];rows=aging['rows']
        overdue_cols=[c for c,label in buckets.items() if label in {'over 90','90','90 days','91','91 120','over 120'}]
        if total<=0 or not overdue_cols:continue
        overdue=sum(r['cells'][c]['value'] for r in rows for c in overdue_cols)
        largest=max(rows,key=lambda r:sum(r['cells'][c]['value'] for c in overdue_cols));largest_overdue=sum(largest['cells'][c]['value'] for c in overdue_cols)
        ratio=overdue/total
        refs=[f['id'] for r in rows for c,f in r['cells'].items() if c in overdue_cols or c==col]
        class Units:pass
        units=Units();units.currency=aging['currency'];units.scale=aging['scale']
        if ratio>=.05:
            summary=f'{money(units,overdue)} of receivables ({ratio:.1%}) is over 90 days; {largest["label"]} accounts for {money(units,largest_overdue)} of that balance. Aging alone does not establish a loss.'
            reserve=next((f for f in aging.get('ledger',[]) if re.search(r'allowance|doubtful',f['label'],re.I)),None)
            if reserve:
                summary+=f' The company allowance is {money(units,abs(reserve["value"]))}; adequacy needs a credit assessment.';refs.append(reserve['id'])
            if aging.get('gl_tie') is False:summary+=' Aging does not reconcile to the general ledger; exposure is provisional.'
            item=add('aging_'+aging['file']+aging['sheet'],'Collections risk is concentrated',summary,money(units,overdue),refs,'collections',f'What is the collection plan for {largest["label"]}, and does the allowance reflect the disputed or aged exposure?',materiality=min(40,ratio*200))
            item['score']+=12;item['score_components']['reconciled_exposure']=12
            item['aging']=dict(total=total,overdue=overdue,ratio=ratio,largest=largest['label'],largest_overdue=largest_overdue,currency=aging['currency'],scale=aging['scale'],allowance=abs(reserve['value']) if reserve else None)
            trend=next((s for s in stats if s['file']==aging['file'] and s['sheet']==aging['sheet'] and s['theme']=='collections' and s['streak']>=3 and s['direction']>0),None)
            if trend:
                item['summary']+=f' {trend["label"]} increased for {trend["streak"]} consecutive months.';item['refs']+= [p['id'] for p in trend['points'][-trend['streak']-1:]];item['score']+=min(20,trend['streak']*3)
        # Receivable concentration is not revenue/customer concentration.
        customer=max(rows,key=lambda r:r['total'])
        if customer['total']/total>=.2:
            add('ar_concentration_'+aging['file'],'Receivables concentration needs monitoring',f'{customer["label"]} represents {customer["total"]/total:.1%} of receivables; this is balance exposure, not revenue concentration.',money(units,customer['total']),[customer['cells'][col]['id'],aging['reported'][0]['cells'][col]['id']],'collections',f'What settlement timing and counterparty controls apply to {customer["label"]}?',materiality=20)
    for cumulative in package.get('cumulative',[]):
        points=cumulative['points'];a,b=points['actual'],points['prior_year']
        if b['value']<=0:continue
        growth=a['value']/b['value']-1
        if growth<.05:continue
        units=dict(unit='money',currency=a['currency'],scale=a['scale'])
        summary=f'YTD {cumulative["label"]} increased {growth:.1%} versus the same prior-year reporting period, to {render(units,a["value"])}.'
        refs=[a['id'],b['id']]
        if 'budget' in points:
            budget=points['budget'];refs.append(budget['id'])
            if budget['value']>0:summary+=f' It remains {a["value"]/budget["value"]-1:+.1%} versus YTD budget.'
        add('ytd_'+a['id'],'YTD '+cumulative['label']+' growth',summary,f'{growth:+.1%}',refs,'momentum','Which initiatives explain the cumulative growth, and how will management close any remaining budget gap?',materiality=min(20,growth*100),positive=True)

    # Business-unit comparisons are within source units/date; contribution is not EBITDA.
    grouped=defaultdict(dict)
    for f in package['units']:grouped[(f['file'],f['sheet'],f['company'],f['period'],f['entity'],f['label'])][f['scenario']]=f
    for key,pair in grouped.items():
        if not {'actual','budget'}<=pair.keys():continue
        a,b=pair['actual'],pair['budget']
        if not re.search(r'contribution|operating (profit|income)|ebitda',a['label'],re.I) or a['unit']!='money' or b['value']<=0:continue
        delta=a['value']-b['value']
        if delta/b['value']>-.1:continue
        summary=f'{a["entity"]} {a["label"].lower()} is {money(review,a["value"])} versus {money(review,b["value"])} plan ({delta/b["value"]:+.1%}). Do not allocate consolidated reconciliation differences to this unit.'
        refs=[a['id'],b['id']]
        peers=[f for f in package['units'] if (f['file'],f['sheet'],f['period'])==(a['file'],a['sheet'],a['period']) and f['scenario']=='actual' and f['entity']==a['entity'] and f['unit']=='ratio' and classify(f['label'])[0] in {'quality','utilization'}]
        for f in peers:
            refs.append(f['id']);summary+=f' Reported {f["label"].lower()}: {f["value"]:.1%}.'
            comparable=[other for other in package['units'] if other['label']==f['label'] and other['entity']!=f['entity'] and (other['file'],other['sheet'],other['period'],other['scenario'])==(f['file'],f['sheet'],f['period'],'actual')]
            if comparable:
                values=[x['value'] for x in comparable];summary+=f' Peers range from {min(values):.1%} to {max(values):.1%}.';refs +=[x['id'] for x in comparable]
        item=add('unit_'+digest('|'.join(key)),a['entity'].split('(')[0].strip()+' contribution under pressure',summary,money(review,delta),refs,'unit',f'What operational actions will restore {a["entity"]} contribution, and which reported operating measures differ from peers?',materiality=min(30,abs(delta)/max(abs(review.metrics.get('revenue',delta)),1)*200),entity=a['entity'])
    # Positive unit performance needs both a revenue beat and a nonnegative contribution comparison.
    for key,pair in grouped.items():
        if not {'actual','budget'}<=pair.keys():continue
        a,b=pair['actual'],pair['budget']
        if not re.search(r'^(net |total )?revenue$',a['label'],re.I) or b['value']<=0 or a['value']/b['value']<1.05:continue
        contributions=[p for k,p in grouped.items() if k[:5]==key[:5] and re.search(r'contribution|operating profit',k[-1],re.I) and {'actual','budget'}<=p.keys() and p['actual']['unit']=='money']
        if len(contributions)!=1 or contributions[0]['actual']['value']<contributions[0]['budget']['value']:continue
        contribution=contributions[0]
        summary=f'{a["entity"]} reported revenue {a["value"]/b["value"]-1:+.1%} above budget and contribution above plan; company-level attribution remains provisional until reconciliation.'
        add('unit_positive_'+digest('|'.join(key)),a['entity'].split('(')[0].strip()+' reported budget beat',summary,f'{a["value"]/b["value"]-1:+.1%}',[a['id'],b['id'],contribution['actual']['id'],contribution['budget']['id']],'unit','Which repeatable operating practices from this unit can management validate and replicate?',materiality=10,positive=True,entity=a['entity'])

    claims=verify_claims(package,review,stats,semantic.get('claims',[]))
    # Attach contradictory management statements to matching investment issue classes.
    for claim in claims:
        if claim['status']!='contradicted':continue
        target=next((f for f in findings if f['theme']==claim['theme'] and not f['positive']),None)
        if target:target['refs']+=claim['refs'];target.setdefault('claims',[]).append(claim['id'])
        else:add('claim_'+claim['id'],'Management explanation needs challenge',claim['assessment'],'Contradicted',claim['refs'],claim['theme'],'How does management reconcile this statement with the cited operating and financial evidence?',materiality=20)
    return dict(stats=stats,findings=findings,claims=claims)


def claim_tokens(text):
    # Conservative English plural normalization, independent of industry vocabulary.
    # Ambiguous or unmatched labels remain unverifiable.
    def singular(word):
        if len(word)>4 and word.endswith('ies'):return word[:-3]+'y'
        if len(word)>3 and word.endswith('s') and not word.endswith(('ss','us','is')):return word[:-1]
        return word
    return {singular(w) for w in clean(text).split()}


def verify_claims(package,review,stats,proposals):
    claims=[];fact_ids={f['id'] for f in package['facts']};stats_by_id={s['series_id']:s for s in stats};quotes={q['id']:q for q in package['narratives']}
    def claim(q,sentence,comparison,selected,theme='unknown'):
        status='unverifiable';assessment='The supplied periods and definitions do not establish this claim.';refs=[q['id']]
        valid=[s for s in selected if s['file']==q['file']]
        if comparison=='record_high' and len(valid)==1:
            s=valid[0];latest=s['latest']['value'];prior=max(p['value'] for p in s['points'][:-1]);refs +=[p['id'] for p in s['points']]
            if latest<prior:status='contradicted';assessment=f'{s["label"]} is {render(s,latest)}, below a prior observed {render(s,prior)}; it is not a record in the supplied history.'
            else:assessment='Latest value is the highest supplied observation; an all-time record cannot be established from limited history.'
        elif comparison=='increasing' and valid:
            outcomes=[s['latest']['value']>=s['points'][-2]['value'] for s in valid];status='supported' if all(outcomes) else 'contradicted';refs +=[p['id'] for s in valid for p in s['points'][-2:]];assessment='The latest comparable observations '+('support' if status=='supported' else 'contradict')+' the claimed increase; causation and longer-term persistence are not established.'
        elif comparison=='majority_current':
            a=next((a for a in package['aging'] if a['valid'] and a['file']==q['file']),None)
            if a:
                current=[c for c,label in a['buckets'].items() if label in {'current','0 30','1 30'}]
                if current:
                    total=a['reported'][0]['total'];value=sum(a['reported'][0]['cells'][c]['value'] for c in current);status='supported' if value>total/2 else 'contradicted';assessment=f'{value/total:.1%} of reconciled receivables is current; this does not demonstrate collectibility of older balances.';refs +=[a['reported'][0]['cells'][c]['id'] for c in current+[a['total_col']]]
        elif comparison=='historically_stable' and len(valid)==1:
            s=valid[0];first=s['points'][0]['value'];last=s['latest']['value'];refs +=[p['id'] for p in s['points']]
            changed=abs(last-first)>=.01 and first!=0 and abs(last/first-1)>.2
            status='contradicted' if changed else 'unverifiable';assessment=f'{s["label"]} changed from {render(s,first)} to {render(s,last)} in the supplied history; historical consistency is screened at ≥1 pp and >20% relative movement, not a causal conclusion.'
        elif comparison=='revenue_above_budget' and 'revenue_variance' in review.metrics:
            status='supported' if review.metrics['revenue_variance']>0 else 'contradicted';assessment='The reported revenue/budget comparison '+('supports' if status=='supported' else 'contradicts')+' the budget assertion; other qualitative explanations are not independently verified.';refs +=[e['Fact ID'] for e in review.evidence if e['Finding']==0 and 'revenue / total' in e['Check / use']]
        elif comparison=='within_budget':
            # Match quoted cost terms to accepted financial labels.
            tokens={w for w in clean(sentence).split() if len(w)>4 and w not in {'costs','expectations','broadly'}}
            records=[r for r in review.normalized if r.get('accepted') and r['source_file']==q['file'] and r['role']=='detail' and r['category'] in {'cogs','operating_expenses'} and tokens & set(clean(r['label']).split())]
            periods=sorted({r['period'] for r in records if r['scenario']=='actual'});pairs=[]
            if periods:
                for r in records:
                    b=next((b for b in records if b['scenario']=='budget' and b['label']==r['label'] and b['source_sheet']==r['source_sheet'] and b['period']==r['period']),None)
                    if r['scenario']=='actual' and r['period']==periods[-1] and b and r['value'] is not None and b['value'] is not None:pairs.append((r,b))
            if pairs:
                actual=sum(a['value'] for a,b in pairs);budget=sum(b['value'] for a,b in pairs)
                if budget>0:
                    variance=actual/budget-1;status='contradicted' if abs(variance)>.05 else 'supported';assessment=f'Matched cost accounts vary {variance:+.1%} from budget under an explicit ±5% alignment screen; volume, mix and unit-price causation require investigation.';refs +=[r['fact_id'] for pair in pairs for r in pair]
        identity='claim_'+digest(q['id']+'|'+sentence)
        claims.append(dict(id=identity,quote_id=q['id'],quote=sentence,status=status,assessment=assessment,refs=list(dict.fromkeys(refs)),theme=theme,tested_assertion=comparison,file=q['file'],sheet=q['sheet'],ref=q['ref']))
    for q in package['narratives']:
        for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z])',q['text']):
            if len(sentence.split())<7:continue
            selected=[];comparison='unsupported';theme='unknown';tokens=set(clean(sentence).split())
            tokens=claim_tokens(sentence)
            candidates=[]
            for s in stats:
                label_tokens=claim_tokens(s['label'])-{'rate','per','of','the','month','end','total','for','up','and','a','to','by'}
                overlap=len(label_tokens & tokens)
                if s['file']==q['file'] and overlap>=2:candidates.append((overlap,s))
            if re.search(r'revenue.*ahead.*budget',sentence,re.I):comparison='revenue_above_budget';theme='financial'
            if re.search(r'\brecord\b|all.time high',sentence,re.I) and candidates:
                stated=[float(n.replace(',','')) for n in re.findall(r'\b\d[\d,]*(?:\.\d+)?',sentence)]
                anchored=[item for item in candidates if any(abs(item[1]['latest']['value']-n)<.01 for n in stated)]
                if len(anchored)==1:
                    best=anchored[0][1];selected=[best];comparison='record_high';theme=best['theme']
            elif re.search(r'quality.*(consistent|historical)',sentence,re.I):
                selected=[s for s in stats if s['file']==q['file'] and s['theme']=='quality' and s['unit']=='ratio'];comparison='historically_stable';theme='quality'
            elif re.search(r'majority.*current',sentence,re.I):comparison='majority_current';theme='collections'
            elif re.search(r'(cost|expense).*(in line|expectations)|in line.*(cost|expense)',sentence,re.I):comparison='within_budget';theme='cost'
            elif re.search(r'continued to (climb|rise|grow)|increased',sentence,re.I) and candidates:
                if re.search(r'average|ticket',sentence,re.I):candidates=[item for item in candidates if item[1]['theme']=='ticket']
                if candidates:
                    best=max(item[0] for item in candidates);selected=[item[1] for item in candidates if item[0]==best];comparison='increasing';theme=selected[0]['theme']
            if re.search(r'\brecord\b|in line|majority|solid|stable|expect|reaffirm|recover|continued|increased|declined|ahead|below|consistent|historical',sentence,re.I):claim(q,sentence,comparison,selected,theme)
    for proposal in proposals:
        q=quotes.get(proposal['quote_id'])
        if q and proposal['quote'] in q['text']:
            selected=[stats_by_id[k] for k in proposal['series_ids'] if k in stats_by_id]
            # A model can propose a test, never its outcome.
            claim(q,proposal['quote'],proposal['comparison'],selected,proposal['theme'])
    return list({c['id']:c for c in claims}.values())


def analysis_findings(review):return review.findings+review.package.get('findings',[])


def enhance(review,package):
    from analyst_ai import interpret
    from engine import InputError
    # Replace the old blanket assertion with measured, per-sheet coverage.
    review.warnings=[w for w in review.warnings if 'Supplementary sheets not interpreted by the financial-statement reader:' not in w]
    base=_financial_present(review)
    initial=build(package,review)
    candidates=[dict(id=c['id'],title=c['title'],summary=c['summary'],indicator=c['impact'],refs=list({e['Fact ID'] for e in review.evidence if e['Finding'] in c['ids']})) for c in base['cards']]+initial['findings']
    try:semantic=interpret(package,initial,candidates,review)
    except InputError as exc:
        semantic=dict(metrics={},claims=[],interpretations={},insights=[],briefing=[],mode=str(exc));package['limitations'].append(str(exc))
    result=build(package,review,semantic)
    for item in semantic.get('insights',[]):
        claim=item['claim_result']
        if claim:
            q=next(q for q in package['narratives'] if q['id']==claim['quote_id'])
            result['claims'].append(dict(claim,id='ai_claim_'+str(item['id']),file=q['file'],sheet=q['sheet'],ref=q['ref'],theme=item['theme']))
        result['findings'].append(dict(id=item['id'],key='ai_'+str(item['id']),title=item['title'],summary=item['text'],indicator=claim['status'].title() if claim else 'Source-linked',
            severity=item['classification'],calculation=item['text']+(' '+claim['assessment'] if claim else ''),conclusion=item['text'],caveat='AI semantic interpretation requires investment-team review. Only an explicitly matched numerical assertion is locally verified; broader implications remain hypotheses.',
            action=item['management_question'],refs=item['fact_ids'],theme=item['theme'],positive=item['kind']=='opportunity',quality=False,entity='',score=126 if claim and claim['status']=='contradicted' else (90 if item['kind']=='opportunity' else 120),score_components={'source_linked_AI_interpretation':120},ai_classification=item['classification'],ai_why=item['why_it_matters']))
    package.update(result);package['mode']=semantic['mode'];package['ai_insights']=semantic.get('insights',[]);package['ai_briefing']=semantic.get('briefing',[]);package['ai_validation']=semantic.get('diagnostics',{})
    # Add a single source ledger, plus finding-specific evidence rows.
    ledger={f['id']:dict(**{'Fact ID':f['id'],'Finding':0,'File':f['file'],'Reference':f['ref'],'Original value / formula':f['raw'],'Validated value':f['value'],'Check / use':f"{f['label']}; {f['period']} {f['scenario']}; grain {f.get('grain','reported_month')}; {f['unit']}; currency {f['currency']}; scale {f['scale']}; entity {f['entity']}; basis {f['basis']}"}) for f in package['facts']}
    ai_refs={ref for item in semantic.get('insights',[]) for ref in item['fact_ids']}|{ref for p in semantic.get('briefing',[]) for ref in p['fact_ids']}
    for f in package.get('grid_facts',[]):
        if f['id'] in ai_refs:ledger[f['id']]={'Fact ID':f['id'],'Finding':0,'File':f['file'],'Reference':f['ref'],'Original value / formula':f['raw'],'Validated value':f['value'],'Check / use':f['assurance']+'; '+f['label']+'; entity '+f['entity']+'; period '+f['period']+'; unit '+f['unit']+'; context '+', '.join(f['context_refs'])}
    for q in package['narratives']:ledger[q['id']]={'Fact ID':q['id'],'Finding':0,'File':q['file'],'Reference':q['ref'],'Original value / formula':q['text'],'Validated value':'Quoted management/source narrative — claim outcome reported separately','Check / use':'Untrusted source statement; not an independently validated fact'}
    ledger.update({e['Fact ID']:e for e in review.evidence if e['Finding']==0})
    review.evidence.extend([e for key,e in ledger.items() if key.startswith(('pkg_','quote_','grid_'))])
    for f in package['findings']:
        review.evidence.extend([dict(ledger[key],Finding=f['id']) for key in f['refs'] if key in ledger])
    # Seed the old, already-reconciled financial findings; keep detailed checks unchanged.
    cards=[]
    for old in base['cards']:
        card=dict(old,refs=list({e['Fact ID'] for e in review.evidence if e['Finding'] in old['ids']}),score=115 if old['kind']=='Business performance' else (135 if 'Financial totals' in old['title'] else 45),theme={'Business performance':'financial','Financing risk':'financing','Reconciliation':'billing','Data quality':'data_quality'}.get(old['kind'],'financial'),positive=(not old['adverse'] and any(word in old['title'].lower() for word in ['above','ahead','increased','improving'])),quality=old['kind']=='Data quality',why='',score_components={'existing_financial_materiality':115 if old['kind']=='Business performance' else 45})
        if old['kind']=='Financing risk':card['score']=105
        if old['kind']=='Reconciliation':card['score']=95
        interpretation=semantic['interpretations'].get(card['id'])
        if interpretation:card['why']=interpretation['why_it_matters']
        cards.append(card)
    # Expand the financial explanation with same-period operating cost evidence, never causation.
    profit=next((c for c in cards if c['title']=='Profitability below budget'),None)
    financial_files={e['File'] for e in review.evidence if profit and e['Finding'] in profit['ids']}
    if profit:
        latest_financial=period(review.report_period)
        related=[f for f in package['findings'] if f['theme']=='cost' and not f['positive'] and any(s['series_id']==f.get('series_id') and s['latest']['period']==latest_financial and s['company']==review.company for s in result['stats']) and any(ledger.get(ref,{}).get('File') in financial_files for ref in f['refs'])]
        if related:
            refs=list(dict.fromkeys(ref for f in related for ref in f['refs']))
            profit['ids']+= [f['id'] for f in related];profit['refs']+=refs
            profit['summary']=profit['summary'].split(' Gross margin')[0]+' Operating cost ratios show persistent pressure; investigate the cited cost measures and their business drivers.'
            profit['summary']=' '.join(profit['summary'].split()[:40])
            profit['why']='Persistent operating cost measures may warrant further investigation; their association with the financial variance does not establish causation.'
            claims=[c for c in package['claims'] if c['status']=='contradicted' and c['theme']=='cost']
            for claim in claims:
                profit['refs']+=claim['refs']
                review.evidence.extend([dict(ledger[key],Finding=profit['id']) for key in claim['refs'] if key in ledger])
    financial_cost_ids=set(profit['ids'][1:]) if profit else set()
    for f in package['findings']:
        if f['id'] in financial_cost_ids:continue
        why={'retention':'Lower retention may weaken recurring revenue; investigate the relevant customer cohorts.','collections':'Aged and concentrated balances could tie up liquidity; collection timing and reserve judgments need attention.','quality':'Adverse quality measures may affect capacity or customer outcomes; investigate root causes before attributing a financial effect.','pipeline':'A stronger order book may support future activity, but conversion, timing and profitability remain unverified.','unit':'Concentrated unit underperformance may warrant targeted operating action; unit contribution is not company EBITDA.','cost':'Rising cost intensity could compress earnings unless pricing, productivity or procurement offsets it.','ticket':'Higher realized tickets may support revenue, but volume and mix need separate review.'}.get(f['theme'],'The movement may affect investment expectations; confirm the business definition and underlying operating drivers.')
        interpretation=semantic['interpretations'].get(f['id'])
        if interpretation:why=interpretation['why_it_matters']
        if f.get('aging'):
            a=f['aging'];u=dict(unit='money',currency=a['currency'],scale=a['scale'])
            text=f'{render(u,a["overdue"])} ({a["ratio"]:.1%} of AR) is over 90 days, including {render(u,a["largest_overdue"])} at {a["largest"]}.'
            if a['allowance'] is not None:text+=f' Company allowance: {render(u,a["allowance"])}.'
            if 'Aging does not reconcile' in f['summary']:text+=' Aging does not reconcile to the general ledger; exposure is provisional.'
            f=dict(f,summary=text+' Assess collections and reserving; loss is unconfirmed.')
        if f['theme']=='retention':f=dict(f,summary=f['summary'].split(' Latest cohort')[0]+' Lower retention may weaken recurring revenue; review cohorts.')
        card=dict(id=f['id'],ids=[f['id']],title=' '.join(f['title'].split()[:8]),impact=f['indicator'],summary=' '.join(f['summary'].split()[:40]),kind='AI-interpreted hypothesis' if f.get('semantic_proposal') else ('Positive development' if f['positive'] else ('Data quality' if f['quality'] else 'Investment risk')),adverse=not f['positive'] and not f['quality'] and not f.get('semantic_proposal'),question=interpretation['management_question'] if interpretation else f['action'],amount=None,multiple_gaps=False,refs=f['refs'],score=f['score'],score_components=f['score_components'],theme=f['theme'],positive=f['positive'],quality=f['quality'],why=why)
        if f.get('ai_classification'):card.update(kind=f['ai_classification'],why=f['ai_why'])
        cards.append(card)
    # Deduplicate themes for the main dashboard; keep distinct detail in the secondary view.
    chosen=[];themes=set()
    for card in sorted(cards,key=lambda c:-c['score']):
        if card['quality'] and card['score']<130:continue
        if card['theme'] in themes:continue
        chosen.append(card);themes.add(card['theme'])
        if len(chosen)==3:break
    secondary=[c for c in cards if c['id'] not in {c['id'] for c in chosen}]
    # Preserve narrow P&L-only/known-adapter behavior when no additional business insight exists.
    if package['findings'] or (not review.adaptive and len(base['cards'])>=2):
        questions=[]
        for card in chosen:
            interpretation=semantic['interpretations'].get(card['id'])
            questions.append(interpretation['management_question'] if interpretation else card['question'])
        if semantic.get('insights'):
            questions=[item['management_question'] for item in semantic['insights'][:3]]
        paragraphs=([(label,p['text']) for label,p in zip(['Investment assessment','Drivers and risks','Management priorities'],semantic['briefing'])] if semantic.get('briefing') else partner_brief(review,base,chosen,secondary))
        notice=base['notice']
        if any(c['quality'] for c in secondary):notice+=' Reporting totals require reconciliation; business-unit attribution is provisional.'
        if package['limitations']:notice+=' Some supporting schedules or interpretations remain limited; see Data Quality & Coverage.'
        package['view']=dict(cards=chosen,secondary=secondary,paragraphs=paragraphs,questions=questions[:3],notice=notice.strip())
    package['coverage_status']='Available' if any(s.get('explicit_unit') for s in package['series']) or package['units'] or any(a['valid'] for a in package['aging']) else 'Not available — additional data required.'
    review.package=package
    review.readiness.append({'Analysis ID':'supporting_schedules','Analysis':'Supporting operating, unit and working-capital schedules','Status':package['coverage_status'],'Additional data':'See worksheet coverage and limitations; recognition is not universal validation.'})
    review.readiness.append({'Analysis ID':'commentary_checks','Analysis':'Management commentary verification','Status':'Available' if any(c['status']!='unverifiable' for c in package['claims']) else 'Not available — additional data required.','Additional data':'Unverifiable claims retain their source quotations and reasons; no future outcome is inferred.'})
    review.warnings.extend(package['limitations'])
    return review


def partner_brief(review,base,chosen,secondary):
    m=review.metrics;paragraphs=[]
    bottom='The supplied schedules support focused operating follow-up. This is a preliminary investment assessment limited to the available evidence, not a complete financial review.'
    if 'revenue' in m:
        bottom=f'Revenue was {money(review,m["revenue"])}'+(f' ({m["revenue_variance"]:+.1%} versus budget)' if 'revenue_variance' in m else '')+'.'
    if 'ebitda' in m:
        bottom+=f' EBITDA was {money(review,m["ebitda"])}'+(' with a '+money(review,abs(m['ebitda_variance']))+' budget '+('shortfall' if m['ebitda_variance']<0 else 'outperformance') if 'ebitda_variance' in m else '')+'.'
        if m.get('revenue_variance',0)>0 and m.get('ebitda_variance',0)<0:bottom+=' Sales growth is not translating into planned earnings.'
    if not review.adaptive:
        bottom='The package calls for focused operating and financing follow-up; the platform and acquired company remain separate accounting views.'
        if 'revenue' in m:bottom+=f' Platform revenue was {money(review,m["revenue"])} ({m["revenue_variance"]:+.1%} versus budget).' 
    paragraphs.append(('Investment assessment',bottom))
    body=[]
    for c in chosen:
        if c['theme']=='financial':
            original=next((text for label,text in base['paragraphs'] if label=='Key drivers'),'')
            body.append(original.split(' These contributed')[0] if original else c['summary'])
            if c['why']:body.append(c['why'])
            if not review.adaptive and m.get('ceo_fill') is not None:body.append(f'The event-staffing fill rate of {m["fill"]:.1%} differs from management commentary of {m["ceo_fill"]:.1%}; confirm the reporting scope.')
        else:
            body.append(re.split(r'(?<=[.!?])\s+',c['summary'])[0])
            if c['theme']=='financing' and 'future_max' in m:body.append(f'The next reported covenant maximum steps down to {m["future_max"]:.2f}x; this sensitivity is not a forecast of breach.')
            if c['theme']=='billing' and 'unbilled' in m:body.append(f'This includes {money(review,m["unbilled"])} of uninvoiced worked hours and {money(review,m["underbilled"])} of rate differences; no recovery is confirmed.')
    paragraphs.append(('Drivers and risks',' '.join(body)))
    positives=sorted((c for c in secondary+chosen if c['positive'] and not c['quality']),key=lambda c:-c['score'])
    steps=[];themes={c['theme'] for c in chosen}
    if m.get('ebitda_variance',0)<0 or themes & {'cost','financial'}:steps.append('test an operating cost recovery plan')
    if themes & {'retention','churn'}:steps.append('review renewal cohorts and cancellation reasons')
    if 'collections' in themes:steps.append('secure aged-account collection plans and assess reserving')
    if 'financing' in themes:steps.append('validate permitted add-backs and prepare for the covenant step-down')
    if 'billing' in themes:steps.append('reconcile billing exceptions before recognizing any recovery')
    actions='Management should '+', '.join(steps or ['validate the business definitions and investigate the cited operating movements'])+'; assign owners and test progress against the next reporting period.'
    if positives:actions='A positive offset is '+positives[0]['summary'][0].lower()+positives[0]['summary'][1:]+' '+positives[0]['why']+' '+actions
    if any(c['quality'] for c in secondary+chosen):actions+=' Reconcile reporting exceptions before attributing the company-level result to a particular business unit.'
    paragraphs.append(('Actions and opportunities',actions))
    # Keep the partner view concise; no arbitrary padding for genuinely sparse packages.
    count=sum(len(text.split()) for _,text in paragraphs)
    if count>195:
        remaining=195;trimmed=[]
        for label,text in paragraphs:
            words=text.split();limit=min(len(words),remaining)
            if label=='Drivers and risks':limit=min(limit,100)
            if limit<len(words):
                sentences=re.split(r'(?<=[.!?])\s+',text);text=''
                for sentence in sentences:
                    if len((text+' '+sentence).split())>limit:break
                    text=(text+' '+sentence).strip()
            trimmed.append((label,text));remaining-=len(text.split())
        paragraphs=trimmed
    return paragraphs
