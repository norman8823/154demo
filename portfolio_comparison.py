"""Period-aware presentation over the existing verified financial-table adapter."""
from dataclasses import dataclass
import math
from excel_layout import financial_table

COMPARABILITY = ('Company figures are presented separately. Summit and Tallis report September monthly results; '
                 'Harrow reports FY2026. No combined revenue, EBITDA or portfolio margin is calculated. '
                 'Accounting bases and entity boundaries are not established for consolidation. '
                 'Unavailable means a comparable source or denominator was not established.')


@dataclass(frozen=True)
class Metric:
    name: str
    actual: float | None
    budget: float | None
    variance: float | None
    variance_pct: float | None
    unit: str
    period: str
    source_ids: tuple
    definition: str


def finite(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def ratio(numerator, denominator):
    a, b = finite(numerator), finite(denominator)
    return a / b if a is not None and b is not None and b > 0 else None


def comparison(company):
    r = company.review
    rows = {row[13]: row for row in financial_table(r)}
    result = {}
    for key in ('revenue', 'ebitda'):
        row = rows.get(key)
        if row is None:
            result[key] = Metric(key, None, None, None, None, r.currency, r.report_period, (), 'Unavailable: comparable source not established')
        else:
            result[key] = Metric(key, *(finite(row[i]) for i in (1, 2, 3, 4)), row[9], row[10], tuple(row[12].split('; ')),
                                 'Reported revenue' if key == 'revenue' else 'Reported EBITDA; excludes adjusted EBITDA sensitivities')
    revenue, ebitda = result['revenue'], result['ebitda']
    refs = tuple(dict.fromkeys(revenue.source_ids + ebitda.source_ids))
    records = [n for n in r.normalized if n.get('fact_id') in refs]
    metadata = {(n.get('company'), n.get('basis'), n.get('currency'), n.get('scale'), n.get('source_file')) for n in records}
    compatible = (revenue.period == ebitda.period and revenue.unit == ebitda.unit
                  and revenue.unit not in ('unknown', 'source units') and len(metadata) == 1
                  and all(n.get('currency') not in (None, 'unknown') and n.get('scale') is not None for n in records))
    actual = ratio(ebitda.actual, revenue.actual) if compatible else None
    budget = ratio(ebitda.budget, revenue.budget) if compatible else None
    variance = (actual - budget) * 100 if actual is not None and budget is not None else None
    result['margin'] = Metric('EBITDA margin', actual, budget, variance, None, 'ratio', revenue.period, refs,
                              'Reported EBITDA / revenue; margin variance is percentage points; no annualization')
    result['period'] = r.report_period
    grains = {n.get('grain') for n in records}
    result['frequency'] = 'Annual' if grains == {'annual'} else ('Monthly' if grains == {'month'} else 'Scope unavailable')
    result['period_label'] = r.report_period + ' · ' + result['frequency'].lower()
    result['basis'] = ', '.join(sorted({n.get('basis') or 'unknown' for n in records})) or 'unknown'
    return result


def money(value, currency='$'):
    if value is None:
        return 'Unavailable'
    sign = '−' if value < 0 else ''
    number = abs(value)
    suffix, scale = ('M', 1e6) if number >= 1e6 else (('K', 1e3) if number >= 1e3 else ('', 1))
    digits = 2 if suffix == 'M' else 0
    prefix = '$' if currency in ('$', 'USD') else currency + ' '
    return f'{sign}{prefix}{number / scale:,.{digits}f}{suffix}'


def percent(value):
    return f'{value:.1%}' if value is not None else 'Unavailable'


def against_plan(metric):
    return f'{metric.variance_pct:+.1%} vs budget' if metric.variance_pct is not None else 'Budget comparison unavailable'
