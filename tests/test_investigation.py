"""Bounded investigation arithmetic, provenance, partial acceptance and reports."""
import copy,json,math
from pathlib import Path
import pytest
from engine import ROOT,Review,demo_files
from investigation import build_packet,validate,investigate,CHAR_LIMIT,FACT_LIMIT
from investigation_math import canonical,Calculations
from ai_runtime import inference_session
from executive import present,report_findings
from reports import export_report


def baseline(name='tallis'):
    # Rebuild source fixtures locally; tests do not depend on private run artifacts.
    from engine import analyze
    if name=='original':files=demo_files()
    else:
        p=ROOT/'tests/fixtures'/('Tallis_Brook_Accounting_Sep2026.xlsx' if name=='tallis' else 'Summit_Home_Services_Sep2026.xlsx')
        files={p.name:p.read_bytes()}
    r=analyze(files)
    titles=['Adjusted earnings review','Working capital review','Client retention review','Operating performance review']
    refs=[e['Fact ID'] for e in r.evidence if type(e.get('Validated value')) in (int,float)][:2]
    r.package['ai_insights']=[dict(id=8000+i,title=title,text='The reported exposure warrants review.',why_it_matters='This may affect earnings durability.',management_question='Which actions address the cited exposure?',fact_ids=refs,kind='risk',classification='AI interpretation / hypothesis') for i,title in enumerate(titles)]
    return r,files


def test_full_retrieval_scope_and_calculations():
    r,files=baseline();packet,c=build_packet(r,files)
    assert len(packet['facts'])<=FACT_LIMIT and len(json.dumps(packet,separators=(',',':')))<=CHAR_LIMIT
    assert 3<=len(packet['issues'])<=5
    legacy=[f for f in c.derived if f['label'].startswith('Source-described legacy')]
    assert legacy and all(f['grain']=='month' and math.isclose(f['value'],.0556,abs_tol=.0001) for f in legacy)
    assert all(f['value']<1 for f in legacy) # never quarterly/monthly growth
    for f in c.derived:
        assert set(f['inputs']+f.get('source_refs',[]))<=(set(c.facts)|{q['id'] for q in r.package['narratives']})
        if f['operation']=='ratio':assert len(f['inputs'])==2
    aliases=[f for f in c.facts.values() if f.get('operation')=='source_scope_alias']
    assert aliases and all(c.facts[f['inputs'][0]]['entity']=='Company total' for f in aliases)
    uplift=next(f for f in c.derived if f['label']=='Reported-to-adjusted LTM EBITDA uplift')
    assert uplift['value']==pytest.approx(2760666.666666666)
    sensitivity=next(f for f in c.derived if f.get('illustrative'))
    assert sensitivity['value']==pytest.approx(7649548)
    departed=next(f for f in c.derived if 'listed departed' in f['label'])
    notice=next(f for f in c.derived if 'listed notice' in f['label'])
    assert departed['value']==482000 and notice['value']==152000
    share=next(f for f in c.derived if f['label'].startswith('Redfern') and 'WIP Over' in f['label'])
    assert share['value']==pytest.approx(413400/495300) and share['grain']=='snapshot'
    # Required financial bridge survives targeted input selection.
    assert any(f['label']=='ebitda variance versus budget' for f in packet['facts'])


def test_generalization_calculations():
    r,fs=baseline('summit');p,c=build_packet(r,fs)
    assert next(f for f in c.derived if f['label']=='ebitda variance versus budget')['value']==-157000
    assert next(f for f in c.derived if 'Overtime cost variance' in f['label'])['value']==99000
    assert next(f for f in c.derived if 'Lakeshore' in f['label'] and 'Gross Profit variance' in f['label'])['value']==-135000
    r,fs=baseline('original');p,c=build_packet(r,fs)
    assert c.facts['calc_known_synergy_trim']['value']==pytest.approx(505378.05)
    assert c.facts['calc_known_billing_total']['company']!=c.facts['calc_known_gross_profit']['company']
    assert c.facts['calc_known_gross_profit_budget']['scenario']=='budget'


