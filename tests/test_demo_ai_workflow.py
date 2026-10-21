"""Demo generation runs AI automatically; non-demo uploads retain explicit consent."""
import json
import io
import pytest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from engine import ROOT,InputError
from ai_runtime import complete


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','offline-test-key')
    monkeypatch.setenv('OPENAI_MODEL','gpt-6-luna')
    monkeypatch.setattr('mapping_ui.load_profiles',lambda:{})


def app(files=None):
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
    if files:at.session_state['uploaded_inputs']=files
    at.run()
    assert not at.exception
    return at


def generate(at):
    next(b for b in at.button if b.label.startswith('Generate Portfolio Review')).click().run()
    assert not at.exception
    return at.session_state['review']


def model(monkeypatch):
    seen=[]
    def invoke(body,phase,request_fn=None):
        def send(req):
            sent=json.loads(req.data);seen.append((phase,sent['model']))
            packet=json.loads(sent['input'][1]['content'])
            fact=packet['facts'][0];ref=fact['id']
            item=dict(title='Reported measure warrants follow-up',theme='financial',kind='risk',text='The reported measure is {'+ref+'}.',why_it_matters='This may warrant management follow-up within the stated reporting scope.',management_question='What explains the reported measure and what follow-up is warranted?',fact_ids=[ref],claim=dict(quote_id='',quote='',fact_id='',operator='none',threshold=''))
            result=dict(metrics=[],claims=[],interpretations=[],insights=[item],briefing=[])
            return dict(status='completed',model=sent['model'],usage=dict(input_tokens=100,output_tokens=100),output=[dict(content=[dict(type='output_text',text=json.dumps(result))])])
        return complete(body,phase,send)
    monkeypatch.setattr('analyst_ai.complete',invoke)
    return seen


def test_use_demo_generate_invokes_configured_ai_without_checkbox(monkeypatch):
    seen=model(monkeypatch);at=app()
    next(b for b in at.button if b.label=='Use Demo Files').click().run()
    assert not any('external analysis' in c.label.lower() for c in at.checkbox)
    assert not any('AI model:' in c.value or 'maximum $' in c.value for c in at.caption)
    assert not any(e.label=='External analysis permission' for e in at.expander)
    r=generate(at)
    assert seen==[('investment_analysis','gpt-6-luna')]
    assert r.package['inference']['authorized'] and r.package['ai_insights']
    wb=load_workbook(io.BytesIO(at.session_state['export'][0]))
    assert any('Reported measure' in str(row) for row in wb['Executive Summary'].values)


def test_uploaded_exact_synthetic_fixture_is_also_automatic(monkeypatch):
    seen=model(monkeypatch)
    source=ROOT/'tests/fixtures/A_Northstar.xlsx'
    at=app({'renamed-demo.xlsx':source.read_bytes()})
    assert not any('external analysis' in c.label.lower() for c in at.checkbox)
    generate(at)
    assert seen and all(m=='gpt-6-luna' for _,m in seen)


def test_changed_or_mixed_upload_never_inherits_demo_authorization(monkeypatch):
    seen=model(monkeypatch)
    source=ROOT/'tests/fixtures/A_Northstar.xlsx'
    at=app({source.name:source.read_bytes()+b'\x00'})
    consent=next(c for c in at.checkbox if c.label=='Authorize external analysis of these uploads')
    assert not consent.value
    disclosure=next(e for e in at.expander if e.label=='External analysis permission')
    assert not disclosure.proto.expanded
    assert any('sends extracted financial facts' in m.value for m in at.markdown)
    r=generate(at)
    assert not seen and not r.package['inference']['authorized']
    assert any('not authorized' in w.value for w in at.warning)


def test_demo_ai_failure_is_brief_and_only_after_generation(monkeypatch):
    def fail(*args,**kwargs):raise InputError('Internal provider failure detail')
    monkeypatch.setattr('analyst_ai.complete',fail)
    at=app();next(b for b in at.button if b.label=='Use Demo Files').click().run()
    assert not any('AI analysis' in w.value for w in at.warning)
    generate(at)
    assert any(w.value=='AI analysis could not complete. Your source-based review and Excel report are ready.' for w in at.warning)
    assert not any('Internal provider failure detail' in w.value for w in at.warning)
    assert at.session_state['export'][0]


def test_demo_without_provider_still_generates_offline(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY')
    at=app();next(b for b in at.button if b.label=='Use Demo Files').click().run()
    assert not any('external analysis' in c.label.lower() for c in at.checkbox)
    r=generate(at)
    assert r.package['inference']['attempts']==0 and at.session_state['export'][0]
    assert any('AI analysis was unavailable.' in w.value for w in at.warning)
