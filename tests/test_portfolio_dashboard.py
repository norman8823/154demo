from portfolio_data import load_companies
from portfolio_dashboard import workflow_summary, chart_records, ebitda_chart, operating_rows, comparison_matrix
from portfolio_comparison import comparison


def test_review_counts_and_chart_values_are_from_verified_reviews():
    companies = load_companies()
    assert workflow_summary(companies) == dict(companies=3, received=3, below_plan=3, comparable_budget=3, issues=17, act_now=6)
    for c in companies:
        rows = chart_records(c)
        v = comparison(c)
        assert [r['Scenario'] for r in rows] == ['Actual', 'Budget']
        assert [r['EBITDA'] for r in rows] == [v['ebitda'].actual, v['ebitda'].budget]
        assert {r['Reporting period'] for r in rows} == {v['period_label']}
        assert all(r['EBITDA'] > 0 and r['Source IDs'] for r in rows)
        spec = ebitda_chart(c).to_dict()
        assert spec['encoding']['y']['scale']['zero'] is True
        assert 'Reporting period' in [t['field'] for t in spec['encoding']['tooltip']]
    assert workflow_summary(companies[:1])['issues'] == 5
    assert len(operating_rows(companies)) == 3
    matrix = comparison_matrix(companies)
    assert matrix[0][companies[2].name] == 'FY2026 · annual'
    assert matrix[4][companies[0].name] == '$502K'
