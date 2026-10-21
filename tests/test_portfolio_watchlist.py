from portfolio_data import load_companies
from portfolio_watchlist import watchlist, source_closure


def test_every_original_finding_question_caveat_and_source_is_retained():
    companies = load_companies()
    items = watchlist(companies)
    assert len(items) == 17
    by_company = {c.id: c for c in companies}
    for item in items:
        r = by_company[item.company_id].review
        original = next(f for f in r.package['ai_insights'] if f['id'] == item.finding['id'])
        assert item.finding == original
        assert item.presentation['caveat']
        assert set(original['fact_ids']) <= set(item.source_ids)
        assert set(original['fact_ids']) <= {e['Fact ID'] for e in item.evidence}
        assert any(e['Reference'].startswith("'") for e in item.evidence)
        assert item.report_period == r.report_period
    assert items[0].finding['priority'] == 'high'
    assert items[0].finding['disposition'] == 'act_now'
    summit = companies[0].review
    closure = source_closure(summit, ['calc_51'])
    assert {'calc_51', 'calc_1', 'calc_2'} <= set(closure)
    assert any(s.startswith('s2_') for s in closure)