def test_no_arithmetic_across_incompatible_scopes():
    f=dict(id='a',file='file',sheet='s',ref='A1',label='revenue',value=100,unit='money',currency='USD',scale=1,period='2026-09',grain='month',entity='unit',company='company',scenario='actual',basis='unknown')
    for field,value in [('grain','quarter'),('currency','unknown'),('entity','other'),('period','2026-08'),('basis','cash'),('file','other')]:
        b=dict(f,id='b',**{field:value});c=Calculations([f,b]);assert c.make('difference',['a','b'],'unsafe') is None
    b=dict(f,id='b',value=0);assert Calculations([f,b]).make('ratio',['a','b'],'zero denominator') is None
    q=canonical(dict(f,label='Q3 2026 revenue',column_label='Unit',sheet_context={}),f['period']);assert q['grain']=='quarter'


def item(issue,fid):
    return dict(title='Source-backed exposure',issue_id=issue,kind='risk',conclusion='The exposure warrants underwriting review.',evidence='The reported amount is {'+fid+'}.',financial_implication='The exposure is {'+fid+'}.',assessment='This may affect earnings durability; the operating explanation remains unresolved.',action='Reconcile the cited exposure with management.',management_question='Which source-supported actions address the cited exposure?',fact_ids=[fid],duration='unresolved')


def test_partial_acceptance_and_strict_safeguards():
    r,fs=baseline();p,c=build_packet(r,fs);fid=next(f['id'] for f in p['facts'] if f['unit']=='money' and not f.get('illustrative'))
    good=item(p['issues'][0]['id'],fid)
    bad=copy.deepcopy(good);bad['issue_id']=p['issues'][1]['id'];bad['financial_implication']='An unsupported $500 loss.'
    accepted,diag=validate(dict(findings=[good,bad]),p)
    assert len(accepted)==1 and any(d.get('code')=='unsupported_number' for d in diag)
    for field,value,code in [('fact_ids',['fabricated'],'invalid_fact_ids'),('duration','persistent','unsupported_assessment'),('assessment','This proves a loss.','unsupported_certainty')]:
        bad=copy.deepcopy(good);bad[field]=value;a,d=validate(dict(findings=[bad]),p);assert not a and any(x.get('code')==code for x in d)
    sensitivity=next(f for f in p['facts'] if f.get('illustrative'));bad=item(p['issues'][0]['id'],sensitivity['id']);a,d=validate(dict(findings=[bad]),p)
    assert not a and any(x.get('code')=='unqualified_sensitivity' for x in d)


