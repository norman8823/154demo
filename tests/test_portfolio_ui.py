from engine import ROOT
from streamlit.testing.v1 import AppTest


def test_overview_uses_prepared_financials_and_explicit_periods():
    at = AppTest.from_file(str(ROOT / 'portfolio_app.py'), default_timeout=60).run()
    assert not at.exception
    text = '\n'.join(m.value for m in at.markdown)
    for expected in ('Summit Home Services', 'Tallis Brook Accounting', 'Harrow Ridge Environmental', '$3.30M', '$684K', '$9.71M',
                     'September 2026 · monthly', 'FY2026 · annual', '15.2%', '19.7%', '20.8%', 'No combined revenue'):
        assert expected in text
    assert len([b for b in at.button if b.label == 'View Investment Detail →']) == 3


def test_documents_library_separates_originals_and_generated_reports():
    at = AppTest.from_file(str(ROOT / 'portfolio_app.py'), default_timeout=60)
    at.session_state['source_viewport']={'desktop':True}
    at.run()
    at.button(key='nav_excel').click().run()
    assert not at.exception
    assert at.title[0].value == 'Documents & Reports'
    assert [s.value for s in at.subheader] == ['Source Documents','Generated Reports']
    assert len([b for b in at.button if b.label == 'Preview']) == 3
    assert not any('Workbook preview' in s.value for s in at.subheader)
