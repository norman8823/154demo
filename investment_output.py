"""Validate AI interpretations and render numerical references exclusively from local facts."""
import re
import ast
from engine import InputError
from ingestion import clean


def schema_parts(obj,string,themes):
    refs={'type':'array','items':string,'description':'Nonempty IDs from facts only. Never use commentary quote IDs here; put those in claim.quote_id.'}
    claim=obj(dict(quote_id=string,quote=string,fact_id=string,operator={'type':'string','enum':['none','gt','gte','lt','lte','eq']},threshold=string))
    insight=obj(dict(title=string,theme={'type':'string','enum':themes},kind={'type':'string','enum':['risk','opportunity','relationship']},text=string,why_it_matters=string,management_question=string,fact_ids=refs,claim=claim))
    insight['properties']['title']=dict(string,description='At most eight words; no figures or unsupported conclusions.')
    insight['properties']['text']=dict(string,description='At most 45 words. Numbers MUST use {exact_fact_id} placeholders cited in fact_ids. Never repeat management assertions as verified facts.')
    insight['properties']['why_it_matters']=dict(string,description='At most 35 words; qualified interpretation containing may, could, risk or opportunity. No asserted causation. Numbers only as cited {fact_id} placeholders.')
    insight['properties']['management_question']=dict(string,description='At most 35 words, ending in a question mark. Ask for a concrete investigation or decision. Numbers only as cited {fact_id} placeholders.')
    paragraph=obj(dict(text=string,fact_ids=refs))
    paragraph['properties']['text']=dict(string,description='At most 75 words; up to three paragraphs totaling about 150 words. Every figure uses a cited {fact_id} placeholder; no raw numbers, calculated claims or asserted causes.')
    return dict(insights={'type':'array','items':insight,'maxItems':6},briefing={'type':'array','items':paragraph,'maxItems':3})


def display(f):
    v=f['value']
    if f['unit']=='ratio':return f'{v:.1%}'
    if f['unit']=='multiple':return f'{v:.2f}x'
    if f['unit']=='pp':return f'{v:.1f} pp'
    if f['unit']=='days':return f'{v:.1f} days'
    if f['unit']=='money' and f.get('currency') not in {'unknown',None} and f.get('scale') is not None:
        symbol='$' if f['currency'] in {'USD','$'} else f['currency']+' '
        return symbol+(f'{v:,.2f}' if re.match(r'^\$\s*/',f.get('source_unit_label','')) else f'{v:,.0f}')
    return f'{v:,.2f}'.rstrip('0').rstrip('.')+(' source units' if f['unit'] in {'unknown','money'} else '')


class RejectedFinding(InputError):
    def __init__(self, code, reason, **details):
        super().__init__(reason)
        self.code, self.details = code, details


def asserted_text(text):
    # Negated evidentiary statements are not affirmative causal claims. End the
    # exemption at sentence, clause and contrast boundaries.
    text=re.sub(r'\bnot\s+(?:(?!(?:but|yet|however|although|and|because|is|are|will|does)\b)[\w-]+\s+){0,10}guaranteed\b','NEGATED_GUARANTEE',text,flags=re.I)
    text=re.sub(r'\bnot\s+(?:proof|evidence)\s+(?:that|of)\b(?:(?!\b(?:but|yet|however|although|and|because)\b)[^.!?;])*','',text,flags=re.I)
    return re.sub(r'\b(?:does|do|did)\s+not\s+(?:establish|prove|demonstrate|show|identify|explain|quantify|isolate|attribute|substantiate|confirm|support|verify)\b(?:\s+that\b)?(?:(?!\b(?:but|yet|however|although|and|because)\b)[^.!?;])*','',text,flags=re.I)


