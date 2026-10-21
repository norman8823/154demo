"""Adapter to the existing Review / accepted-finding boundary; numbers are local."""
import math
import re
from types import SimpleNamespace
from engine import InputError
from investment_output import grounded, management_question, rejection, RejectedFinding, display
from skill_tools import object_schema

VERSION='skill-output-4'
CHECKS=['management_claims','cash_reinvestment_debt','earnings_quality','customers_operating_drivers','decisions_uncertainty_positives']
FIELDS={'title':12,'conclusion':60,'evidence':100,'financial_implication':70,'assessment':65,'action':65,'management_question':45}
CATEGORIES=['growth','earnings_quality','cash_conversion','operating','working_capital','contract','data_quality','other']


def schema():
    text={'type':'string'}
    props={k:dict(type='string',description=f'At most {n} words. Every numerical quantity uses a cited {{fact_id}} placeholder, never literal figures or spelled-out numbers. No figures in titles.') for k,n in FIELDS.items()}
    props.update(category=dict(type='string',enum=CATEGORIES),kind=dict(type='string',enum=['risk','opportunity','relationship']),
        priority=dict(type='string',enum=['high','medium','low']),disposition=dict(type='string',enum=['act_now','investigate','monitor','opportunity']),
        evidence_status=dict(type='string',enum=['verified_observation','evidence_backed_interpretation','open_question']),
        fact_ids=dict(type='array',items=text,maxItems=40,description='Numeric cell or calculation IDs ONLY. Text/date/note IDs belong in source_quotes, never numeric placeholders. Every numeric placeholder must be listed.'),
        source_quotes=dict(type='array',items=object_schema(dict(source_id=text,quote=text)),maxItems=10))
    return object_schema(dict(findings=dict(type='array',items=object_schema(props),maxItems=7),
        rejected_candidates=dict(type='array',items=object_schema(dict(candidate=text,reason=text)),maxItems=7),
        coverage_limitations=dict(type='array',items=text,maxItems=12),
        completion_checks=dict(type='array',minItems=5,maxItems=5,items=object_schema(dict(area=dict(type='string',enum=CHECKS),status=dict(type='string',enum=['tested','not_applicable','missing_inputs']),fact_ids=dict(type='array',items=text,maxItems=30),explanation=dict(type='string',description='Concise audit of tests performed, calculations derived, or genuinely absent inputs. Do not confuse a metric not printed with missing inputs.'))))))


