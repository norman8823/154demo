"""Source-grounded presentation shared by the dashboard and Excel; no provider calls.

Detailed findings/calculations remain on Review and in the supporting report sheets.
"""
import re


def money(review,value,signed=False):
    prefix='$' if review.currency in {'USD','$'} else review.currency+' '
    if review.currency=='unknown' or review.scale is None:prefix=''
    absolute=abs(value)
    number=f'{absolute/1e6:.2f}M' if absolute>=1e6 else (f'{absolute/1000:,.0f}K' if absolute>=1000 else f'{absolute:,.0f}')
    sign='−' if value<0 else ('+' if signed and value else '')
    return sign+prefix+number+(' source units' if not prefix else '')


def pp(value):return ('−' if value<0 else '+')+f'{abs(value):.1f} pp'


def drivers(review,finding):
    """Reformat only the paired cost records already cited by this finding."""
    ids={e['Fact ID'] for e in review.evidence if e['Finding']==finding['id']}
    rows=[r for r in review.normalized if r.get('fact_id') in ids and r.get('accepted') and r['role']=='detail' and r['category'] in {'cogs','operating_expenses'} and r['value'] is not None]
    result=[]
    for row in rows:
        old=next((r for r in rows if r['scenario']=='budget' and r['period']==row['period'] and r['label']==row['label'] and r['source_file']==row['source_file'] and r['source_sheet']==row['source_sheet']),None)
        if row['scenario']!='actual' or not old or row['value']<=old['value']:continue
        label=re.sub(r'\s*\([^)]*\)','',row['label']).strip()
        if 'overtime' in label.lower():label='Overtime'
        result.append((label,row['value']-old['value'],row['category']))
    return sorted(result,key=lambda x:-x[1])[:2]


def _label(text):return ' '.join(word if word.isupper() else word.lower() for word in text.split())


def _short(text,limit=40):
    """Fallback for uncommon existing finding types, never add a new assertion."""
    text=re.sub(r'\b20\d\d-\d\d\s*','',text)
    text=re.sub(r'(?<=\d)\.00\b','',text)
    words=text.split()
    return text if len(words)<=limit else ' '.join(words[:limit-1]).rstrip(';,.')+'…'


def _gap(summary):
    # Repeated category gaps are not additive. Show the largest absolute gap.
    amounts=re.findall(r'difference (?:[A-Z]{3}\s*|\$\s*)?([−+-]?[\d,]+(?:\.\d+)?)',summary)
    if not amounts:amounts=re.findall(r'\bby ([−+-]?[\d,]+(?:\.\d+)?)',summary)
    values={abs(float(x.replace(',','').replace('−','-'))) for x in amounts}
    return max(values,default=None),len(values)>1


