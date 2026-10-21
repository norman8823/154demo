"""Display existing validated values without changing findings or cached analyses."""
import re
from html import escape


# Require a financial/operating unit: source IDs, years and status labels are not metrics.
_METRIC = re.compile(r"(?<![\w])(?:[−+\-]?(?:[$€£]|(?:USD|GBP|EUR|CAD|AUD)\s)[−+\-]?\d[\d,]*(?:\.\d+)?(?:[KMB](?![a-z]))?|[−+\-]?\d[\d,]*(?:\.\d+)?\s*(?:%|pp\b|days\b|x\b))")


def card_metric(card, review):
    """Prefer designated impact; otherwise use an exact metric in accepted AI prose.

    Never derive a new amount, percentage or direction from cited source cells.
    Relationship findings retain neutral metric typography.
    """
    from investigation import active_findings
    insights = active_findings(review)
    accepted = next((item for item in insights if item['id'] == card['id']), None)
    impact = str(card.get('impact') or '').strip()
    if _METRIC.fullmatch(impact):
        return impact, bool(card.get('adverse')) if accepted is None else accepted['kind'] == 'risk'
    if accepted:
        text = accepted['text']
        matches = list(_METRIC.finditer(text))
        # Prefer a measure named in the title over an incidental earlier figure.
        terms = set(re.findall(r'[a-z]+', accepted.get('title', card['title']).lower()))
        if 'earnings' in terms:
            terms.update({'ebitda', 'profit', 'income', 'margin'})
        relevant = [m for m in matches if terms.intersection(
            re.findall(r'[a-z]+', text[max(0, m.start()-45):m.start()].lower())[-4:])]
        if matches:
            return (relevant or matches)[0].group(), accepted['kind'] == 'risk'
    return '', False


def finding_html(card, review):
    value, adverse = card_metric(card, review)
    tone = '' if card.get('adverse') else ' amber'
    metric = (f'<div class="indicator{ " adverse" if adverse else "" }">{escape(value)}</div>' if value else '')
    return (f'<div class="finding{tone}"><span class="badge{tone}">{escape(card["kind"])}</span>'
            f'<h3>{escape(card["title"])}</h3>{metric}<p>{escape(card["summary"])}</p></div>')
