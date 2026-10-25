"""Actual Chrome proof for the bounded final refinement and its test fixture."""
import json,base64,re,sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/product-refinement/browser';OUT.mkdir(parents=True,exist_ok=True)
receipt={'screens':[],'errors':[],'external_requests':[]}

def settle(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    page.wait_for_timeout(200)

def audit(page):
    settle(page)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    traps=page.evaluate('''()=>[...document.querySelectorAll('*')].filter(e=>{let s=getComputedStyle(e),r=e.getBoundingClientRect();return r.width>0&&r.height>40&&e.scrollHeight>e.clientHeight+3&&/auto|scroll/.test(s.overflowY)&&!['stMain','stAppViewContainer','stApp','stSidebar','stSidebarContent','stSidebarUserContent'].includes(e.dataset.testid)&&!['HTML','BODY'].includes(e.tagName)&&!e.closest('[data-testid="stSidebar"]');}).map(e=>({tag:e.tagName,cls:e.className}))''')
    assert not traps,traps
    assert page.locator('.katex').count()==0

def shot(page,name):
    audit(page);page.screenshot(path=str(OUT/(name+'.png')),full_page=True);receipt['screens'].append(name)

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1200},accept_downloads=True,permissions=['clipboard-read','clipboard-write'])
    page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
    def local(route):
        if urlparse(route.request.url).hostname not in ['127.0.0.1','localhost']:
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',local)
    for width in (() if '--fixture-only' in sys.argv else (1440,390)):
        page.set_viewport_size({'width':width,'height':1200})
        for route in ('overview','foundation'):
            print('Checking',width,route,flush=True)
            page.goto('http://127.0.0.1:8502/?page='+route);settle(page)
            if width==390 and page.locator('[data-testid="stSidebar"]').get_attribute('data-collapsed')=='false':
                page.get_by_role('button',name='Collapse sidebar',exact=True).click();page.wait_for_timeout(250)
            assert page.title()=='Portfolio Reporting Copilot | NL Intelligence'
            assert page.get_by_role('combobox',name='Open company',exact=True).count()==0
            if route=='overview':
                expect(page.locator('.v3-card-returns')).to_have_count(3)
                expect(page.get_by_text('Illustrative investment values and valuation context',exact=True)).to_have_count(0)
                expect(page.locator('.gp-holdings')).to_have_count(0)
                for s,moic,irr in [('summit','2.50x','21.77%'),('tallis','0.71x','-9.54%'),('harrow','1.68x','13.80%')]:
                    text=page.locator('.st-key-gp_company_'+s).inner_text();assert moic in text and irr in text
                if width==1440:
                    rects=page.locator('.st-key-operating_cards [class*="st-key-gp_company_"]').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().top)')
                    assert max(rects)-min(rects)<3
                shot(page,f'overview-{width}')
                page.locator('.st-key-operating_cards').screenshot(path=str(OUT/f'holdings-cards-{width}.png'))
                page.locator('.st-key-open_tallis button').click();settle(page)
                expect(page.get_by_role('heading',name='Tallis Brook Accounting',exact=True)).to_be_visible()
                expect(page.get_by_role('combobox',name='Company',exact=True)).to_be_visible()
            else:
                expect(page.get_by_text('76/100',exact=True)).to_be_visible()
                expect(page.get_by_text('67%',exact=True)).to_be_visible()
                expect(page.get_by_role('heading',name='Data Catalog & Dictionary',exact=True)).to_be_visible()
                assert page.locator('.foundation-detail').count()==3
                shot(page,f'foundation-{width}')
                page.locator('.foundation-detail-grid').screenshot(path=str(OUT/f'catalog-detail-{width}.png'))
                page.get_by_role('combobox',name='Data element',exact=True).fill('Reported EBITDA')
                page.get_by_role('combobox',name='Data element',exact=True).press('ArrowDown')
                page.get_by_role('option',name='Reported EBITDA · 34 observations',exact=True).click();settle(page)
                page.get_by_role('combobox',name='Company',exact=True).click()
                page.get_by_role('option',name='Harrow Ridge Environmental',exact=True).click();settle(page)
                page.get_by_role('combobox',name='Scenario',exact=True).click()
                page.get_by_role('option',name='budget',exact=True).click();settle(page)
                expect(page.get_by_text('$10,895,000',exact=True)).to_be_visible()
                assert "'P&L Summary'!G34" in page.get_by_role('combobox',name='Mapping source',exact=True).input_value()
                audit(page)
        if width==390:
            page.get_by_role('button',name='Expand sidebar',exact=True).click()
            expect(page.get_by_role('button',name='Portfolio Overview',exact=True)).to_be_visible()
            assert not page.locator('.st-key-mobile_access').is_visible()
            receipt['mobile_navigation']='pass'
    if '--main-only' in sys.argv:
        assert not receipt['errors'] and not receipt['external_requests']
        (OUT/'main-receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2));browser.close();sys.exit(0)
    # Separate, test-only fixture: production portfolio remains exactly3 companies.
    page.set_viewport_size({'width':1440,'height':1200})
    print('Checking fixture / QR',flush=True)
    page.goto('http://127.0.0.1:8503');settle(page)
    assert page.locator('.holdings-row').count()==12
    expect(page.locator('.st-key-open_fixture-01 button')).to_be_visible()
    expect(page.locator('.st-key-open_fixture-02 button')).to_be_visible()
    assert page.get_by_role('checkbox',name='Select Fixture 03 · Harrow Ridge Environmental',exact=True).is_disabled()
    page.locator('.st-key-holding_select_fixture-01 label').click();expect(page.locator('.st-key-open_fixture-01')).to_have_count(0);settle(page)
    page.locator('.st-key-holding_select_fixture-03 label').click();settle(page)
    assert page.locator('.st-key-open_fixture-01').count()==0
    expect(page.locator('.st-key-open_fixture-03 button')).to_be_visible()
    shot(page,'twelve-holdings-1440')
    page.get_by_role('button',name='Clear selection',exact=True).click();settle(page)
    expect(page.locator('.v3-card-returns')).to_have_count(0)
    page.locator('.st-key-holding_select_fixture-12 label').click();expect(page.locator('.st-key-open_fixture-12')).to_have_count(1);settle(page)
    page.set_viewport_size({'width':390,'height':1200})
    if page.locator('[data-testid="stSidebar"]').get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
    shot(page,'twelve-holdings-390')
    page.locator('.st-key-open_fixture-12 button').click();settle(page)
    assert 'company=fixture-12' in page.url
    receipt['twelve_holdings_selection']='default2 / limit2 / replace / clear / select12 / navigate: pass'
    # QRs are generated for an explicitly configured fixture URL; no remote request.
    page.set_viewport_size({'width':1440,'height':1200})
    print('Checking fixture / QR',flush=True)
    page.goto('http://127.0.0.1:8503');settle(page)
    button=page.get_by_role('button',name='View on Mobile',exact=True)
    expect(button).to_be_visible()
    style=button.evaluate('(e)=>getComputedStyle(e).backgroundImage')
    (OUT/'qr-compact.png').write_bytes(base64.b64decode(re.search('base64,([^"\\)]+)',style).group(1)))
    button.click()
    dialog=page.get_by_role('dialog');expect(dialog).to_be_visible()
    expect(dialog.get_by_role('heading',name='View on Mobile',exact=True)).to_be_visible()
    image=dialog.locator('img');expect(image).to_be_visible()
    (OUT/'qr-large.png').write_bytes(image.screenshot())
    expect(dialog.get_by_text('https://demo.example.com/?page=foundation',exact=True)).to_be_visible()
    # Streamlit's native code-block copy action is credential/network-free.
    dialog.locator('[data-testid="stCode"]').hover()
    copy=dialog.get_by_role('button',name='Copy to clipboard',exact=True)
    copy.click();page.wait_for_timeout(200)
    assert page.evaluate('navigator.clipboard.readText()')=='https://demo.example.com/?page=foundation'
    page.screenshot(path=str(OUT/'mobile-qr-dialog.png'))
    page.keyboard.press('Escape');expect(dialog).not_to_be_visible()
    button.click();expect(dialog).to_be_visible()
    dialog.get_by_role('button',name='Close',exact=True).click();expect(dialog).not_to_be_visible()
    receipt['qr_modal_and_copy']='both open targets share native button; native Copy Link/clipboard exact; Escape/Close pass'
    assert not receipt['errors'] and not receipt['external_requests']
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
    browser.close()