def _financial_present(review):
    """Build a concise view without changing financial checks or original evidence IDs."""
    m=review.metrics;cards=[]
    earnings=next((f for f in review.findings if ' · EBITDA ' in f['title'] and ' budget' in f['title']),None)
    costs=drivers(review,earnings) if earnings else []
    merged=set()
    if earnings and m.get('ebitda_variance',0)<0 and m.get('gm_variance_pp',0)<0 and any(category=='cogs' for _,_,category in costs):
        company=earnings['title'].split(' · ')[0]
        # Combine only same-company budget margin findings with evidenced direct-cost drivers.
        merged={f['id'] for f in review.findings if f['title'].startswith(company+' · Gross margin ') and f['title'].endswith(' budget')}
    for f in review.findings:
        if f['id'] in merged:continue
        title=f['title'].split(' · ',1)[-1];kind='Business performance';adverse=False
        impact=f['indicator'];summary=_short(f['summary']);question=f['action'];amount=None;multiple=False
        if f is earnings:
            title='Profitability below budget' if 'below' in title else 'Profitability ahead of budget'
            gap=m.get('ebitda_variance')
            impact=money(review,gap) if gap is not None else _short(f['indicator'],5)
            summary=('Revenue beat budget, but EBITDA missed plan.' if m.get('revenue_variance',0)>0 and gap is not None and gap<0 else 'EBITDA differs from budget; review the earnings variance.')
            if costs:summary+=' Cost pressure included '+ ' and '.join(_label(label)+' ('+money(review,delta)+' over plan)' for label,delta,_ in costs)+'.'
            if merged and 'gm_variance_pp' in m:summary+=' Gross margin '+('fell ' if m['gm_variance_pp']<0 else 'rose ')+f'{abs(m["gm_variance_pp"]):.1f} pp.'
            adverse=gap is not None and gap<0
            question=('What drove '+ ' and '.join(money(review,delta)+' '+_label(label) for label,delta,_ in costs)+' overruns, and which actions will bring costs back to plan?') if costs else 'Which cost or revenue variances explain the EBITDA gap, and what recovery actions will management commit to?'
        elif 'reconciliation' in title.lower():
            kind='Data quality';amount,multiple=_gap(f['summary']);impact=money(review,amount) if amount is not None else '1 source exception'
            if 'Branch/entity' in title:
                title='Branch reporting needs reconciliation'
                summary='Branch totals differ from the consolidated statement'+(' by '+money(review,amount) if amount is not None else '')+'. Resolve the reporting discrepancy before evaluating branch performance.'+(' This is separate from the earnings miss.' if earnings and m.get('ebitda_variance',0)<0 else ' This is a reporting exception, not an established loss.')
                if multiple:summary='Branch reporting has multiple discrepancies; the largest is '+money(review,amount)+'. Reconcile the statements before evaluating branch performance; these are reporting exceptions, not established losses.'
                question='Can the controller reconcile '+(money(review,amount)+' in ' if amount is not None else 'the ')+'branch-to-consolidated differences before the next investment review?'
            else:
                title='Financial totals need reconciliation'
                summary='Source financial totals do not reconcile. '+_short(f['summary'],22)+' Review affected figures before relying on them.'
                question='Which source totals or account mappings explain the reconciliation difference, and which reported figures require correction?'
        elif not review.adaptive:
            if f['id']==1:
                impact=pp(m['gm_variance_pp']);adverse=m['gm_variance_pp']<0
                summary=f'Gross margin is {m["gm"]:.1%} versus {m["gm_budget"]:.1%} budget. Subcontract labor is {money(review,m["subcontract_variance"])} over plan; event-staffing fill rate is {m["fill"]:.1%}. These warrant follow-up; causation is unconfirmed.'
                question='Which staffing gaps and subcontract rate or volume changes explain the margin variance, and what operating actions will management take?'
            elif f['id']==2:
                kind='Financing risk';impact=f'{m["leverage_cap"]:.2f}x'
                summary=f'Cap-only leverage sensitivity is {m["leverage_cap"]:.2f}x versus {m["leverage_reported"]:.2f}x reported, against a {m["covenant_max"]:.2f}x current limit. Validate permitted add-backs and prepare for the {m["future_max"]:.2f}x March limit; this is not a breach forecast.'
                question=f'What evidence supports the synergy add-back, and what financing plan addresses the {m["future_max"]:.2f}x March covenant limit?'
            elif f['id']==3:
                kind='Reconciliation';impact=money(review,m['billing_total'])
                summary=f'Uninvoiced worked hours and below-contract invoiced rates total {impact} in potential exceptions. Check invoices, credits and contract amendments before treating any amount as recoverable revenue.'
                question='Which flagged worked hours and rate differences remain unbilled after checking invoices, credits and contract amendments?'
        else:
            adverse=('below' in title.lower() or 'declined' in title.lower())
            if title.startswith('Expense outlier:'):title='Cost increase needs review'
            if 'Gross margin' in title and 'gm_variance_pp' in m:impact=pp(m['gm_variance_pp'])
            if title.startswith('Revenue'):
                question='What explains the '+impact+' revenue movement'+(' against budget' if 'budget' in title else '')+', and should management adjust the next forecast?'
            elif title.startswith('Gross margin'):
                question='Which pricing or direct-cost changes explain the '+impact+' margin movement, and what operating response should management approve?'
            elif f['title'].split(' · ',1)[-1].startswith('Expense outlier:'):
                account=f['title'].split('Expense outlier:',1)[-1].strip()
                question='What price, volume or timing changes explain the increase in '+account+', and which spending controls should management approve?'
            elif title.startswith('EBITDA'):
                question='Which operating changes explain the '+impact+' EBITDA movement, and which effects are expected to persist?'
        cards.append(dict(id=f['id'],ids=[f['id']]+(sorted(merged) if f is earnings else []),title=' '.join(title.split()[:8]),impact=impact,summary=_short(summary),kind=kind,adverse=adverse,question=question,amount=amount,multiple_gaps=multiple))
    cards=cards[:3]
    questions=list(dict.fromkeys(c['question'] for c in cards))[:3]
    paragraphs=[]
    if review.adaptive and earnings and 'ebitda' in m and 'ebitda_variance' in m:
        gap=m['ebitda_variance'];direction='below' if gap<0 else 'above'
        bottom=f'EBITDA of {money(review,m["ebitda"])} was {money(review,abs(gap))} {direction} plan.'
        if 'revenue' in m and 'revenue_variance' in m:
            bottom=f'Revenue of {money(review,m["revenue"])} '+('beat' if m['revenue_variance']>=0 else 'missed')+f' budget by {abs(m["revenue_variance"]):.1%}, '+('but ' if m['revenue_variance']>=0 and gap<0 else 'while ')+bottom
        if 'gm' in m and merged:bottom+=f' Gross margin was {m["gm"]:.1%}, '+('down' if m['gm_variance_pp']<0 else 'up')+f' {abs(m["gm_variance_pp"]):.1f} percentage points against budget.'
        if merged and m.get('revenue_variance',0)>0 and gap<0:bottom+=' Higher sales therefore did not translate into planned earnings.'
        key='The largest identified cost pressures were '+ ' and '.join(_label(label)+' ('+money(review,delta)+' above budget)' for label,delta,_ in costs)+'. These contributed to the earnings shortfall; they are not a complete explanation of the variance.' if costs and gap<0 else 'Management should reconcile the earnings variance to the underlying revenue and cost movements before attributing it to a particular driver.'
        risks='Management should separate temporary overruns from recurring costs and present a measurable recovery plan.' if gap<0 else 'Management should test whether the favorable variance is repeatable before updating expectations.'
        branch=next((c for c in cards if c['title']=='Branch reporting needs reconciliation'),None)
        if branch:risks+=' Separately, branch totals differ from the consolidated statement'+(' by '+money(review,branch['amount']) if branch['amount'] is not None else '')+'; reconcile the reporting before judging branch performance.'
        if branch and branch['multiple_gaps']:risks='Management should present a measurable cost recovery plan. Branch reporting has multiple discrepancies, with a largest gap of '+money(review,branch['amount'])+'; reconcile all differences before judging branch performance.'
        paragraphs=[('Bottom line',bottom),('Key drivers',key),('Risks and actions',risks)]
    else:
        # Sparse inputs produce a shorter briefing rather than invented supporting detail.
        if cards:paragraphs=[('Bottom line',cards[0]['summary']),('Risks and actions',' '.join(c['summary'] for c in cards[1:]))]
        else:paragraphs=[('Bottom line','No material findings were established from the available data. This does not establish that unavailable analyses are free of risk.')]
        if review.adaptive and m:
            figures=[label+' '+money(review,m[key]) for label,key in [('Revenue','revenue'),('EBITDA','ebitda')] if key in m]
            if figures:paragraphs[0]=('Bottom line','; '.join(figures)+'. '+paragraphs[0][1])
    notice=[]
    if any('receivables conclusions' in w for w in review.warnings):notice.append('Operating KPIs and AR aging were not analyzed.')
    if any(not row.get('accepted') for row in review.normalized):notice.append('Some account classifications remain uncertain; affected calculations are unavailable.')
    if any('source reconciliation requires review' in w or 'Overlapping statements disagree' in w for w in review.warnings):notice.append('Some source totals require reconciliation; affected conclusions are limited.')
    if review.adaptive and (review.currency=='unknown' or review.scale is None):notice.append('Currency or scale is not established; amounts remain in source units.')
    if review.adaptive and any('accounting basis not stated' in w for w in review.warnings):notice.append('Accounting basis is not stated.')
    if review.adaptive and review.currency=='$':notice.append('Dollar currency jurisdiction is not stated.')
    if not review.adaptive and 'addon_cash_income' in m and 'revenue' in m:notice.append('Platform and acquired-company results use different accounting bases and are shown separately.')
    if not notice and review.warnings:notice.append('Source limitations require review in Data Quality & Coverage.')
    return dict(cards=cards,paragraphs=[(label,text) for label,text in paragraphs if text],questions=questions,notice=' '.join(notice))