def validate(proposal, tools):
    accepted=[];diagnostics=[]
    if not isinstance(proposal,dict) or set(proposal)!=set(schema()['properties']):
        return [],[dict(status='rejected',code='schema_error',reason='Invalid assessment fields.')]
    raw=proposal['findings']
    if not isinstance(raw,list) or len(raw)>7:return [],[dict(status='rejected',code='schema_error',reason='Invalid findings array.')]
    for index,item in enumerate(raw):
        try:
            if not isinstance(item,dict) or set(item)!=set(schema()['properties']['findings']['items']['properties']):raise InputError('Invalid finding fields.')
            for field,choices in [('category',CATEGORIES),('kind',['risk','opportunity','relationship']),('priority',['high','medium','low']),('disposition',['act_now','investigate','monitor','opportunity']),('evidence_status',['verified_observation','evidence_backed_interpretation','open_question'])]:
                if item[field] not in choices:raise InputError('Invalid '+field)
            refs=item['fact_ids']
            if not isinstance(refs,list) or not refs or len(refs)>40 or not all(isinstance(r,str) for r in refs):raise InputError('Invalid fact IDs.')
            # The existing publication contract accepts quoted text IDs too.
            # Rebind them only when an explicit quote supplies their evidence,
            # never when a numeric placeholder tries to render the text as a value.
            quoted={q.get('source_id') for q in item['source_quotes'] if isinstance(q,dict)}
            note_refs={k for k in refs if k in tools.notes and k in quoted and not any('{'+k+'}' in item[field] for field in FIELDS)}
            if note_refs:
                refs=[k for k in refs if k not in note_refs];item['fact_ids']=refs
                diagnostics.append(dict(status='normalized',index=index,code='quoted_text_ids',reason='Quoted text IDs moved to the source-quote evidence channel.',source_ids=sorted(note_refs)))
            for identity in refs:tools.verify_fact(identity)
            quotes=item['source_quotes']
            if not isinstance(quotes,list) or len(quotes)>10:raise InputError('Invalid source quotation array.')
            for q in quotes:
                note=tools.notes.get(q.get('source_id'))
                if note and isinstance(q.get('quote'),str) and q['quote'] not in note['text']:
                    start=note['text'].lower().find(q['quote'].lower())
                    if start>=0:
                        q['quote']=note['text'][start:start+len(q['quote'])]
                        diagnostics.append(dict(status='normalized',code='quote_case',reason='Capitalization-only quote difference rebound to exact source excerpt.',index=index))
                if not note or not isinstance(q.get('quote'),str) or len(q['quote'])<3 or q['quote'] not in note['text']:
                    raise InputError('Source quotation is not an exact excerpt of a read workbook cell.')
            rendered={};field_errors=[];first_error=None
            for field,limit in FIELDS.items():
                if field=='management_question':continue
                try:
                    rendered[field]=grounded(item[field],refs,tools.facts,limit if field=='title' else 160)
                    if len(item[field].split())>limit:
                        diagnostics.append(dict(status='warning',index=index,field=field,code='prose_target_exceeded',reason='Full verified prose retained within the publication bound; concise wording target exceeded.',target_words=limit,actual_words=len(item[field].split())))
                except InputError as exc:
                    first_error=first_error or exc
                    field_errors.append(dict(field=field,reason=str(exc),code=getattr(exc,'code','schema_error'),word_limit=limit,details=getattr(exc,'details',{})))
            if field_errors:
                raise RejectedFinding(getattr(first_error,'code','schema_error'),str(first_error),field_errors=field_errors)
            rendered['management_question']=management_question(item['management_question'],refs,tools.facts,rendered['title'],diagnostics,index,45)
            slots=re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}', ' '.join(item[k] for k in FIELDS))
            has_illustrative=any(tools.facts[k].get('illustrative') for k in refs)
            if has_illustrative and not re.search(r'illustrative|sensitivity',rendered['financial_implication']+' '+rendered['assessment']+' '+rendered['conclusion'],re.I):
                rendered['financial_implication']+=' Includes illustrative calculations using the recorded assumptions; these are not forecasts or verified loss estimates.'
                diagnostics.append(dict(status='normalized',index=index,code='illustrative_label_added',reason='Recorded illustrative calculation classification made explicit in the report.'))
            if not re.search(r'\b(?:may|could|risk|opportunity|unverified|unknown|unresolved|uncertain|unproven|unquantified|unconfirmed|unclear|unavailable|unaudited|open)\b|not (?:established|supplied|proven)|not.{0,30}(?:substantiated|establish)|require\w*.{0,40}(?:review|validation|evidence|support)|no\b.{0,120}\bwas reviewed|not be treated as (?:expected|proven)|not\b.{0,90}(?:provid\w*|available|quantified|forecast|isolate|establish|verify|show|include|confirm|support|demonstrate|prove|quantify|disclose)|no\b.{0,60}(?:forecast|evidence|visibility)|no\b[^.!?]{0,200}\b(?:supplied|provided|available)',rendered['assessment']+' '+rendered['financial_implication']+' '+rendered['conclusion'],re.I):
                rendered['assessment']+=' Source and arithmetic support do not establish this interpretation; investment-team review is required.'
                diagnostics.append(dict(status='warning',index=index,code='narrative_review_required',reason='Explicit review caveat added: lexical checks cannot establish narrative qualification or truth.'))
            impact_ids=re.findall(r'\{([A-Za-z][A-Za-z0-9_]*)\}',item['financial_implication'])
            classification='Source-supported observation; interpretation requires review' if item['evidence_status']=='verified_observation' else 'AI interpretation / hypothesis'
            if has_illustrative:classification+=' / illustrative calculations included'
            accepted.append(dict(item,**rendered,id=10000+index,text=rendered['evidence']+' '+rendered['financial_implication'],
                why_it_matters=rendered['assessment'],classification=classification,theme='financial',claim_result=None,
                impact=display(tools.facts[impact_ids[0]]) if impact_ids else '',issue_id=item['category']))
            diagnostics.append(dict(status='accepted',index=index,title=rendered['title'],fact_ids=refs,source_quotes=len(quotes),assurance='Source and arithmetic support only; not narrative proof.'))
        except (InputError,KeyError,TypeError,ValueError,RecursionError) as exc:
            rejection(diagnostics,'skill_findings',index,item,exc)
    # Rejected candidates/coverage are disclosed as model notes, never accepted evidence.
    for key in ('rejected_candidates','coverage_limitations'):
        if not isinstance(proposal.get(key),list):diagnostics.append(dict(status='rejected',code='schema_error',reason='Invalid '+key))
    checks=proposal.get('completion_checks',[])
    try:
        if len(checks)!=len(CHECKS) or {c['area'] for c in checks}!=set(CHECKS):raise InputError('Completion checks missing or duplicated.')
        for c in checks:
            if c['status'] not in {'tested','not_applicable','missing_inputs'} or not c['explanation'].strip():raise InputError('Incomplete analytical self-check.')
            if c['status']=='tested' and not c['fact_ids']:raise InputError('Tested completion check requires source or calculation IDs.')
            for ref in c['fact_ids']:
                if ref in tools.facts:tools.verify_fact(ref)
                elif ref not in tools.notes:raise InputError('Unknown completion-check source: '+ref)
    except (InputError,KeyError,TypeError) as exc:
        diagnostics.append(dict(status='rejected',code='completion_check',reason=str(exc)))
    return accepted,diagnostics