def test_one_call_idempotence_accepted_only_outputs_and_exports(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test');monkeypatch.setenv('OPENAI_MODEL','gpt-6-luna')
    r,fs=baseline();initial=copy.deepcopy(r.package['ai_insights']);calls=[]
    def request(req):
        body=json.loads(req.data);p=json.loads(body['input'][1]['content']);calls.append(p)
        fid=next(f['id'] for f in p['facts'] if f['unit']=='money' and not f.get('illustrative'))
        good=item(p['issues'][0]['id'],fid);bad=item(p['issues'][1]['id'],fid);bad['title']='Rejected fabricated claim';bad['evidence']='Fabricated $12345 claim.'
        return dict(status='completed',output=[dict(content=[dict(type='output_text',text=json.dumps(dict(findings=[good,bad])))])],usage=dict(input_tokens=100,output_tokens=100))
    with inference_session(True):
        investigate(r,fs,request);investigate(r,fs,request)
    assert len(calls)==1 and r.package['ai_insights']==initial
    assert r.package['investigation']['accepted']==1 and r.package['investigation']['rejected']==1
    from package_analysis import analysis_findings
    assert any(f['id']==9000 and f['calculation'] for f in analysis_findings(r))
    v=present(r);assert v['cards'][0]['id']==9000
    assert 'Rejected fabricated' not in str(v) and report_findings(r)[0]['action']=='Reconcile the cited exposure with management.'
    for template in [None,(ROOT/'sample_templates/Sample_Firm_Review_Template.xlsx').read_bytes()]:
        data,_,_=export_report(r,template);assert data


def test_followup_failure_preserves_initial_analysis(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test');monkeypatch.setenv('OPENAI_MODEL','gpt-6-luna')
    r,fs=baseline();initial=copy.deepcopy(present(r))
    with inference_session(True):investigate(r,fs,lambda req: (_ for _ in ()).throw(TimeoutError()))
    assert r.package['investigation']['status']=='api_failure'
    assert present(r)==initial


def test_unresolved_causes_questions_and_negative_statements_are_not_assertions():
    r,fs=baseline();p,c=build_packet(r,fs);fid=next(f['id'] for f in p['facts'] if f['unit']=='money' and not f.get('illustrative'))
    good=item(p['issues'][0]['id'],fid)
    good['assessment']='Their causes, persistence, and contribution to earnings remain unresolved; margin risks require investigation.'
    good['management_question']='What explains the cited financial exposure?'
    good['financial_implication']='The amount is {'+fid+'}; this does not prove collectability or cause.'
    a,d=validate(dict(findings=[good]),p);assert len(a)==1,d
    good['assessment']='The snapshot is established, but aging alone does not prove collectability or cause; further losses remain risks, not established outcomes.'
    a,d=validate(dict(findings=[good]),p);assert len(a)==1,d
    bad=copy.deepcopy(good);bad['conclusion']='This causes a financial loss.'
    a,d=validate(dict(findings=[bad]),p);assert not a and any(x.get('code')=='unsupported_causality_or_duration' for x in d)
    bad=copy.deepcopy(good);bad['financial_implication']+=' But fraud caused the exposure.'
    a,d=validate(dict(findings=[bad]),p);assert not a


def test_verified_scope_note_is_not_a_numerical_fact():
    r,fs=baseline();p,c=build_packet(r,fs);fid=next(f['id'] for f in p['facts'] if f['unit']=='money' and not f.get('illustrative'))
    note=p['source_statements'][0]['id'];good=item(p['issues'][0]['id'],fid)
    good['fact_ids'].append(note);good['evidence']+=' The source describes comparison scope {'+note+'}.'
    a,d=validate(dict(findings=[good]),p);assert len(a)==1,d
    bad=copy.deepcopy(good);bad['fact_ids'].append('quote_fabricated')
    a,d=validate(dict(findings=[bad]),p);assert not a and any(x.get('code')=='invalid_fact_ids' for x in d)


def test_engine_runs_initial_then_exactly_one_followup_and_caches(monkeypatch,tmp_path):
    import io
    from engine import analyze
    from test_ai_investment import files,model_result,response
    from report_cache import ReportCache,cache_key,successful
    monkeypatch.setenv('OPENAI_API_KEY','test');monkeypatch.setenv('OPENAI_MODEL','gpt-6-luna')
    calls=[]
    def provider(req,timeout=None):
        body=json.loads(req.data);p=json.loads(body['input'][1]['content']);calls.append(body['text']['format']['name'])
        if calls[-1]=='investment_interpretation':out=response(model_result(p))
        else:
            fid=next(f['id'] for f in p['facts'] if f['unit']=='money' and not f.get('illustrative'))
            out=response(dict(findings=[item(p['issues'][0]['id'],fid)]))
        out['model']='gpt-6-luna';return io.StringIO(json.dumps(out))
    monkeypatch.setattr('urllib.request.urlopen',provider)
    fs=files();r=analyze(fs,ai_authorized=True)
    assert calls==['investment_interpretation','bounded_investigation']
    assert r.package['investigation']['accepted']==1
    assert [e['phase'] for e in r.package['inference']['events']]==['investment_analysis','investment_investigation']
    assert successful(r)
    cache=ReportCache(tmp_path);key=cache_key(fs,ai_authorized=True)
    assert cache.save(key,r);loaded=cache.load(key)
    assert present(loaded)==present(r) and loaded.package['inference']['attempts']==0
    assert len(calls)==2
    rejected=copy.deepcopy(r);rejected.package['investigation']['status']='validation_failure'
    assert not cache.save('failed-followup',rejected)
