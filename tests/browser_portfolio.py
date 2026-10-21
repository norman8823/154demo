"""Actual Chrome journeys/downloads and screenshots against localhost:8502 only."""
import io
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/gp-portfolio'
OUT.mkdir(parents=True, exist_ok=True)
URL = os.environ.get('COPILOT_GP_TEST_URL', 'http://127.0.0.1:8502')
assert urlparse(URL).hostname in ('127.0.0.1', 'localhost')
results = {'companies': {}, 'external_requests': [], 'browser_errors': []}


def check(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state', 'notRunning', timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')


with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1510, 'height': 1600}, accept_downloads=True)
    page.on('pageerror', lambda error: results['browser_errors'].append(str(error)))
    def local_only(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1', 'localhost'):
            results['external_requests'].append(route.request.url)
            route.abort()
        else:
            route.continue_()
    page.route('**/*', local_only)
    page.goto(URL)
    expect(page.get_by_role('button', name='Open investment review →', exact=True)).to_have_count(3, timeout=60000)
    check(page)
    boxes = [page.locator('.st-key-gp_company_'+s).bounding_box() for s in ('summit', 'tallis', 'harrow')]
    assert all(boxes)
    assert max(b['width'] for b in boxes) - min(b['width'] for b in boxes) < 2
    assert max(b['height'] for b in boxes) - min(b['height'] for b in boxes) < 3
    page.screenshot(path=str(OUT/'overview-final.png'), full_page=True)
    with page.expect_download() as downloaded:
        page.get_by_role('button', name='↓ Download Portfolio Excel', exact=True).click()
    path = OUT/'portfolio-browser.xlsx'
    downloaded.value.save_as(path)
    gp = load_workbook(path)
    assert gp.sheetnames == ['Portfolio Overview', 'Company Comparison', 'Portfolio Watchlist', 'Source References']
    results['portfolio_download'] = {'bytes': path.stat().st_size, 'sheets': gp.sheetnames}
    for slug in ('summit', 'tallis', 'harrow'):
        page.locator('.st-key-open_'+slug+' button').click()
        expect(page.get_by_role('heading', name='Investment Summary', exact=True)).to_be_visible(timeout=60000)
        check(page)
        page.screenshot(path=str(OUT/(slug+'-summary.png')), full_page=True)
        page.get_by_role('heading', name='Management Questions', exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(OUT/(slug+'-assessment-questions.png')), full_page=True)
        page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTo(0,0)')
        outputs = {}
        for custom in (False, True):
            page.get_by_role('combobox', name='Company Excel format', exact=True).click()
            page.get_by_role('option', name='Use supplied firm template' if custom else 'Standard Excel report', exact=True).click()
            if custom:
                expect(page.get_by_text('Optional company Excel template', exact=True)).to_be_visible(timeout=60000)
            else:
                expect(page.get_by_text('Optional company Excel template', exact=True)).to_have_count(0)
            check(page)
            with page.expect_download() as download:
                page.get_by_role('button', name='↓  Download Excel Report', exact=True).first.click()
            destination = OUT/(slug+('-custom' if custom else '-standard')+'.xlsx')
            download.value.save_as(destination)
            book = load_workbook(destination)
            assert {'Findings', 'Source Evidence', 'Analyst Execution'} <= set(book.sheetnames)
            assert any(c.hyperlink for row in book['Findings'] for c in row)
            if custom:
                assert book['Partner Review']['C16'].data_type == 'f'
            else:
                assert 'Partner Review' not in book.sheetnames
            outputs['custom' if custom else 'standard'] = destination.stat().st_size
        page.get_by_role('button', name='View Evidence  →', exact=True).first.click()
        expect(page.get_by_role('heading', name='See where every conclusion came from', exact=True)).to_be_visible(timeout=60000)
        check(page)
        page.screenshot(path=str(OUT/(slug+'-evidence.png')), full_page=True)
        page.get_by_role('button', name='← Portfolio Overview', exact=True).click()
        expect(page.get_by_role('heading', name='Portfolio Overview', exact=True)).to_be_visible(timeout=60000)
        results['companies'][slug] = {'summary': 'pass', 'evidence': 'pass', 'return': 'pass', 'downloads': outputs}
    page.get_by_role('button', name='Portfolio Watchlist', exact=True).click()
    expect(page.get_by_role('heading', name='Portfolio Watchlist', exact=True)).to_be_visible()
    expect(page.get_by_text('17 findings shown', exact=False)).to_be_visible()
    assert page.locator('.katex').count() == 0
    expect(page.get_by_text('YTD reported EBITDA is $3,916,548 against budget of $5,311,831', exact=False)).to_be_visible()
    page.screenshot(path=str(OUT/'watchlist-top.png'), full_page=True)
    page.locator('.st-key-watch_tallis_10000 button').click()
    expect(page.get_by_role('heading', name='See where every conclusion came from', exact=True)).to_be_visible(timeout=60000)
    expect(page.get_by_role('radio', name='010000  Reported earnings materially trail plan', exact=True)).to_be_checked()
    page.get_by_text('Investment Summary & Priority Findings', exact=True).click()
    page.get_by_role('button', name='View source evidence', exact=True).click()
    expect(page.get_by_role('heading', name='See where every conclusion came from', exact=True)).to_be_visible(timeout=60000)
    expect(page.get_by_role('radio', name='010000  Reported earnings materially trail plan', exact=True)).to_be_checked()
    results['deep_link_summary_evidence_regression'] = 'pass'
    page.get_by_role('button', name='Excel Reports', exact=True).click()
    expect(page.get_by_role('heading', name='Workbook preview', exact=True)).to_be_visible(timeout=60000)
    for name in gp.sheetnames:
        page.get_by_role('tab', name=name, exact=True).click()
        check(page)
    page.get_by_role('tab', name='Portfolio Overview', exact=True).click()
    page.wait_for_function("Array.from(document.querySelectorAll('[data-testid=stDataFrame]')).some(e=>e.checkVisibility() && e.getBoundingClientRect().width>600)")
    page.wait_for_timeout(250)  # Allow canvas painting after the hidden tab resizes.
    page.screenshot(path=str(OUT/'excel-preview.png'), full_page=True)
    page.get_by_role('button', name='Portfolio Overview', exact=True).click()
    expect(page.get_by_role('heading', name='Portfolio Overview', exact=True)).to_be_visible(timeout=60000)
    check(page)
    page.set_viewport_size({'width': 390, 'height': 1000})
    # Native Streamlit sidebar is collapsible on narrow screens.
    page.wait_for_timeout(500)  # Native sidebar animates/collapses during resize.
    sidebar = page.locator('[data-testid="stSidebar"]')
    if sidebar.get_attribute('data-collapsed') == 'false':
        page.get_by_role('button', name='Collapse sidebar', exact=True).click()
    expect(sidebar).to_have_attribute('data-collapsed', 'true')
    check(page)
    page.screenshot(path=str(OUT/'overview-mobile.png'), full_page=True)
    results['mobile_no_overflow'] = 'pass'
    assert not results['browser_errors'], results['browser_errors']
    assert not any('openai' in u for u in results['external_requests'])
    (OUT/'browser-results.json').write_text(json.dumps(results, indent=2))
    browser.close()
    print(json.dumps(results, indent=2))
