"""Upload -> Generate stays optional-review-first, with truthful recognition."""
from streamlit.testing.v1 import AppTest
import pytest
from engine import ROOT

@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.setattr('mapping_ui.load_profiles',lambda:{})


def app(files=None):
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
    if files:at.session_state['uploaded_inputs']=files
    return at.run()


def generate(at):
    button=next(b for b in at.button if b.label.startswith('Generate Portfolio Review'))
    assert not button.disabled
    button.click().run()
    assert not at.exception
    return at.session_state['review']


def test_three_steps_standard_default_and_single_action():
    at=app()
    assert not at.exception
    assert [h.value for h in at.subheader]==['1 — Upload Financial Files','2 — Choose Output Format','3 — Generate Portfolio Review']
    assert at.radio(key='report_format').value=='Standard Excel report'
    assert len([b for b in at.button if b.label.startswith('Generate Portfolio Review')])==1
    assert next(b for b in at.button if b.label.startswith('Generate Portfolio Review')).disabled
    assert all(not e.proto.expanded for e in at.expander)


def test_summit_summary_only_claims_supported_recognition():
    p=ROOT/'tests/fixtures/Summit_Home_Services_Sep2026.xlsx'
    at=app({p.name:p.read_bytes()})
    captions=' '.join(c.value for c in at.caption)
    assert 'Income statement recognized' in captions and 'Branch reporting recognized' in captions
    assert 'supporting schedules are checked during generation' in captions
    assert not any(e.proto.expanded for e in at.expander)
    r=generate(at)
    assert r.metrics['revenue']==3298000 and r.metrics['ebitda']==502000
    assert at.session_state['export'][0]
    assert all(not e.proto.expanded for e in at.expander)
    assert any('$47K' in m.value for m in at.markdown)


def test_unfamiliar_statement_uncertainty_does_not_block_other_metrics():
    p=ROOT/'tests/fixtures/B_Harbor.xlsx'
    at=app({p.name:p.read_bytes()})
    assert any('may need review. You can continue.' in c.value for c in at.caption)
    assert not next(e for e in at.expander if e.label=='Review Account Mappings').proto.expanded
    r=generate(at)
    assert 'revenue' in r.metrics
    assert any(not row['accepted'] for row in r.normalized)
    assert any('unconfirmed' in w for w in r.warnings)
    assert at.session_state['export'][0]


def test_unrecognized_file_does_not_claim_financial_readiness():
    at=app({'notes.csv':b'Name,Notes\nExample,No financial statement\n'})
    assert not at.exception
    captions=' '.join(c.value for c in at.caption)
    assert 'recognition is limited' in captions
    assert 'Financial analysis available' not in captions


def test_valid_analysis_without_findings_is_not_described_as_failed():
    at=app({'plain.csv':b'Example Company,,\nUSD whole units accrual,,\nAccount,Sep-26 Actual,Aug-26 Actual\nRevenue,100,100\nCost of sales,60,60\nGross profit,40,40\n'})
    r=generate(at)
    assert r.metrics['revenue']==100 and not r.findings
    assert any('No material findings were established' in i.value for i in at.info)
    assert not any('No priority analyses could be completed' in i.value for i in at.info)
