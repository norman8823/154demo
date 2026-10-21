"""Priority metrics are financial values, never evidence or validation status."""
from types import SimpleNamespace
import copy
import pytest
from card_presentation import card_metric, finding_html


def example(impact='Source-linked', text='Retention is 84.5% versus 91.0% previously.', kind='risk'):
    item=dict(id=8000, text=text, kind=kind,title='Retention warrants review',management_question='What actions will improve retention?',why_it_matters='This may weaken revenue quality.',classification='AI interpretation / hypothesis',fact_ids=['test_metric'])
    card=dict(id=8000, impact=impact, adverse=True, kind='AI interpretation / hypothesis', title='Retention warrants review', summary=text)
    return card, SimpleNamespace(package=dict(ai_insights=[item]))


@pytest.mark.parametrize('status',['Source-linked','Contradicted','Supported','Unverifiable'])
def test_status_is_replaced_by_accepted_metric(status):
    card, review=example(impact=status)
    before=copy.deepcopy((card,review.package))
    assert card_metric(card,review)==('84.5%',True)
    html=finding_html(card,review)
    assert '<div class="indicator adverse">84.5%</div>' in html
    assert status not in html
    assert (card,review.package)==before


@pytest.mark.parametrize('text',['Review client concentration.','Venue 01 requires review.','Review the 2026 reporting basis.'])
def test_no_placeholder_or_identifier_when_metric_is_absent(text):
    card, review=example(text=text)
    assert card_metric(card,review)==('',False)
    assert 'class="indicator' not in finding_html(card,review)


@pytest.mark.parametrize('kind',['relationship','opportunity'])
def test_citations_and_relationships_do_not_make_metric_red(kind):
    card, review=example(kind=kind)
    assert card_metric(card,review)==('84.5%',False)
    assert '<div class="indicator">84.5%</div>' in finding_html(card,review)


@pytest.mark.parametrize('value',['−$262K','+3.2 pp','61 days','4.25x','USD 684,306'])
def test_existing_designated_metrics_keep_their_value(value):
    card, review=example(impact=value)
    review.package['ai_insights']=[]
    assert card_metric(card,review)==(value,True)


def test_numeric_prose_is_not_scraped_from_unaccepted_findings():
    card,review=example()
    review.package['ai_insights']=[]
    assert card_metric(card,review)==('',False)


def test_cached_review_renders_without_generating_analysis(monkeypatch):
    from engine import ROOT, analyze, demo_files
    from executive import present
    from streamlit.testing.v1 import AppTest
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    review=analyze(demo_files())
    summary=present(review)
    card,accepted=example()
    summary['cards'][0]=card
    review.package['view']=summary
    review.package['ai_insights']=accepted.package['ai_insights']
    review.package['ai_insights'][0]['fact_ids']=[review.evidence[0]['Fact ID']]
    at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
    from reports import export_report
    at.session_state['review']=review
    at.session_state['export']=export_report(review)
    at.session_state['view']='02  Portfolio Review'
    at.run()
    assert not at.exception
    panels=[m.value for m in at.markdown if 'class="finding' in m.value]
    assert len(panels)==len(present(review)['cards'])
    assert all('>Source-linked</div>' not in p and '>Contradicted</div>' not in p for p in panels)
    for card,panel in zip(present(review)['cards'],panels):
        value,adverse=card_metric(card,review)
        assert ('class="indicator' in panel)==bool(value)
        if value:assert ('indicator adverse' in panel)==adverse


def test_earnings_card_prefers_earnings_to_incidental_revenue():
    card,review=example(text='Net Revenue is $3,298,000 and EBITDA is $502,000 against budget of $659,000.')
    card['title']='Earnings need reconciliation'
    review.package['ai_insights'][0]['title']=card['title']
    assert card_metric(card,review)==('$502,000',True)