def grounded(text,refs,facts,max_words):
    if not isinstance(text,str) or not text.strip() or len(text.split())>max_words:
        raise RejectedFinding('prose_scope', 'AI prose exceeds its scope or length bound.')
    if not isinstance(refs,list) or not all(isinstance(ref,str) for ref in refs):
        raise RejectedFinding('schema_error', 'fact_ids must be an array of strings.')
    refs=set(refs)
    if not refs or not refs<=facts.keys():
        raise RejectedFinding('invalid_fact_ids', 'AI cites unavailable numerical facts.', invalid_ids=sorted(refs-facts.keys()))
    # Placeholders already render denominations. Normalize only redundant
    # matching unit tokens, never alter numbers or infer a conversion.
    for identity in refs:
        f=facts[identity];slot=r'\{'+re.escape(identity)+r'\}'
        if f.get('unit')=='money' and f.get('currency') in {'$','USD'}:
            text=re.sub(r'\$\s*(?='+slot+r')','',text)
        if f.get('unit')!='money' and re.search(r'[$£€]\s*'+slot,text):
            raise RejectedFinding('unit_mismatch','Currency prefix on a nonmonetary fact.')
        if f.get('unit')=='days':
            text=re.sub('('+slot+r')\s+days\b',r'\1',text,flags=re.I)
        if f.get('unit')=='pp':
            text=re.sub('('+slot+r')\s+(?:percentage points?|pp)\b',r'\1',text,flags=re.I)
    slots=re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}',text)
    if not set(slots)<=refs:
        raise RejectedFinding('uncited_placeholder', 'AI numerical reference is not cited.', uncited_ids=sorted(set(slots)-refs))
    plain=text
    # An exact cited monetary aging bucket is a source metric name, not a new
    # numerical claim. Bind the label to its OWN placeholder; amounts, dates,
    # invented buckets and labels attached to another fact remain prohibited.
    for ref in refs:
        fact=facts[ref];label=str(fact.get('label','')).strip()
        aging=r'(?:WIP|AR|work in process|accounts receivable|receivables)\s+(?:over\s+\d+|\d+\s*[-–]\s*\d+)\s+days'
        if fact.get('unit')=='money' and re.fullmatch(aging,label,re.I):
            pattern=r'(?<!\w)'+re.escape(label)+r'(?=\s+(?:is|are|of|at|was|were)\s+\{'+re.escape(ref)+r'\})'
            plain=re.sub(pattern,'SOURCE_AGING_BUCKET',plain,flags=re.I)
    plain=re.sub(r'\{[A-Za-z][A-Za-z0-9_]*\}','',plain)
    # A cited source entity identifier is a name, never a financial quantity.
    # Exempt only exact role-prefixed IDs; fabricated IDs and literal figures still fail.
    for ref in refs:
        entity=re.sub(r'\s*\([^)]*\)\s*$','',str(facts[ref].get('entity',''))).strip()
        if re.fullmatch(r'(?:venue|branch|unit|region|division|entity|account|customer)\s+[0-9]{1,6}',entity,re.I):
            plain=re.sub(r'(?<![\w$%])'+re.escape(entity)+r'(?![\w%]|\.\d)','SOURCE_ENTITY',plain,flags=re.I)
    # Period labels, age-bucket captions and source identifiers are descriptors,
    # never permission to supply raw amounts. Bind them to the cited source cell.
    descriptor_refs=set(refs)
    pending=list(refs)
    while pending:
        for parent in facts[pending.pop()].get('inputs',[]):
            if parent in facts and parent not in descriptor_refs:
                descriptor_refs.add(parent);pending.append(parent)
    for ref in descriptor_refs:
        fact=facts[ref];header=str(fact.get('column_label',''));label=str(fact.get('label',''))
        # Fiscal-year captions are descriptors only when bound to a cited
        # metric's own source header and placeholder, never free numerical claims.
        if ref in descriptor_refs-refs or '{'+ref+'}' in text:
            for fy in re.findall(r'\bFY\s?20\d{2}\b',header,re.I)+fact.get('source_period_labels',[]):
                plain=re.sub(r'\b'+re.escape(fy)+r'\b','SOURCE_FISCAL_YEAR',plain,flags=re.I)
        # Aging-bucket descriptors can be reworded, but their boundary must
        # come from this cited source label/header, never its amount.
        aging_source=header+' '+label
        threshold=re.search(r'(?:over|>)\s*(\d+)\s*days?|\b(\d+)\s*\+\s*days?',aging_source,re.I)
        if threshold and fact.get('unit')=='money' and (ref in descriptor_refs-refs or '{'+ref+'}' in text):
            days=threshold.group(1) or threshold.group(2)
            plain=re.sub(r'\bover[ -]'+days+r'[ -]days?\b|\b'+days+r'\+[- ]days?\b','SOURCE_AGING_BUCKET',plain,flags=re.I)
        q=re.search(r'\bQ([1-4])\b',header+' '+label,re.I)
        if not q:q=re.search(r'(?:F?Q)([1-4])$',str(fact.get('period','')))
        if q and (ref in descriptor_refs-refs or '{'+ref+'}' in text):
            plain=re.sub(r'\bQ'+q[1]+r'\b','SOURCE_QUARTER',plain,flags=re.I)
        entity=re.split(r'\s*[·(]',str(fact.get('entity','')))[0].strip()
        if re.fullmatch(r'(?:(?:national|regional|key|major)\s+)?(?:account|customer|client|venue|branch|unit|region|division|entity)\s+\d{1,6}',entity,re.I):
            plain=re.sub(r'(?<![\w$%])'+re.escape(entity)+r'(?![\w%]|\.\d)','SOURCE_ENTITY',plain,flags=re.I)
        if re.fullmatch(r'\d+\+?\s*(?:[-–]\s*\d+)?\s+years',label,re.I):
            own=r'\{'+re.escape(ref)+r'\}(?:\s+\w+){0,5}\s+'+re.escape(label)
            if re.search(own,text,re.I):plain=re.sub(re.escape(label),'SOURCE_AGE_BUCKET',plain,flags=re.I)
    # A counted source group is descriptive only when its OWN total is a
    # recorded sum of exactly that many distinct raw source cells.
    number_words={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
    def sum_terms(node):
        if isinstance(node,ast.Name):return [node.id]
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
            left,right=sum_terms(node.left),sum_terms(node.right)
            return left+right if left and right else []
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='sum':
            groups=[sum_terms(a) for a in node.args]
            return [v for group in groups for v in group] if all(groups) else []
        return []
    for ref in refs:
        f=facts[ref]
        if not f.get('expression'):continue
        try:terms=sum_terms(ast.parse(f['expression'],mode='eval').body)
        except (ValueError,SyntaxError):continue
        count=len(terms)
        if not 1<count<=10 or len(set(terms))!=count or any(k not in facts or facts[k].get('expression') for k in terms):continue
        word=next(k for k,v in number_words.items() if v==count)
        pattern=r'\b(?:'+word+'|'+str(count)+r')\s+(?:oldest\s+)?(?:buckets|accounts|branches|customers|contracts|components|items|source rows)\s+(?:total(?:ed)?|sum(?:med)? to|represent(?:ed)?|were|are)\s+\{'+re.escape(ref)+r'\}'
        for match in re.finditer(pattern,text,re.I):
            span=re.sub(r'\{[A-Za-z][A-Za-z0-9_]*\}','',match.group())
            plain=plain.replace(span,'SOURCE_GROUP_TOTAL')
    # Abstract discourse counts are not financial quantities. Currency,
    # customer counts, dates and magnitudes still require cited placeholders.
    plain=re.sub(r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:(?:correlated|material|separate|distinct|illustrative|reported|financial|key|major)\s+){0,2}(?:issues?|risks?|opportunities|questions?|cases?|scenarios?|metrics?|comparisons?|measures?|bridges?)\b','DISCOURSE_GROUP',plain,flags=re.I)
    # Accounting instruction, not a literal multiplier or quantity.
    plain=re.sub(r'\b(?:double[- ]count(?:ed|ing)?|one[- ](?:off|time))\b','ACCOUNTING_TERM',plain,flags=re.I)
    numeric=re.search(r'[0-9]+(?:[.,][0-9]+)*|[{}]|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|double[sd]?|triple[sd]?|half|hundred|thousand|million|billion)\b',plain,re.I)
    if numeric:
        raise RejectedFinding('unsupported_number', 'AI supplied an unsupported numerical conclusion; use source-fact placeholders.', token=numeric.group(),excerpt=plain[max(0,numeric.start()-35):numeric.end()+35])
    # An explicit statement that causation is NOT established is not a causal claim.
    # Stop at contrast/conjunction boundaries so a later asserted cause still fails.
    certainty_text=asserted_text(plain)
    if re.search(r'\bcaused\b|\bproves?\b|\bguarantee\w*|\bfraud\b|\binsolven\w*|\bbankrupt\w*|\bunderreserved\b|due to|driven by',certainty_text,re.I):
        raise RejectedFinding('unsupported_certainty', 'AI supplied unsupported causal or diagnostic certainty.')
    for identity in set(slots):text=text.replace('{'+identity+'}',display(facts[identity]))
    return text


def numeric_claim(proposal,facts,quotes):
    if proposal['operator']=='none':return None
    q=quotes.get(proposal['quote_id']);f=facts.get(proposal['fact_id']);text=proposal['quote'];threshold=proposal['threshold']
    if not q or not f or not text or text not in q['text']:raise InputError('AI invented a management quotation or KPI.')
    before=q['text'][:q['text'].index(text)];sentence_prefix=re.split(r'[.!?]',before)[-1]
    negated=bool(re.search(r'\bnot\b|\bnever\b|\bno longer\b|n.t\b',sentence_prefix+' '+text,re.I))
    outcome=dict(status='unverifiable',quote=text,quote_id=q['id'],refs=[q['id'],f['id']],tested_assertion='scoped numerical threshold',assessment='Metric meaning, entity, period or quoted threshold could not be matched locally.')
    # Only an explicit literal numeric assertion is verified, not the entire narrative.
    patterns={'gt':r'(?:above|over|more than|greater than)','gte':r'(?:at least|no less than)','lt':r'(?:below|under|less than)','lte':r'(?:at most|no more than)','eq':r'(?:was|is|of|at|equals?)'}
    if negated:return outcome
    if not re.search(patterns[proposal['operator']]+r'\s+'+re.escape(threshold)+r'(?![\d.])',text,re.I):return outcome
    m=re.fullmatch(r'([-+]?\d[\d,]*(?:\.\d+)?)(%)?',threshold)
    if not m or (f['unit']=='ratio')!=bool(m[2]) or f['unit'] not in {'ratio','count'}:return outcome
    if not f.get('company') or f['company'].startswith('Company not stated'):return outcome
    if f['file']!=q['file'] or f.get('company')!=q.get('company') or not q.get('period') or f.get('period')!=q['period']:return outcome
    if re.search(r'year.to.date|\bytd\b|\bltm\b|historical|last year|prior year',text,re.I):return outcome
    anchors={w for w in clean(f['label']).split() if len(w)>3}-{'rate','total','value','reported','amount','ratio'}
    if not anchors & set(clean(text).split()):return outcome
    entity=clean(f.get('entity'))
    if entity and entity!=clean(f.get('company')):
        total=bool(re.search(r'\btotal\b|consolidated',entity))
        if not (entity in clean(text) or (total and re.search(r'firmwide|companywide|groupwide|consolidated|overall',clean(text)))):return outcome
    expected=float(m[1].replace(',',''))/(100 if m[2] else 1);actual=f['value']
    supported={'gt':actual>expected,'gte':actual>=expected,'lt':actual<expected,'lte':actual<=expected,'eq':abs(actual-expected)<1e-9}[proposal['operator']]
    outcome.update(status='supported' if supported else 'contradicted',assessment=f'The cited {f["label"]} is {display(f)} for {f["period"]}, compared with the quoted threshold {threshold}. This verifies only the matched numerical assertion, not causation or the rest of management’s narrative.')
    return outcome


def rejection(diagnostics, section, index, item, exc, field=None):
    entry=dict(section=section,index=index,status='rejected',code=getattr(exc,'code','schema_error'),reason=str(exc))
    if field:entry['field']=field
    if isinstance(item,dict):
        entry['finding']=item
        entry['title']=item.get('title') if isinstance(item.get('title'),str) else None
        entry['fact_ids']=item.get('fact_ids',[]) if isinstance(item.get('fact_ids',[]),list) else []
    entry.update(getattr(exc,'details',{}))
    diagnostics.append(entry)


def management_question(text,refs,facts,title,diagnostics,index,limit=35):
    """Question wording cannot discard an otherwise validated investment finding."""
    try:
        rendered=grounded(text,refs,facts,limit)
        if rendered.endswith('?'):return rendered
        # An imperative request is actionable; convert only its presentation.
        if re.match(r'^(?:please\s+)?(?:provide|reconcile|bridge|explain|identify|review|confirm|quantify|validate|assess)\b',rendered,re.I):
            request=re.sub(r'^please\s+','',rendered,flags=re.I).rstrip('.!?')
            diagnostics.append(dict(section='questions',index=index,status='reformatted',code='imperative_request',reason='Actionable request converted to question form.'))
            return 'Can management '+request[0].lower()+request[1:]+'?'
        raise RejectedFinding('inactionable_question','Management question needs rewriting.')
    except (InputError,TypeError,KeyError,ValueError) as exc:
        diagnostics.append(dict(section='questions',index=index,status='rewritten',code=getattr(exc,'code','schema_error'),reason=str(exc)))
        # Title has already passed grounding and length checks. No unvalidated
        # question figures, forecasts or claims are carried into the replacement.
        return 'What evidence supports management’s explanation of “'+title+'”, and what specific actions should follow?'


def validate(result,packet,diagnostics=None):
    diagnostics=diagnostics if diagnostics is not None else []
    facts={f['id']:f for f in packet['facts']};quotes={q['id']:q for q in packet['commentary']};insights=[]
    raw=result.get('insights')
    if not isinstance(raw,list):
        rejection(diagnostics,'insights',None,raw,RejectedFinding('schema_error','insights must be an array.'))
        raw=[]
    for index,item in enumerate(raw):
        field='schema'
        try:
            if index>=6:raise RejectedFinding('schema_error','AI result exceeds the finding bound.')
            expected={'title','theme','kind','text','why_it_matters','management_question','fact_ids','claim'}
            if not isinstance(item,dict) or set(item)!=expected:raise RejectedFinding('schema_error','Invalid AI insight fields.')
            if not all(isinstance(item[k],str) for k in ['title','theme','kind','text','why_it_matters','management_question']):raise RejectedFinding('schema_error','Insight prose fields must be strings.')
            if item['kind'] not in {'risk','opportunity','relationship'} or item['theme'] not in {'retention','churn','quality','cost','utilization','pipeline','volume','ticket','collections','financial','unknown'}:raise RejectedFinding('schema_error','Invalid AI insight kind or theme.')
            refs=item['fact_ids'];rendered={}
            # A failed field rejects this finding only. Retain every detected field failure.
            failures=False
            for field,limit in [('title',8),('text',45),('why_it_matters',35)]:
                try:rendered[field]=grounded(item[field],refs,facts,limit)
                except InputError as exc:
                    rejection(diagnostics,'insights',index,item,exc,field);failures=True
            if failures:continue
            field='why_it_matters'
            if not re.search(r'\bmay\b|\bcould\b|\brisks?\b|\bopportunity\b',rendered[field],re.I):raise RejectedFinding('unqualified_implication','AI investment implication must be qualified.')
            rendered['management_question']=management_question(item['management_question'],refs,facts,rendered['title'],diagnostics,index)
            field='claim'
            claim_fields={'quote_id','quote','fact_id','operator','threshold'}
            if not isinstance(item['claim'],dict) or set(item['claim'])!=claim_fields or not all(isinstance(v,str) for v in item['claim'].values()):raise RejectedFinding('schema_error','Invalid numerical claim proposal.')
            if item['claim']['operator'] not in {'none','gt','gte','lt','lte','eq'}:raise RejectedFinding('schema_error','Invalid numerical claim operator.')
            try:claim=numeric_claim(item['claim'],facts,quotes)
            except InputError as exc:raise RejectedFinding('invalid_claim_citation',str(exc)) from exc
            if claim and item['claim']['fact_id'] not in refs:raise RejectedFinding('uncited_claim_kpi','Claim KPI is missing from insight citations.')
            if claim:refs=list(dict.fromkeys(refs+claim['refs']))
            locations={(facts[k]['file'],facts[k]['sheet']) for k in refs if k in facts}|{(quotes[k]['file'],quotes[k]['sheet']) for k in refs if k in quotes}
            field='fact_ids'
            cells={(facts[k]['file'],facts[k]['ref']) for k in refs if k in facts}|{(quotes[k]['file'],quotes[k]['ref']) for k in refs if k in quotes}
            if item['kind']=='relationship' and len(cells)<2:raise RejectedFinding('relationship_sources','A relationship requires distinct cited source records; worksheet count is not proof.')
            insights.append(dict(item,**rendered,id=8000+index,fact_ids=refs,claim_result=claim,classification='Verified numerical comparison' if claim and claim['status']!='unverifiable' else 'AI interpretation / hypothesis'))
            diagnostics.append(dict(section='insights',index=index,status='accepted',title=rendered['title'],fact_ids=refs))
        except (InputError,TypeError,KeyError,ValueError) as exc:
            rejection(diagnostics,'insights',index,item,exc,field)
    # Independently generated narrative is never a route around finding validation.
    raw_brief=result.get('briefing')
    if not isinstance(raw_brief,list):
        rejection(diagnostics,'briefing',None,raw_brief,RejectedFinding('schema_error','briefing must be an array.'))
        raw_brief=[]
    for index,item in enumerate(raw_brief):
        try:
            if index>=3 or not isinstance(item,dict) or set(item)!={'text','fact_ids'}:raise RejectedFinding('schema_error','Invalid AI briefing structure.')
            grounded(item['text'],item['fact_ids'],facts,75)
            diagnostics.append(dict(section='briefing',index=index,status='excluded',code='rebuilt_from_accepted_findings',reason='Independent narrative is not used; briefing is assembled only from accepted findings.'))
        except (InputError,TypeError,KeyError,ValueError) as exc:rejection(diagnostics,'briefing',index,item,exc)
    brief=[];words=0
    for item in insights[:3]:
        text=item['text']+' '+item['why_it_matters']+' '+item['management_question']
        if words+len(text.split())>210:text=item['text']
        brief.append(dict(text=text,fact_ids=item['fact_ids'],finding_id=item['id']))
        words+=len(text.split())
    return insights,brief
