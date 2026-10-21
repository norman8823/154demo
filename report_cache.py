"""Private, atomic JSON cache for complete source-validated AI reviews; no database."""
from dataclasses import asdict
from datetime import date,datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid
from engine import ROOT,Review

FORMAT_VERSION=1
ANALYSIS_VERSION='validated-review-5'
SOURCES=('engine.py','ingestion.py','financial_analysis.py','package_reader.py','package_analysis.py','ai_evidence.py','investment_output.py','executive.py','reports.py','excel_layout.py','ai_runtime.py','report_cache.py','investigation.py','investigation_math.py','company_context.py','skill_engine.py','skill_tools.py','skill_output.py','task_budget.py')
PROMPTS=('analyst_ai.py','mapping_ai.py')
SETTINGS=('OPENAI_MODEL','COPILOT_AI_MAX_REVIEW_USD','COPILOT_AI_TIMEOUT_SECONDS','COPILOT_AI_MAX_RETRIES','OPENAI_INPUT_USD_PER_M','OPENAI_OUTPUT_USD_PER_M')


def _digest(value):return hashlib.sha256(value).hexdigest()


def pack(value):
    if isinstance(value,dict):return {'type':'dict','items':[[pack(k),pack(v)] for k,v in value.items()]}
    if isinstance(value,tuple):return {'type':'tuple','items':[pack(v) for v in value]}
    if isinstance(value,set):return {'type':'set','items':[pack(v) for v in sorted(value,key=repr)]}
    if isinstance(value,list):return [pack(v) for v in value]
    if isinstance(value,datetime):return {'type':'datetime','value':value.isoformat()}
    if isinstance(value,date):return {'type':'date','value':value.isoformat()}
    if value is None or type(value) in (str,int,float,bool):return value
    raise TypeError('Unsupported review cache value: '+type(value).__name__)


def unpack(value):
    if isinstance(value,list):return [unpack(v) for v in value]
    if isinstance(value,dict):
        kind=value['type']
        if kind=='dict':return {unpack(k):unpack(v) for k,v in value['items']}
        if kind=='tuple':return tuple(unpack(v) for v in value['items'])
        if kind=='set':return set(unpack(v) for v in value['items'])
        if kind=='date':return date.fromisoformat(value['value'])
        if kind=='datetime':return datetime.fromisoformat(value['value'])
        raise ValueError('Invalid cached value type')
    return value


def cache_key(files,decisions=None,layouts=None,profiles=None,ai_authorized=False,engine_name=None):
    from ai_runtime import configuration
    cfg=configuration()
    from skill_engine import selected_engine,identity
    chosen=engine_name or selected_engine()
    value=dict(format=FORMAT_VERSION,analysis_version=ANALYSIS_VERSION,provider='OpenAI',model=cfg['model'],
        inputs=sorted((name,_digest(data)) for name,data in files.items()),
        prompt_version={name:_digest((ROOT/name).read_bytes()) for name in PROMPTS},
        analysis_source={name:_digest((ROOT/name).read_bytes()) for name in SOURCES},
        settings={name:os.environ.get(name) for name in SETTINGS},rates=cfg['rates'],timeout=cfg['timeout'],
        decisions=decisions or {},layouts=layouts or {},profiles=profiles or {},authorized=ai_authorized is True,
        credential_scope=_digest(os.environ.get('OPENAI_API_KEY','').encode()),engine=chosen,
        skill_identity=identity() if chosen=='skill' else None)
    return _digest(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode())


def successful(review,require_real=True):
    p=review.package;items=p.get('ai_insights',[]);brief=p.get('ai_briefing',[]);v=p.get('ai_validation',{})
    if p.get('engine_identity')=='skill':
        state=p.get('skill_engine',{})
        if state.get('status')!='completed' or any(c['read']!=c['total'] for c in state.get('coverage',[])):return False
    if not items or not brief or v.get('status')!='accepted' or v.get('accepted')!=len(items):return False
    ids={f['id'] for f in items};evidence={e['Fact ID'] for e in review.evidence}
    if len(ids)!=len(items) or any(not f['fact_ids'] or not set(f['fact_ids'])<=evidence for f in items):return False
    if any(b.get('finding_id') not in ids for b in brief):return False
    if p.get('view',{}).get('questions')!=[f['management_question'] for f in items[:3]]:return False
    investigation=p.get('investigation',{})
    if investigation and investigation.get('status')!='not_applicable':
        refined=investigation.get('findings',[])
        if investigation.get('status')!='accepted' or not refined or investigation.get('accepted')!=len(refined):return False
        if any(not i['fact_ids'] or not set(i['fact_ids'])<=evidence for i in refined):return False
    inf=p.get('inference',{});origin=inf.get('origin',inf)
    if investigation.get('findings') and require_real and not any(e.get('phase')=='investment_investigation' and e.get('transport')=='provider' and e.get('provider_completed') is True for e in origin.get('events',[])):return False
    phase='skill_analysis' if p.get('engine_identity')=='skill' else 'investment_analysis'
    return not require_real or (origin.get('authorized') is True and any(e.get('phase')==phase and e.get('transport')=='provider' and e.get('provider_completed') is True and e.get('model')==os.environ.get('OPENAI_MODEL','gpt-4o-mini') and (e.get('returned_model')==e.get('model') or str(e.get('returned_model','')).startswith(e.get('model','')+'-')) for e in origin.get('events',[])))


def reused(review,kind):
    """Keep the original provider receipt separate from zero-call current-run usage."""
    previous=review.package.get('inference',{});origin=previous.get('origin',previous)
    review.package['inference']=dict(run_id=uuid.uuid4().hex,provider=origin.get('provider','OpenAI'),model=origin.get('model'),authorized=origin.get('authorized',False),attempts=0,inference_observed=False,estimated_usd=0,reserved_upper_usd=0,events=[],reused=True,cache=kind,origin=origin)
    return review


class ReportCache:
    def __init__(self,directory=None):
        self.directory=Path(directory or os.environ.get('COPILOT_REPORT_CACHE_DIR',ROOT/'.local'/'analysis-cache'))

    def load(self,key):
        try:
            path=self.directory/(key+'.json')
            if path.is_symlink() or self.directory.is_symlink():return None
            envelope=json.loads(path.read_text())
            raw=envelope['review']
            digest=_digest(json.dumps(raw,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
            if envelope.get('key')!=key or envelope.get('format')!=FORMAT_VERSION or digest!=envelope.get('sha256'):return None
            review=Review(**unpack(raw))
            if not successful(review):return None
            return reused(review,'persistent')
        except (OSError,ValueError,TypeError,KeyError,AttributeError):return None

    def save(self,key,review):
        if not successful(review):return False
        temporary=None
        try:
            raw=pack(asdict(review))
            encoded=json.dumps(raw,sort_keys=True,separators=(',',':'),allow_nan=False)
            envelope=dict(key=key,format=FORMAT_VERSION,sha256=_digest(encoded.encode()),review=raw)
            self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
            if self.directory.is_symlink():return False
            with tempfile.NamedTemporaryFile(mode='w',dir=self.directory,delete=False) as stream:
                temporary=stream.name
                json.dump(envelope,stream,separators=(',',':'),allow_nan=False)
            os.replace(temporary,self.directory/(key+'.json'))
            return True
        except (OSError,TypeError,ValueError):return False
        finally:
            if temporary and os.path.exists(temporary):os.unlink(temporary)