def briefing(summary):return '\n\n'.join(label+': '+text for label,text in summary['paragraphs'])


def report_findings(review):
    """One reporting set: accepted AI findings, or the existing offline findings.

    Stored analyses stay intact; this is a presentation projection for cached reviews too.
    """
    from investigation import active_findings
    accepted=active_findings(review)
    if accepted:
        by_id={f['id']:f for f in review.package.get('findings',[])}
        return [dict(by_id.get(i['id'],{}),id=i['id'],title=i['title'],summary=i['text'],
                     action=i.get('action',i['management_question']),refs=i['fact_ids'],severity=i['classification'],
                     why=i['why_it_matters'],positive=i['kind']=='opportunity',ai_kind=i['kind']) for i in accepted]
    return list({f['id']:f for f in review.findings+review.package.get('findings',[])}.values())


def rank_insights(review):
    """Rank accepted findings by cited economic coverage and independence.

    Source breadth is a selection signal, not proof of causation or quantified impact.
    No company names or expected case conclusions enter this policy.
    """
    from investigation import active_findings
    insights=active_findings(review)
    if review.package.get('engine_identity')=='skill':
        return [dict(id=i['id'],score=len(insights)-n,components={'skill_priority':len(insights)-n},topics=[i.get('category','other')],selection_score=len(insights)-n) for n,i in enumerate(insights)]
    if review.package.get('investigation',{}).get('findings'):
        return [dict(id=i['id'],score=len(insights)-n,components={'investigated_priority':len(insights)-n},topics=[i.get('issue_id','initial_analysis')],selection_score=len(insights)-n) for n,i in enumerate(insights)]
    facts={f['id']:f for f in review.package.get('facts',[])+review.package.get('grid_facts',[])}
    for row in review.normalized:
        if row.get('fact_id') not in facts:
            facts[row.get('fact_id')]=dict(label=row.get('label',''),file=row.get('source_file',''),sheet=row.get('source_sheet',''),entity='',unit='money' if row.get('currency')!='unknown' else 'unknown')
    scored=[]
    lenses={
        'earnings_quality':r'normaliz|adjusted ebitda|pre.acquisition|partner compensation|transaction costs|integration costs',
        'cash_conversion':r'\bwip\b|work in process|receivable|write.down|overdue|realization',
        'revenue_quality':r'retention|clients lost|client.*fees|ltm fees',
        'unit_economics':r'ebitda|contribution|gross profit|utilization|chargeable',
        'growth_perimeter':r'revenue|acquisition|acquired|legacy',
    }
    for index,item in enumerate(insights):
        cited=[facts[ref] for ref in item['fact_ids'] if ref in facts]
        labels=' '.join(str(f.get('label','')) for f in cited).lower()
        topics=[key for key,pattern in lenses.items() if re.search(pattern,labels)]
        prose=item.get('text','')+' '+item.get('why_it_matters','')
        if 'growth_perimeter' in topics and not re.search(r'organic|like.for.like|same.perimeter|growth.{0,40}(?:acqui|perimeter)|(?:acqui|perimeter).{0,40}growth',prose,re.I):topics.remove('growth_perimeter')
        sheets={(f.get('file'),f.get('sheet')) for f in cited}
        money=sum(f.get('unit')=='money' for f in cited)
        components=dict(economic_coverage=12*min(len(topics),2),cross_sheet_context=5*min(max(0,len(sheets)-1),1),source_supported_amounts=4*min(money,2),multiple_observations=4 if len(cited)>1 else 0)
        # A scope/normalization question must cite that scope/adjustment; titles alone cannot boost it.
        if 'earnings_quality' in topics:components['underwriting_assumptions']=12
        score=sum(components.values())
        scored.append(dict(id=item['id'],score=score,components=components,topics=topics,refs=set(item['fact_ids']),index=index))
    ranked=[]
    while scored:
        def adjusted(item):
            overlap=max((len(item['refs']&other['refs'])/max(1,len(item['refs']|other['refs'])) for other in ranked),default=0)
            return item['score']-(40 if overlap>.5 else 16*overlap)
        winner=max(scored,key=lambda item:(adjusted(item),-item['index']))
        winner['selection_score']=round(adjusted(winner),2)
        ranked.append(winner);scored.remove(winner)
    return [{k:v for k,v in item.items() if k not in {'refs','index'}} for item in ranked]


