from dataclasses import replace
from copy import deepcopy
import pytest
from portfolio_data import load_companies
from portfolio_comparison import comparison, ratio, money


@pytest.fixture(scope='module')
def companies():
    return load_companies()


def test_actual_values_periods_and_traceable_budget_math(companies):
    expected = [(3298000, 502000, 3207000, 659000, 'Monthly'),
                (3475418, 684306, 3651832, 946225, 'Monthly'),
                (46650000, 9712000, 47006000, 10895000, 'Annual')]
    for c, (rev, eb, rb, eb_b, frequency) in zip(companies, expected):
        v = comparison(c)
        assert v['frequency'] == frequency
        assert v['revenue'].actual == rev
        assert v['revenue'].budget == rb
        assert v['ebitda'].actual == eb
        assert v['ebitda'].budget == eb_b
        assert v['margin'].actual == pytest.approx(eb / rev)
        assert v['margin'].budget == pytest.approx(eb_b / rb)
        assert v['margin'].variance == pytest.approx((eb / rev - eb_b / rb) * 100)
        assert v['ebitda'].variance_pct == pytest.approx(eb / eb_b - 1)
        ids = {e['Fact ID'] for e in c.review.evidence}
        assert set(v['margin'].source_ids) <= ids
        assert all('total' not in k for k in v)
    assert comparison(companies[-1])['period'] == 'FY2026'


def test_missing_budget_unknown_units_and_no_denominator_are_unavailable(companies):
    r = deepcopy(companies[0].review)
    r.financial_rows = [row for row in r.financial_rows if ' · budget · ' not in row[0]]
    view = comparison(replace(companies[0], review=r))
    assert view['revenue'].budget is None
    assert view['margin'].budget is None
    r.normalized = [dict(n, currency='unknown') for n in r.normalized]
    assert comparison(replace(companies[0], review=r))['margin'].actual is None
    for denominator in (None, 0, -1, float('nan')):
        assert ratio(20, denominator) is None
    assert money(-1183000) == '−$1.18M'
    assert money(None) == 'Unavailable'


def test_incomparable_budget_is_not_silently_used(companies):
    r = deepcopy(companies[0].review)
    r.normalized = [dict(n, basis='cash') if n['scenario'] == 'budget' else n for n in r.normalized]
    v = comparison(replace(companies[0], review=r))
    assert v['revenue'].budget is None
    assert v['ebitda'].variance is None
