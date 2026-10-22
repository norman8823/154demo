"""Data Landscape terminology and navigation preserve the foundation route/data."""
from streamlit.testing.v1 import AppTest
from engine import ROOT


def test_landscape_navigation_order_heading_workflow_and_unchanged_kpis():
    at=AppTest.from_file(str(ROOT/'portfolio_app.py'),default_timeout=60).run()
    expected=[('Portfolio Overview','nav_overview'),('Investment Detail','nav_company'),
              ('Data Landscape','nav_foundation'),('Documents & Reports','nav_excel')]
    assert [(b.label,b.key) for b in at.sidebar.button if str(b.key).startswith('nav_')]==expected
    at.button(key='nav_foundation').click().run()
    assert not at.exception
    assert at.query_params['page']=='foundation'
    assert at.title[0].value=='Data Landscape'
    assert at.subheader[0].value=='AI Workflow Readiness'
    html='\n'.join(m.value for m in at.markdown)
    assert 'Overview of portfolio data sources, definitions, quality, mapping gaps, and readiness for AI-enabled workflows.' in html
    assert 'Monthly Portfolio Operating Review' in html
    assert 'Portfolio / Data Landscape' in html
    assert '76/100' in html and '67%' in html
    assert '>4</span><span class="foundation-kpi-label">Data Issues' in html
    assert all(h in [s.value for s in at.subheader] for h in ('Data Catalog & Dictionary','Data Issues','Structured Data Export'))
    assert at.selectbox(key='foundation_metric').options
    assert not any(b.label in ('Data Foundation','Investment Issues') for b in at.sidebar.button)
    at.query_params['page']='foundation';at.run()
    assert not at.exception and at.title[0].value=='Data Landscape'
