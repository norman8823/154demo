"""GP-01: portable source-bound Reviews and zero-inference viewing."""
import pytest
from portfolio_data import load_companies, company_by_id
from report_cache import successful


@pytest.fixture(scope='module')
def companies():
    return load_companies()


def test_registry_preserves_three_verified_review_contracts(companies):
    assert [c.id for c in companies] == ['summit', 'tallis', 'harrow']
    assert [c.review.report_period for c in companies] == ['September 2026', 'September 2026', 'FY2026']
    for company in companies:
        r = company.review
        assert successful(r, require_real=False)
        assert r.package['prepared_demo']['snapshot_sha256'] == company.provenance['snapshot_sha256']
        assert r.package['inference']['attempts'] == 0
        assert r.package['inference']['estimated_usd'] == 0
        assert r.package['inference']['origin']['inference_observed']
        assert company.provenance['workbook_sha256']
        evidence_ids = {e['Fact ID'] for e in r.evidence}
        assert all(set(f['fact_ids']) <= evidence_ids for f in r.package['ai_insights'])
    assert company_by_id(companies, 'tallis') is companies[1]
    assert company_by_id(companies, 'missing') is None


def test_adapter_does_not_invoke_analysis_or_configuration(monkeypatch):
    def reject(*a, **k):
        raise AssertionError('Portfolio viewing attempted analysis/configuration')
    monkeypatch.setattr('engine.analyze', reject)
    monkeypatch.setattr('ai_runtime.configuration', reject)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert len(load_companies()) == 3
