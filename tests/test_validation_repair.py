"""Finding isolation, accepted-only narratives and exact configured-model routing."""
import copy
import io
import json
import urllib.error
import pytest
from openpyxl import load_workbook
from engine import analyze,InputError
from executive import briefing,present
from reports import export_report
from ai_runtime import load_environment,configuration,inference_session,complete
from test_ai_investment import config,files,fake_model,response


@pytest.mark.parametrize('fault,code',[
    ('fact_ids','invalid_fact_ids'),('number','unsupported_number'),
    ('placeholder','uncited_placeholder'),('schema','schema_error'),
    ('quote','invalid_claim_citation'),('certainty','unsupported_certainty')])
def test_mixed_findings_keep_good_item_and_exclude_bad_narrative(monkeypatch,fault,code):
    def transform(result):
        good=result['insights'][0]
        bad=copy.deepcopy(good)
        if fault=='fact_ids':bad['fact_ids']=['fabricated_id']
        if fault=='number':bad['text']='The company lost $999,000.'
        if fault=='placeholder':bad['text']='Reported result is {uncited_id}.'
        if fault=='schema':bad['claim']=[]
        if fault=='quote':bad['claim']['quote']='Management invented this quote.'
        if fault=='certainty':bad['why_it_matters']='This proves fraud.'
        result['insights'].append(bad)
        # Valid IDs cannot authorize independent assertions, even without numbers.
        result['briefing']=[dict(text='Management has recovered completely.',fact_ids=good['fact_ids'])]
        # A malformed legacy item must not discard valid investment findings.
        result['metrics']=[dict(series_id='made_up')]
        return result
    fake_model(monkeypatch,transform)
    r=analyze(files(),ai_authorized=True)
    d=r.package['ai_validation']
    assert (d['generated'],d['accepted'],d['rejected'])==(2,1,1)
    assert any(e['index']==1 and e['code']==code for e in d['items'])
    assert len(r.package['ai_insights'])==1
    text=briefing(present(r))
    assert '86.0%' in text and 'recovered completely' not in text
    assert all(p['finding_id']==8000 for p in r.package['ai_briefing'])
    assert present(r)['questions']==[r.package['ai_insights'][0]['management_question']]
    for template in (None,(__import__('engine').ROOT/'sample_templates/Sample_Firm_Review_Template.xlsx').read_bytes()):
        data,_,_=export_report(r,template)
        wb=load_workbook(io.BytesIO(data))
        summary=' '.join(str(row) for row in wb['Partner Review' if template else 'Executive Summary'].values)
        assert '86.0%' in summary and 'recovered completely' not in summary and '999,000' not in summary


def test_env_file_model_is_shared_but_explicit_environment_wins(monkeypatch,tmp_path):
    path=tmp_path/'.env'
    path.write_text('OPENAI_MODEL=gpt-6-luna\nOPENAI_API_KEY=unused-test-key\nOPENAI_ANALYSIS_MODEL=ignored\n')
    monkeypatch.delenv('OPENAI_MODEL',raising=False)
    load_environment(path)
    assert configuration()['model']=='gpt-6-luna'
    assert configuration()['model_source']==str(path)
    seen=[]
    with inference_session(True):
        for phase in ('workbook_interpretation','investment_analysis'):
            def send(req):
                seen.append(json.loads(req.data)['model'])
                return response({})
            complete(dict(model='gpt-4o-mini',max_output_tokens=100,input=[]),phase,send)
    assert seen==['gpt-6-luna','gpt-6-luna']
    monkeypatch.setenv('OPENAI_MODEL','gpt-4.1-mini')
    load_environment(path)
    assert configuration()['model']=='gpt-4.1-mini'
    assert configuration()['model_source']=='process environment'


def test_unavailable_model_reports_error_without_fallback(monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL','gpt-6-luna');seen=[]
    def fail(req):
        seen.append(json.loads(req.data)['model'])
        raise urllib.error.HTTPError(req.full_url,404,'Not found',{},None)
    with inference_session(True) as session:
        with pytest.raises(InputError,match='gpt-6-luna; no fallback'):
            complete(dict(input=[],max_output_tokens=100),'investment_analysis',fail)
    assert seen==['gpt-6-luna'] and session.events[0]['status']=='http_404'


def test_luna_cost_accounts_for_provider_cache_usage(monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL','gpt-6-luna')
    def send(req):
        result=response({});result['model']='gpt-6-luna'
        result['usage']={'input_tokens':100,'output_tokens':10,'input_tokens_details':{'cached_tokens':20,'cache_write_tokens':30}}
        return result
    with inference_session(True) as session:
        complete(dict(input=[],max_output_tokens=100),'investment_analysis',send)
    assert session.events[0]['estimated_usd']==pytest.approx(.00001395)
    assert session.events[0]['cache_write_tokens']==30
    assert session.events[0]['estimated_usd']<session.events[0]['reserved_upper_usd']


def test_numeric_financial_evidence_has_canonical_id_without_text_coercion():
    from analyst_ai import validated_evidence_facts
    from engine import Review
    packet={'facts':[dict(id='source',file='book.xlsx',sheet='Economics',ref="'Economics'!B4",label='Revenue',unit='money',currency='USD',scale=1,value=1000,period='2028-09',company='Example',entity='')],'grid_facts':[]}
    review=Review(evidence=[{'Fact ID':'computed_revenue','File':'book.xlsx','Reference':"'Economics'!B4",'Validated value':1000,'Check / use':'Recomputed source value'},{'Fact ID':'text_only','File':'book.xlsx','Reference':'A1','Validated value':'more than 1000','Check / use':'Unverified note'}])
    facts=validated_evidence_facts(packet,review)
    assert facts['computed_revenue']['value']==1000 and facts['computed_revenue']['unit']=='money'
    assert 'text_only' not in facts


def test_cited_entity_identifier_is_not_an_unsupported_financial_figure():
    from investment_output import grounded
    facts={'metric':dict(entity='Unit 12 (north)',value=.86,unit='ratio')}
    assert '86.0%' in grounded('Unit 12 reported {metric}.',['metric'],facts,45)
    for text in ('Unit 13 reported {metric}.','Unit 12 fell 10%.','Unit 12% reported {metric}.'):
        with pytest.raises(InputError):grounded(text,['metric'],facts,45)


def test_explicit_causation_disclaimer_is_not_a_causal_assertion():
    from investment_output import grounded
    facts={'metric':dict(entity='Example',value=10,unit='count')}
    text='This may warrant review but does not establish that operating metrics caused the result.'
    assert grounded(text,['metric'],facts,35)==text
    for text in ('This may warrant review but operating metrics caused the result.','This does not establish that staffing caused the result but fraud caused the loss.'):
        with pytest.raises(InputError):grounded(text,['metric'],facts,45)