def present(review):
    view=review.package.get('view') or _financial_present(review)
    from investigation import active_findings
    accepted=active_findings(review)
    if not accepted:return view
    # Preserve existing accepted-card priorities; legacy exceptions cannot displace AI.
    from copy import deepcopy
    result=deepcopy(view)
    accepted_ids={i['id'] for i in accepted}
    ordered=[c for c in result['cards']+result.get('secondary',[]) if c['id'] in accepted_ids]
    for item in accepted:
        if item['id'] not in {c['id'] for c in ordered}:
            ordered.append(dict(id=item['id'],ids=[item['id']],title=item['title'],impact=item.get('impact',''),
                summary=item['text'],kind=item['classification'],adverse=item['kind']=='risk',
                question=item['management_question'],refs=item['fact_ids'],why=item['why_it_matters']))
    by_id={i['id']:i for i in accepted}
    for card in ordered:
        item=by_id[card['id']]
        card.update(title=item['title'],summary=item['text'],question=item['management_question'],why=item['why_it_matters'])
    ranking=rank_insights(review)
    priorities={item['id']:index for index,item in enumerate(ranking)}
    ordered.sort(key=lambda card:priorities[card['id']])
    result['selection_diagnostics']=ranking
    result['cards']=ordered[:3]
    result['secondary']=ordered[3:]
    result['questions']=[c['question'] for c in result['cards']]
    result['paragraphs']=[('Investment conclusion' if index==0 else c['title'],(c['summary']+' ' if index==0 else '')+c['why']) for index,c in enumerate(result['cards'])]
    if review.package.get('investigation',{}).get('findings'):
        top=[by_id[c['id']] for c in result['cards']]
        result['paragraphs']=[('Investment conclusion',top[0].get('conclusion',top[0]['text'])+' '+top[0].get('assessment',top[0]['why_it_matters'])),('Earnings and cash implications',' '.join(i.get('financial_implication',i['why_it_matters']) for i in top)),('Management priorities',' '.join(i.get('action',i['management_question']) for i in top))]
    elif result['questions']:result['paragraphs'].append(('Management priority',result['questions'][0]))
    return result