def publish(review, tools, accepted, diagnostics, proposal, partial_reason=None):
    from investigation import publish as publish_existing
    packet=dict(facts=list(tools.facts.values()),source_statements=list(tools.notes.values()))
    for item in accepted:
        item['fact_ids']=list(dict.fromkeys(item['fact_ids']+[q['source_id'] for q in item['source_quotes']]))
    review.findings=[]
    review.package.update(findings=[],facts=[],grid_facts=[],claims=[],ai_insights=accepted,
        ai_briefing=[dict(text=i['conclusion']+' '+i['assessment'],finding_id=i['id'],fact_ids=i['fact_ids']) for i in accepted[:3]],
        ai_validation=dict(status='accepted',accepted=len(accepted),diagnostics=diagnostics,assurance='References and arithmetic checked; narrative conclusions need investment-team review.'),
        investigation=dict(status='not_applicable',reason='Single skill workflow already includes targeted investigation.'),
        skill_rejected_candidates=proposal.get('rejected_candidates',[]),skill_coverage_limitations=proposal.get('coverage_limitations',[]))
    publish_existing(review,packet,SimpleNamespace(facts=tools.facts),accepted)
    cards=[dict(id=i['id'],ids=[i['id']],title=i['title'],impact=i['impact'],summary=i['text'],kind=i['classification'],adverse=i['kind']=='risk',
                question=i['management_question'],refs=i['fact_ids'],why=i['assessment']) for i in accepted]
    notice='Skill analyst · source references and arithmetic checked; explanations, scope judgments and sensitivities require investment-team review.'
    review.package['view']=dict(cards=cards[:3],secondary=cards[3:],paragraphs=[('Investment assessment',i['conclusion']+' '+i['assessment']) for i in accepted[:3]],questions=[i['management_question'] for i in accepted[:3]],notice=notice)
    review.questions=[i['management_question'] for i in accepted]
    review.memo='\n\n'.join(i['conclusion']+' '+i['financial_implication']+' '+i['assessment']+' '+i['action'] for i in accepted)
    review.package['mode']='Skill analyst v2 · completed · numerical support checked, narrative review required'
    if partial_reason:
        notice='PARTIAL REVIEW — '+partial_reason+' Only validated findings are shown; rejected claims and dependent summaries/questions are excluded.'
        review.package['view']['notice']=notice
        review.package['mode']='Skill analyst v2 · PARTIAL REVIEW — '+partial_reason
        review.package['ai_validation']['status']='partial'
        review.memo=notice+'\n\n'+review.memo
    review.warnings.append(notice)
    review.warnings.extend('Analyst coverage limitation (unverified): '+str(x) for x in proposal.get('coverage_limitations',[]))
