"""Actual Chrome checks of Data Landscape naming, nav order and preserved download."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/outlook/landscape';OUT.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images/outlook';IMAGES.mkdir(parents=True,exist_ok=True)
receipt={'browser_errors':[],'external_requests':[]}
expected=['Portfolio Overview','Company Detail','Data Landscape','Documents & Reports']
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
    page.on('pageerror',lambda e:receipt['browser_errors'].append(str(e)))
    def local(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',local)
    page.goto('http://127.0.0.1:8502/?page=foundation')
    def ready():
        expect(page.get_by_role('heading',name='Data Landscape',exact=True)).to_be_visible(timeout=60000)
        expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    ready()
    nav=page.locator('.st-key-workspace_navigation button')
    assert nav.all_text_contents()==expected,nav.all_text_contents()
    for heading in ('AI Workflow Readiness','Data Catalog & Dictionary','Data Issues','Structured Data Export'):
        expect(page.get_by_role('heading',name=heading,exact=True)).to_be_visible()
    expect(page.locator('.foundation-intro')).to_have_text('Overview of portfolio data sources, definitions, quality, mapping gaps, and readiness for AI-enabled workflows.')
    expect(page.locator('.foundation-subtitle')).to_have_text('Monthly Portfolio Operating Review')
    assert page.locator('.foundation-kpi-value').all_text_contents()==['76/100','67%','4']
    assert page.locator('.foundation-detail').count()==3
    with page.expect_download() as download:
        page.get_by_role('button',name='↓ Download AI-ready data package',exact=True).click()
    target=OUT/'data-package.zip';download.value.save_as(target)
    expected_hash=json.loads((ROOT/'artifacts/outlook/export-preservation.json').read_text())['data_zip_sha256_unchanged']
    actual_hash=hashlib.sha256(target.read_bytes()).hexdigest();assert actual_hash==expected_hash
    consumer=OUT/'consumer';consumer.mkdir(exist_ok=True)
    with zipfile.ZipFile(target) as z:z.extractall(consumer)
    result=subprocess.run([sys.executable,'-I','-S',str(consumer/'example_consumer.py')],cwd=consumer,env={'PATH':os.defpath},capture_output=True,text=True,check=True,timeout=30)
    comparison=json.loads(result.stdout);assert len(comparison['comparison'])==3
    page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
    page.screenshot(path=str(IMAGES/'data-landscape-desktop.png'),full_page=True)
    receipt.update({'navigation':expected,'foundation_url_preserved':True,'kpis':['76/100','67%','4'],'data_zip_sha256_unchanged':actual_hash,'standalone_consumer_companies':3,'desktop_no_overflow':True})
    page.get_by_role('button',name='Company Detail',exact=True).click()
    expect(page.get_by_role('heading',name='Summit Home Services',exact=True)).to_be_visible(timeout=60000)
    page.get_by_role('button',name='Data Landscape',exact=True).click();ready()
    assert 'page=foundation' in page.url
    page.set_viewport_size({'width':390,'height':1100})
    sidebar=page.locator('[data-testid="stSidebar"]')
    page.wait_for_timeout(400)  # Wait for Streamlit's viewport-driven sidebar transition.
    collapse=page.get_by_role('button',name='Collapse sidebar',exact=True)
    if collapse.is_visible():collapse.click()
    ready()
    page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
    page.screenshot(path=str(IMAGES/'data-landscape-390.png'),full_page=True)
    assert page.locator('.foundation-kpi-value').all_text_contents()==['76/100','67%','4']
    receipt['phone_390_no_overflow']=True
    assert not receipt['browser_errors'] and not receipt['external_requests']
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
