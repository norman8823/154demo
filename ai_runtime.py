"""Small shared outbound gate and per-review budget; never logs financial payloads or keys."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass,field
from datetime import datetime,timezone
import uuid
import json
import logging
import math
import os
import shlex
import tempfile
from pathlib import Path
import time
import urllib.error
import urllib.request
from engine import InputError

_CURRENT=ContextVar('investment_inference',default=None)
LOG=logging.getLogger('copilot.inference')
# USD / million tokens, standard uncached list estimates; not provider invoices.
# https://developers.openai.com/api/docs/models/gpt-4o-mini
RATES={'gpt-6-luna':(.10,.50),'gpt-4o-mini':(.15,.60),'gpt-4o-mini-2024-07-18':(.15,.60),'gpt-4.1-mini':(.40,1.60),'gpt-4.1-mini-2025-04-14':(.40,1.60)}


CACHE_RATES={'gpt-6-luna':(.01,.125)}
_FILE_SETTINGS={}


def load_environment(path=None):
    """Load the app-local .env once per process; explicit shell settings win.

    Parse values as data, never execute shell code or log credentials. An explicit
    empty COPILOT_ENV_FILE disables local configuration (e.g. isolated tests).
    """
    configured=os.environ.get('COPILOT_ENV_FILE')
    if path is None and configured=='':return
    path=Path(path or configured or Path(__file__).resolve().parent/'.env')
    if not path.is_file():return
    allowed={'OPENAI_API_KEY','OPENAI_MODEL','OPENAI_INPUT_USD_PER_M','OPENAI_OUTPUT_USD_PER_M','COPILOT_AI_MAX_REVIEW_USD','COPILOT_AI_TIMEOUT_SECONDS','COPILOT_AI_MAX_RETRIES'}
    for line in path.read_text().splitlines():
        key,sep,value=line.strip().removeprefix('export ').partition('=')
        key=key.strip()
        if not sep or key not in allowed or key in os.environ:continue
        try:parts=shlex.split(value,comments=True)
        except ValueError:raise InputError('Invalid .env syntax for '+key+'.') from None
        if len(parts)!=1:raise InputError('Expected one nonempty .env value for '+key+'.')
        os.environ[key]=parts[0]
        _FILE_SETTINGS[key]=(str(path),parts[0])


def model_source():
    origin=_FILE_SETTINGS.get('OPENAI_MODEL')
    if origin and os.environ.get('OPENAI_MODEL')==origin[1]:return origin[0]
    return 'process environment' if 'OPENAI_MODEL' in os.environ else 'application default'


def positive(value,name,maximum=None):
    try:value=float(value)
    except (TypeError,ValueError):raise InputError(name+' must be a positive finite number.')
    if not math.isfinite(value) or value<=0 or (maximum is not None and value>maximum):raise InputError(name+' is outside the allowed bounds.')
    return value


def configuration():
    model=os.environ.get('OPENAI_MODEL','gpt-4o-mini')
    pair=RATES.get(model)
    overrides=[os.environ.get('OPENAI_INPUT_USD_PER_M'),os.environ.get('OPENAI_OUTPUT_USD_PER_M')]
    if any(v is not None for v in overrides):
        pair=tuple(positive(v,'Model token price') for v in overrides)
    limit=positive(os.environ.get('COPILOT_AI_MAX_REVIEW_USD','.10'),'Review spending limit')
    timeout=positive(os.environ.get('COPILOT_AI_TIMEOUT_SECONDS','90'),'AI timeout',300)
    retries=os.environ.get('COPILOT_AI_MAX_RETRIES','0')
    if retries not in {'0','1'}:raise InputError('AI retries must be 0 or 1.')
    return dict(model=model,model_source=model_source(),cache_rates=CACHE_RATES.get(model) if not any(v is not None for v in overrides) else None,rates=pair,limit=limit,timeout=timeout,retries=int(retries))


@dataclass
class InferenceSession:
    authorized:bool=False
    run_id:str=field(default_factory=lambda:uuid.uuid4().hex)
    limit:float|None=None
    events:list=field(default_factory=list)
    reserved:float=0
    responses:list=field(default_factory=list)
    def summary(self):
        completed=[e for e in self.events if e.get('provider_completed')]
        costs=[e.get('estimated_usd') for e in self.events]
        return dict(run_id=self.run_id,model=os.environ.get('OPENAI_MODEL','gpt-4o-mini'),authorized=self.authorized,model_source=model_source(),provider='OpenAI',attempts=len(self.events),inference_observed=bool(completed),
                    estimated_usd=(0 if not costs else sum(costs) if all(c is not None for c in costs) else None),
                    reserved_upper_usd=self.reserved,events=self.events)


@contextmanager
def inference_session(authorized=False,limit=None):
    session=InferenceSession(authorized=authorized is True,limit=limit);token=_CURRENT.set(session)
    try:yield session
    finally:_CURRENT.reset(token)


def permitted():
    s=_CURRENT.get()
    return bool(s and s.authorized)


def complete(body,phase,request_fn=None,*,deadline=None,settle_usage=False):
    """Reserve a pessimistic token-price bound before each attempt, including retries.

    Explicit test transports never imply provider inference. Unknown billing after a
    network failure retains its reservation. Only an explicit HTTP 429 may retry.
    """
    cfg=configuration();s=_CURRENT.get() or InferenceSession()
    if not request_fn and not s.authorized:raise InputError('External AI is not authorized for these files.')
    if not os.environ.get('OPENAI_API_KEY'):raise InputError('OPENAI_API_KEY is not configured.')
    if not cfg['rates']:raise InputError('Model pricing is unknown; configure both token prices before inference. No fallback model was selected.')
    body=dict(body,model=cfg['model'],store=False)
    raw=json.dumps(body,separators=(',',':')).encode()
    if len(raw)>190000:raise InputError('AI request exceeds the bounded input size.')
    # A byte-level ceiling is intentionally much higher than a typical token count.
    # Include serialized tool definitions, schema, message framing and completion.
    input_upper=len(raw)+4096;output_upper=body.get('max_output_tokens',0)
    if not isinstance(output_upper,int) or not 1<=output_upper<=(32000 if phase.startswith('skill_') else 10000):raise InputError('AI output token limit is invalid.')
    input_rate=max(cfg['rates'][0],cfg['cache_rates'][1]) if cfg['cache_rates'] else cfg['rates'][0]
    upper=(input_upper*input_rate+output_upper*cfg['rates'][1])/1_000_000
    limit=min(cfg['limit'],positive(s.limit,'Authorized review limit')) if s.limit is not None else cfg['limit']
    for attempt in range(cfg['retries']+1):
        if deadline is not None and time.monotonic()>=deadline:raise InputError('AI elapsed-time limit reached.')
        if s.reserved+upper>limit:raise InputError('AI spending limit would be exceeded; limited offline analysis retained.')
        from task_budget import update as task_budget
        ticket=task_budget(amount=upper,metadata=dict(run_id=s.run_id,phase=phase,model=cfg['model'])) if not request_fn else None
        s.reserved+=upper
        started=time.monotonic()
        event=dict(timestamp=datetime.now(timezone.utc).isoformat(),run_id=s.run_id,phase=phase,model=cfg['model'],model_source=cfg['model_source'],provider='OpenAI',transport='mock' if request_fn else 'provider',attempt=attempt+1,
                   provider_completed=False,inference_occurred='not observed',input_tokens=None,output_tokens=None,
                   approximate_input_tokens=round(len(raw)/4),estimated_usd=None,reserved_upper_usd=upper,status='attempted')
        s.events.append(event)
        req=urllib.request.Request('https://api.openai.com/v1/responses',data=raw,headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':'application/json'})
        try:
            if request_fn:response=request_fn(req)
            else:
                timeout=min(cfg['timeout'],max(.001,deadline-time.monotonic())) if deadline is not None else cfg['timeout']
                with urllib.request.urlopen(req,timeout=timeout) as reply:response=json.load(reply)
            if not request_fn:s.responses.append(dict(phase=phase,response=response))
            event['approximate_output_tokens']=round(len(json.dumps(response.get('output',[])))/4)
            usage=response.get('usage') or {}
            reasoning=(usage.get('output_tokens_details') or {}).get('reasoning_tokens')
            if type(reasoning) is int and reasoning>=0:event['reasoning_tokens']=reasoning
            details=usage.get('input_tokens_details') or {}
            cached=details.get('cached_tokens')
            if type(cached) is int and cached>=0:event['cached_input_tokens']=cached
            for key in ['input_tokens','output_tokens']:
                value=usage.get(key)
                if type(value) is int and value>=0:event[key]=value
            event.update(response_status=response.get('status'),incomplete_details=response.get('incomplete_details'),response_id=response.get('id'),status='response_received',returned_model=response.get('model'),provider_completed=not request_fn and response.get('status')=='completed',inference_occurred='mocked' if request_fn else ('observed' if response.get('status')=='completed' else 'unknown'))
            if event['input_tokens'] is not None and event['output_tokens'] is not None:
                event['estimated_usd']=(event['input_tokens']*cfg['rates'][0]+event['output_tokens']*cfg['rates'][1])/1_000_000
                event['cost_basis']='provider token usage × configured uncached list rates; cache discounts not assumed'
                if cfg['cache_rates']:
                    details=usage.get('input_tokens_details') or {}
                    cached=details.get('cached_tokens',0);written=details.get('cache_write_tokens',0)
                    if type(cached) is int and type(written) is int and min(cached,written)>=0 and cached+written<=event['input_tokens']:
                        event.update(cached_input_tokens=cached,cache_write_tokens=written)
                        event['estimated_usd']=((event['input_tokens']-cached-written)*cfg['rates'][0]+cached*cfg['cache_rates'][0]+written*cfg['cache_rates'][1]+event['output_tokens']*cfg['rates'][1])/1_000_000
                        event['cost_basis']='provider token usage including cache reads/writes × documented standard list rates; not an invoice'
                    else:event.update(estimated_usd=None,cost_basis='invalid cache usage; actual cost unknown; reservation retained')
            else:event['cost_basis']='usage missing; upper reservation retained; billed cost unknown'
            returned=response.get('model')
            if returned and returned!=cfg['model'] and not returned.startswith(cfg['model']+'-'):
                event.update(estimated_usd=None,cost_basis='returned model differs; applicable rates unknown; reservation retained')
            # Opt-in bounded loops settle a known completed receipt, retaining
            # the upper reservation for missing usage, errors and unknown cost.
            # This does not raise the authorized ceiling or retry a request.
            if settle_usage and event.get('provider_completed') and event.get('estimated_usd') is not None:
                s.reserved+=event['estimated_usd']-upper
                event['settled_usd']=event['estimated_usd']
            if ticket and event.get('provider_completed') and event.get('estimated_usd') is not None:
                task_budget(ticket=ticket,cost=event['estimated_usd'])
                event['task_budget_ticket']=ticket
            if deadline is not None and time.monotonic()>=deadline:raise InputError('AI elapsed-time limit reached; late response not published.')
            return response
        except urllib.error.HTTPError as exc:
            event.update(status='http_'+str(exc.code),inference_occurred='unknown')
            if exc.code==429 and attempt<cfg['retries']:
                time.sleep(.25);continue
            if exc.code in {400,401,403,404}:
                raise InputError(f'OpenAI configuration/request error (HTTP {exc.code}) for model {cfg["model"]}; no fallback model was selected.') from None
            raise InputError(f'AI provider request failed (HTTP {exc.code}); limited offline analysis retained.') from None
        except Exception as exc:
            event.update(status='request_timeout' if isinstance(exc,TimeoutError) else 'request_failed',failure_type=type(exc).__name__,inference_occurred='unknown' if not request_fn else 'mocked')
            raise InputError('AI request failed or timed out; limited offline analysis retained.') from exc
        finally:
            event['elapsed_seconds']=round(time.monotonic()-started,3)
            # Metadata only. The application launcher can direct this logger to its normal log.
            LOG.warning('copilot_inference %s',json.dumps(event,separators=(',',':')))


def persist_diagnostics(review):
    """Retain real-response diagnostics privately, including failed output validation."""
    session=_CURRENT.get()
    if not session or not any(e.get('transport')=='provider' for e in session.events):return
    folder=Path(os.environ.get('COPILOT_DIAGNOSTIC_DIR',Path(__file__).resolve().parent/'.local'/'analysis-diagnostics'))
    temporary=None
    try:
        folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        if folder.is_symlink():raise OSError('Diagnostic directory must not be a symlink')
        payload=dict(inference=review.package.get('inference'),validation=review.package.get('ai_validation'),accepted_findings=review.package.get('ai_insights',[]),investigation=review.package.get('investigation'),skill_engine=review.package.get('skill_engine'),responses=session.responses)
        with tempfile.NamedTemporaryFile(mode='w',dir=folder,delete=False) as stream:
            temporary=stream.name
            json.dump(payload,stream,default=str)
        os.replace(temporary,folder/(session.run_id+'.json'))
    except (OSError,TypeError,ValueError):
        LOG.warning('copilot_diagnostics_write_failed run_id=%s',session.run_id)
    finally:
        if temporary and os.path.exists(temporary):os.unlink(temporary)
