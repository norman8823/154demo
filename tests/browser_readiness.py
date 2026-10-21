"""Actual Chrome, source inspection and independent package consumer receipt."""
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse
import zipfile
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('COPILOT_READINESS_ARTIFACT_DIR',ROOT/'artifacts/ai-readiness'))
OUT.mkdir(parents=True,exist_ok=True)
receipt={'browser_errors':[],'external_requests':[]}


def check(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    assert page.locator('.katex').count()==0


with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1510,'height':1700},accept_downloads=True)
    page.on('pageerror',lambda e:receipt['browser_errors'].append(str(e)))
    def route_local(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',route_local)
    page.goto('http://127.0.0.1:8502/?page=foundation')
    expect(page.get_by_role('heading',name='AI Workflow Automation Readiness',exact=True)).to_be_visible(timeout=60000)
    for heading in ['Data Mapping','Data Issues','Structured Data Export']:
        expect(page.get_by_role('heading',name=heading,exact=True)).to_be_visible()
    expect(page.get_by_text('67%',exact=True)).to_be_visible()
    expect(page.get_by_text('Not Evaluated',exact=True)).to_be_visible()
    check(page)
    page.wait_for_timeout(450)  # Native dataframe canvas paints after script completion.
    page.screenshot(path=str(OUT/'ai-workflow-readiness-desktop.png'),full_page=True)
    expect(page.get_by_text('Original company input',exact=True)).to_be_visible()
    expect(page.get_by_text('Normalization & transformation',exact=True)).to_be_visible()
    expect(page.get_by_text('GP-standardized output',exact=True)).to_be_visible()
    assert page.locator('.foundation-kpi').count()==3
    # Presentation is scoped: investment pages must lose the foundation styles.
    assert page.locator('.foundation-detail').count()==3
    page.wait_for_timeout(350)
    page.screenshot(path=str(OUT/'ai-workflow-readiness-source-details.png'),full_page=True)
    page.get_by_text('Inspect a mapping and its source evidence',exact=True).click()
    page.get_by_text('Review Required · Branch and consolidated EBITDA schedules do not reconcile · $47,000',exact=True).click()
    expect(page.get_by_text('The unresolved schedule difference is $47,000.',exact=False)).to_be_visible()
    check(page)
    page.wait_for_timeout(350)
    page.screenshot(path=str(OUT/'ai-workflow-readiness-data-issue.png'),full_page=True)
    # Capture the full native expander, including operands below the fold.
    page.locator('[data-testid="stExpander"]').filter(has_text='Branch and consolidated EBITDA schedules do not reconcile').screenshot(path=str(OUT/'ai-workflow-readiness-issue-operands.png'))
    page.get_by_role('button',name='Open original finding & evidence',exact=True).click()
    expect(page.get_by_role('heading',name='Summit Home Services',exact=True)).to_be_visible(timeout=60000)
    check(page)
    assert 'company=summit' in page.url and 'finding=10004' in page.url
    assert page.locator('.foundation-kpis').count()==0
    receipt['source_issue_deep_link']='pass'
    page.get_by_role('button',name='Data Foundation',exact=True).click()
    expect(page.get_by_role('heading',name='AI Workflow Automation Readiness',exact=True)).to_be_visible(timeout=60000)
    with page.expect_download() as d:
        page.get_by_role('button',name='↓ Download AI-ready data package',exact=True).click()
    downloaded=OUT/'AI_Ready_Operating_Data_browser.zip';d.value.save_as(downloaded)
    consumer=OUT/'consumer';consumer.mkdir(exist_ok=True)
    with zipfile.ZipFile(downloaded) as archive:
        assert set(archive.namelist())=={'financial_facts.csv','metric_definitions.json','source_lineage.csv','quality_report.json','example_consumer.py','README.md'}
        archive.extractall(consumer)
    result=subprocess.run([sys.executable,'-I','-S',str(consumer/'example_consumer.py')],cwd=consumer,env={'PATH':os.defpath},capture_output=True,text=True,check=True,timeout=30)
    comparison=json.loads(result.stdout)
    assert len(comparison['comparison'])==3
    (OUT/'independent-consumer.json').write_text(result.stdout)
    receipt['download_and_standalone_consumer']='pass'
    page.set_viewport_size({'width':390,'height':1200})
    sidebar=page.locator('[data-testid="stSidebar"]')
    page.wait_for_timeout(350)
    if sidebar.get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
    page.wait_for_timeout(350)
    page.locator('.st-key-foundation_page').evaluate('(e)=>{for(let p=e.parentElement;p;p=p.parentElement)p.scrollTop=0;}')
    check(page)
    assert page.get_by_role('heading',name='AI Workflow Automation Readiness',exact=True).bounding_box()['y']>=60
    page.screenshot(path=str(OUT/'ai-workflow-readiness-mobile.png'),full_page=True)
    receipt['mobile_no_document_overflow']='pass'
    assert receipt['browser_errors']==[]
    assert receipt['external_requests']==[]
    (OUT/'browser-readiness.json').write_text(json.dumps(receipt,indent=2))
    browser.close()
    print(json.dumps(receipt,indent=2))
