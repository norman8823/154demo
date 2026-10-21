"""Persistent successful-review reuse, provenance fidelity and invalidation."""
from dataclasses import asdict
from datetime import date,datetime
import copy
import json
import os
import subprocess
import sys
import pytest
from engine import ROOT,Review,analyze
from ai_runtime import inference_session,persist_diagnostics
from report_cache import ReportCache,cache_key,pack,unpack,successful
from test_ai_investment import config,files,fake_model


@pytest.fixture
def receipt(monkeypatch):
    fake_model(monkeypatch);r=analyze(files(),ai_authorized=True)
    for e in r.package['inference']['events']:
        e.update(transport='provider',provider_completed=True,inference_occurred='observed')
    r.package['inference']['inference_observed']=True
    r.narrative_mode='AI-assisted investment analysis'
    assert successful(r)
    return r


def test_full_roundtrip_and_fresh_process_exports(monkeypatch,tmp_path,receipt):
    key=cache_key(files(),ai_authorized=True);cache=ReportCache(tmp_path)
    assert cache.save(key,receipt)
    loaded=cache.load(key)
    assert loaded.package['inference']['attempts']==0
    assert loaded.package['inference']['estimated_usd']==0
    assert loaded.package['inference']['origin']==receipt.package['inference']
    for name in asdict(receipt):
        if name=='package':continue
        assert getattr(loaded,name)==getattr(receipt,name)
    for name in receipt.package:
        if name!='inference':assert loaded.package[name]==receipt.package[name]
    assert (tmp_path/(key+'.json')).stat().st_mode & 0o077==0
    script="""
import io,sys
from pathlib import Path
from report_cache import ReportCache
from reports import export_report
from openpyxl import load_workbook
r=ReportCache(sys.argv[1]).load(sys.argv[2]);assert r
assert r.package['inference']['attempts']==0
for t in (None,(Path('sample_templates')/'Sample_Firm_Review_Template.xlsx').read_bytes()):
    data,_,_=export_report(r,t);w=load_workbook(io.BytesIO(data))
    assert any('86.0%' in str(row) for row in w['Partner Review' if t else 'Executive Summary'].values)
print('fresh-process cache hit; both Excel formats verified')
"""
    result=subprocess.run([sys.executable,'-c',script,str(tmp_path),key],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('change',['content','model','prompt','analysis','validation','mapping','authorization','credential'])
def test_key_invalidates_relevant_inputs(monkeypatch,change,tmp_path,receipt):
    import report_cache
    base=files();key=cache_key(base,ai_authorized=True)
    cache=ReportCache(tmp_path);assert cache.save(key,receipt)
    opts=dict(ai_authorized=True)
    if change=='content':base={k:v+b'changed' for k,v in base.items()}
    if change=='model':monkeypatch.setenv('OPENAI_MODEL','gpt-6-luna')
    if change=='prompt':monkeypatch.setattr(report_cache,'PROMPTS',('mapping_ai.py',))
    if change=='analysis':monkeypatch.setattr(report_cache,'ANALYSIS_VERSION','next')
    if change=='validation':monkeypatch.setenv('COPILOT_AI_MAX_REVIEW_USD','.05')
    if change=='mapping':opts['decisions']={'account':{'category':'other'}}
    if change=='authorization':opts['ai_authorized']=False
    if change=='credential':monkeypatch.setenv('OPENAI_API_KEY','different-project-test-key')
    changed=cache_key(base,**opts)
    assert changed!=key and cache.load(changed) is None


def test_never_persists_mocked_offline_or_failed_reviews(monkeypatch,tmp_path,receipt):
    c=ReportCache(tmp_path)
    assert not c.save('offline',Review())
    for variant in ('mock','no_findings','no_brief','invalid','bad_refs','bad_questions'):
        r=copy.deepcopy(receipt)
        if variant=='mock':r.package['inference']['events'][0]['transport']='mock'
        if variant=='no_findings':r.package['ai_insights']=[]
        if variant=='no_brief':r.package['ai_briefing']=[]
        if variant=='invalid':r.package['ai_validation']['status']='validation_failure'
        if variant=='bad_refs':r.package['ai_insights'][0]['fact_ids']=['fabricated']
        if variant=='bad_questions':r.package['view']['questions']=['A rejected question?']
        assert not c.save(variant,r)
    assert not list(tmp_path.glob('*.json'))


def test_corrupt_cache_is_a_miss(tmp_path,receipt):
    c=ReportCache(tmp_path);assert c.save('key',receipt)
    p=tmp_path/'key.json';p.write_text(p.read_text().replace('86.0%','99.0%'))
    assert c.load('key') is None
    p.write_text('{truncated');assert c.load('key') is None


def test_codec_preserves_supported_containers_without_code_execution():
    value={2:('a',{1,2}), 'dates':[date(2026,1,1),datetime(2026,1,1,2,3)]}
    assert unpack(json.loads(json.dumps(pack(value))))==value


def test_failed_diagnostics_survive_separately_from_success_cache(monkeypatch,tmp_path):
    monkeypatch.setenv('COPILOT_DIAGNOSTIC_DIR',str(tmp_path))
    with inference_session(True) as session:
        session.events.append(dict(transport='provider',phase='investment_analysis',status='request_timeout'))
        session.responses.append(dict(phase='investment_analysis',response={'status':'incomplete','incomplete_details':{'reason':'max_output_tokens'}}))
        r=Review(package={'inference':session.summary(),'ai_validation':{'status':'response_failure','items':[{'index':0,'reason':'not cited'}]}})
        persist_diagnostics(r)
        saved=json.loads((tmp_path/(session.run_id+'.json')).read_text())
        assert saved['validation']['status']=='response_failure' and saved['responses']
        assert not ReportCache(tmp_path/'cache').save('failure',r)
