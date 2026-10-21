"""Lossless cross-company findings with transparent, inherited priority ordering."""
from copy import deepcopy
from dataclasses import dataclass
from package_analysis import analysis_findings


@dataclass(frozen=True)
class WatchItem:
    company_id: str
    company_name: str
    report_period: str
    finding: dict
    presentation: dict
    evidence: tuple
    source_ids: tuple


def source_closure(review, source_ids):
    """Include calculation operands all the way back to original source cells."""
    facts = {f['id']: f for f in review.package.get('facts', [])}
    facts.update({f['id']: f for f in review.package.get('skill_engine', {}).get('calculations', [])})
    ordered = []
    def visit(source_id):
        if source_id in ordered:
            return
        ordered.append(source_id)
        for operand in facts.get(source_id, {}).get('inputs', []):
            visit(operand)
    for source_id in source_ids:
        visit(source_id)
    return tuple(ordered)


def evidence_for(review, source_ids):
    # Multiple findings can cite a fact; retain the first identical source record.
    by_id = {}
    for evidence in review.evidence:
        by_id.setdefault(evidence['Fact ID'], evidence)
    return tuple(deepcopy(by_id[s]) for s in source_ids if s in by_id)


def watchlist(companies):
    items = []
    for company in companies:
        display = {f['id']: f for f in analysis_findings(company.review)}
        for finding in company.review.package['ai_insights']:
            ids = source_closure(company.review, finding['fact_ids'])
            items.append(WatchItem(company.id, company.name, company.review.report_period, deepcopy(finding),
                                   deepcopy(display[finding['id']]), evidence_for(company.review, ids), ids))
    priority = {'high': 0, 'medium': 1, 'low': 2}
    disposition = {'act_now': 0, 'investigate': 1, 'monitor': 2, 'opportunity': 3}
    # Stable sort preserves source order within each priority/disposition group.
    return tuple(sorted(items, key=lambda i: (priority.get(i.finding.get('priority'), 3),
                                             disposition.get(i.finding.get('disposition'), 4))))
