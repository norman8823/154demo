"""Operational review models over approved Reviews; no new investment analytics."""
import altair as alt
import pandas as pd
from portfolio_comparison import comparison, money, percent


def workflow_summary(companies):
    views = [comparison(c) for c in companies]
    findings = [f for c in companies for f in c.review.package['ai_insights']]
    return dict(companies=len(companies), received=sum(c.review.package['skill_engine']['status'] == 'completed' for c in companies),
                below_plan=sum(v['ebitda'].actual is not None and v['ebitda'].budget is not None and v['ebitda'].actual < v['ebitda'].budget for v in views),
                comparable_budget=sum(v['ebitda'].actual is not None and v['ebitda'].budget is not None for v in views),
                issues=len(findings), act_now=sum(f.get('disposition') == 'act_now' for f in findings))


def operating_rows(companies):
    from portfolio_investments import investments_for, investment_summary
    investments={i.company_id:i for i in investments_for(companies)}
    rows = []
    for c in companies:
        v = comparison(c)
        rows.append({'Company': c.name, 'Reporting period': v['period_label'], 'Revenue': v['revenue'].actual,
                     'Reported EBITDA': v['ebitda'].actual, 'EBITDA budget': v['ebitda'].budget,
                     'EBITDA margin': v['margin'].actual, 'EBITDA vs budget': v['ebitda'].variance_pct,
                     'Revenue vs budget': v['revenue'].variance_pct, 'Company ID': c.id})
        investment=investments[c.id];result=investment_summary([investment])
        rows[-1].update({'Invested capital (illustrative)':result['invested_capital'],'Current equity (illustrative)':result['current_equity_value'],
                        'Gross MOIC (illustrative)':result['gross_moic'],'Gross IRR (illustrative)':result['gross_irr'],'Investment valuation date':result['valuation_date'],'Sector':c.sector})
    return rows


def chart_records(company):
    v = comparison(company)
    m = v['ebitda']
    return [{'Company': company.name, 'Reporting period': v['period_label'], 'Scenario': name, 'EBITDA': value,
             'Source IDs': ', '.join(m.source_ids), 'Unit': m.unit}
            for name, value in [('Actual', m.actual), ('Budget', m.budget)] if value is not None]


def ebitda_chart(company):
    """One company/period per independent positive-baseline small multiple."""
    records = chart_records(company)
    base = alt.Chart(pd.DataFrame(records)).encode(
        x=alt.X('Scenario:N', sort=['Actual', 'Budget'], title=None, axis=alt.Axis(labelAngle=0, labelColor='#61758a', labelPadding=8)),
        y=alt.Y('EBITDA:Q', title=None, scale=alt.Scale(zero=True), axis=alt.Axis(format='$~s', tickCount=3, gridColor='#edf1f5', domain=False, labelColor='#718497')),
        color=alt.Color('Scenario:N', scale=alt.Scale(domain=['Actual', 'Budget'], range=['#173e57', '#b8cbd9']), legend=None),
        tooltip=[alt.Tooltip('Company:N'), alt.Tooltip('Reporting period:N'), alt.Tooltip('Scenario:N'), alt.Tooltip('EBITDA:Q', format='$,.0f'), alt.Tooltip('Unit:N'), alt.Tooltip('Source IDs:N')])
    bars = base.mark_bar(size=48, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    return bars.properties(height=155).configure_view(stroke=None).configure_axis(labelFont='Arial', labelFontSize=10)


def comparison_matrix(companies):
    rows = [dict(Attribute=label) for label in ('Reporting period', 'Revenue', 'Revenue budget', 'Revenue vs budget', 'Reported EBITDA',
        'EBITDA budget', 'EBITDA variance', 'EBITDA vs budget', 'EBITDA margin', 'Budget margin', 'Margin variance', 'Accounting basis')]
    for c in companies:
        v = comparison(c)
        vals = [v['period_label'], money(v['revenue'].actual, v['revenue'].unit), money(v['revenue'].budget, v['revenue'].unit),
                percent(v['revenue'].variance_pct), money(v['ebitda'].actual, v['ebitda'].unit), money(v['ebitda'].budget, v['ebitda'].unit),
                money(v['ebitda'].variance, v['ebitda'].unit), percent(v['ebitda'].variance_pct), percent(v['margin'].actual), percent(v['margin'].budget),
                f"{v['margin'].variance:+.1f} pp" if v['margin'].variance is not None else 'Unavailable', v['basis']]
        for row, value in zip(rows, vals):
            row[c.name] = value
    from portfolio_investments import investments_for, investment_summary
    extra=[dict(Attribute=label) for label in ('Illustrative valuation date','Illustrative invested capital','Illustrative current sponsor equity','Illustrative gross MOIC','Illustrative gross IRR')]
    for i in investments_for(companies):
        company=next(c for c in companies if c.id==i.company_id);result=investment_summary([i])
        for row,value in zip(extra,[result['valuation_date'],money(result['invested_capital']),money(result['current_equity_value']),f'{result["gross_moic"]:.2f}x',f'{result["gross_irr"]:.2%}' if result['gross_irr'] is not None else 'Unavailable']):row[company.name]=value
    return rows+extra
