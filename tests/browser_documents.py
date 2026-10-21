"""Actual Chrome proof: approved originals, authentic highlighted cells and citations."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/source-documents';OUT.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images/source-documents';IMAGES.mkdir(parents=True,exist_ok=True)
MANIFEST=json.loads((ROOT/'demo_results/manifest.json').read_text())
receipt={'originals':{},'citations':[],'errors':[],'external_requests':[]}
TARGETS=[('summit','Summit Home Services','Income Statement','D15','3,298'),('tallis','Tallis Brook Accounting','Practice P&L','G12','$3,475,418'),('harrow','Harrow Ridge Environmental','P&L Summary','F13','46,650')]


def ready(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)


def close(page):
    page.get_by_role('dialog').get_by_role('button',name='Close',exact=True).last.click()
    expect(page.get_by_role('dialog')).to_have_count(0,timeout=60000)


def highlighted(page,sheet,cell,value):
    dialog=page.get_by_role('dialog')
    expect(dialog.get_by_role('combobox',name='Worksheet',exact=True)).to_be_visible(timeout=60000)
    expect(dialog.locator('.source-target')).to_have_attribute('data-coordinate',cell,timeout=60000)
    expect(dialog.locator('.source-target')).to_have_text(value)
    expect(dialog.get_by_text(sheet+' · '+cell,exact=True)).to_be_visible()
    assert dialog.locator('.source-grid tbody tr').count()<=12
    assert dialog.locator('.source-grid').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')


with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1400},accept_downloads=True)
    page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
    def local(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',local)
    page.goto('http://127.0.0.1:8502/?page=excel')
    expect(page.get_by_role('heading',name='Source Documents',exact=True)).to_be_visible(timeout=60000)
    ready(page)
    expect(page.get_by_role('heading',name='Workbook preview',exact=True)).to_have_count(0)
    page.screenshot(path=str(IMAGES/'documents-library-desktop.png'),full_page=True)
    for slug,company,sheet,cell,value in TARGETS:
        card=page.locator('.st-key-source_document_'+slug)
        entry=next(r for r in MANIFEST['runs'] if r['run']==slug+('-17-final' if slug=='harrow' else '-05-final'))
        with page.expect_download() as download:card.get_by_role('button',name='Download Original',exact=True).click()
        path=OUT/(slug+'-original.xlsx');download.value.save_as(path)
        assert download.value.suggested_filename==Path(entry['workbook']).name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['workbook_sha256']
        print('original downloaded',slug,flush=True)
        card.get_by_role('button',name='Preview',exact=True).click()
        dialog=page.get_by_role('dialog')
        expect(dialog.get_by_role('heading',name=company,exact=True)).to_be_visible(timeout=60000)
        dialog.get_by_role('combobox',name='Worksheet',exact=True).click()
        page.get_by_role('option',name=sheet,exact=True).click()
        expect(dialog.get_by_text(sheet+' · A1:',exact=False)).to_be_visible(timeout=60000)
        expect(dialog.get_by_role('textbox',name='Inspect cell',exact=True)).to_have_value('A1',timeout=60000)
        dialog.get_by_role('textbox',name='Inspect cell',exact=True).fill(cell)
        dialog.get_by_role('textbox',name='Inspect cell',exact=True).press('Enter')
        highlighted(page,sheet,cell,value)
        print('highlighted',slug,flush=True)
        dialog.get_by_text('Original formula text',exact=True).click()
        expect(dialog.locator('code')).to_contain_text('=SUM(')
        expect(dialog.locator('code')).to_be_visible()
        page.wait_for_timeout(250)
        page.screenshot(path=str(IMAGES/(slug+'-highlighted-source-desktop.png')),full_page=True)
        # An invalid coordinate cannot leave a stale, valid target visible.
        dialog.get_by_role('textbox',name='Inspect cell',exact=True).fill('XFD999999')
        dialog.get_by_role('textbox',name='Inspect cell',exact=True).press('Enter')
        expect(dialog.get_by_text('Source preview unavailable:',exact=False)).to_be_visible(timeout=60000)
        expect(dialog.locator('.source-target')).to_have_count(0)
        close(page)
        receipt['originals'][slug]={'sha256':entry['workbook_sha256'],'filename':download.value.suggested_filename,'highlight':sheet+'!'+cell,'invalid_reference':'fails safely'}
    # Mapping -> exact original workbook and cell, one click.
    page.goto('http://127.0.0.1:8502/?page=foundation')
    expect(page.locator('.st-key-foundation_source_view button')).to_be_visible(timeout=60000)
    for slug,company,sheet,cell,value in TARGETS:
        page.get_by_role('combobox',name='Company',exact=True).click()
        page.get_by_role('option',name=company,exact=True).click()
        expect(page.locator('.foundation-detail-grid')).to_contain_text(sheet,timeout=60000)
        print('mapping selected',slug,flush=True)
        page.locator('.st-key-foundation_source_view button').click()
        highlighted(page,sheet,cell,value)
        if slug=='summit':
            dialog=page.get_by_role('dialog')
            dialog.get_by_role('textbox',name='Inspect cell',exact=True).fill('D16')
            dialog.get_by_role('textbox',name='Inspect cell',exact=True).press('Enter')
            expect(dialog.locator('.source-target')).to_have_attribute('data-coordinate','D16')
            page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
            page.locator('.st-key-foundation_source_view button').click()
            highlighted(page,sheet,cell,value)
            receipt['reopened_citation_reset']='D16 inspection -> Escape -> original D15 citation'
        close(page)
        receipt['citations'].append({'route':'foundation','company':slug,'target':sheet+'!'+cell})
    # Exact finding -> recorded source operand, with derived definitions retained.
    for route,key in [('issues','issue_source_summit_'),('company&company=summit&finding=10000','company_source_summit_')]:
        page.goto('http://127.0.0.1:8502/?page='+route)
        button=page.locator('[class*="st-key-'+key+'"][class*="_view"] button').first
        expect(button).to_be_visible(timeout=60000)
        select=page.locator('[class*="st-key-'+key+'"][class*="_operand"]') .first
        selected=select.get_by_role('combobox',name='Original source cell',exact=True).input_value()
        button.click()
        dialog=page.get_by_role('dialog')
        expect(dialog.locator('.source-target')).to_have_count(1,timeout=60000)
        actual=dialog.get_by_role('textbox',name='Inspect cell',exact=True).input_value()
        sheetname=dialog.get_by_role('combobox',name='Worksheet',exact=True).input_value()
        assert actual in selected and sheetname in selected,(actual,sheetname,selected)
        if route=='issues':page.screenshot(path=str(IMAGES/'finding-original-operand-desktop.png'),full_page=True)
        close(page)
        receipt['citations'].append({'route':route,'target':sheetname+'!'+actual,'matches_recorded_operand':True})
    page.set_viewport_size({'width':390,'height':1000})
    page.goto('http://127.0.0.1:8502/?page=excel')
    expect(page.get_by_role('heading',name='Source Documents',exact=True)).to_be_visible(timeout=60000)
    sidebar=page.locator('[data-testid="stSidebar"]')
    if sidebar.get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
    ready(page)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    page.screenshot(path=str(IMAGES/'documents-library-mobile.png'),full_page=True)
    page.locator('.st-key-preview_summit button').click()
    dialog=page.get_by_role('dialog')
    dialog.get_by_role('combobox',name='Worksheet',exact=True).click()
    page.get_by_role('option',name='Income Statement',exact=True).click()
    expect(dialog.get_by_text('Income Statement · A1:',exact=False)).to_be_visible(timeout=60000)
    dialog.get_by_role('textbox',name='Inspect cell',exact=True).fill('D15')
    dialog.get_by_role('textbox',name='Inspect cell',exact=True).press('Enter')
    highlighted(page,'Income Statement','D15','3,298')
    page.screenshot(path=str(IMAGES/'source-dialog-mobile-controls.png'),full_page=True)
    dialog.locator('.source-target').scroll_into_view_if_needed()
    page.screenshot(path=str(IMAGES/'summit-highlighted-source-mobile.png'),full_page=True)
    page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
    assert not receipt['errors'] and not receipt['external_requests'],receipt
    (OUT/'browser-documents.json').write_text(json.dumps(receipt,indent=2))
    browser.close();print(json.dumps(receipt,indent=2))
