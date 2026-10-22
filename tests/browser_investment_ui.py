"""Actual Chrome naming, bottom report actions, shared styling and mobile checks."""
import json,sys,hashlib
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_documents import evidence_locations
OUT=ROOT/'artifacts/investment-ui';IMAGES=ROOT/'docs/images/investment-ui';IMAGES.mkdir(parents=True,exist_ok=True)
receipt={'desktop':[],'phone':[],'styles':[],'source_targets':[],'errors':[],'external_requests':[]}

def ready(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')

def style(button):
    return button.evaluate("e=>{const s=getComputedStyle(e);return {height:s.minHeight,radius:s.borderRadius,background:s.backgroundColor,color:s.color,padding:s.padding,fontWeight:s.fontWeight};}")

def capture(page,name):
    page.screenshot(path=str(IMAGES/(name+'.png')),full_page=True,animations='disabled')

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
    page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
    def local(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',local)
    page.goto('http://127.0.0.1:8502/')
    portfolio=page.get_by_role('button',name='Download Excel',exact=True)
    expect(portfolio).to_have_count(1,timeout=60000);ready(page)
    assert page.locator('.st-key-workspace_navigation button').all_text_contents()==['Portfolio Overview','Investment Detail','Data Landscape','Source Documents']
    assert portfolio.bounding_box()['y']>page.locator('.st-key-operating_cards').bounding_box()['y']+page.locator('.st-key-operating_cards').bounding_box()['height']
    receipt['styles'].append(style(portfolio));capture(page,'overview-top')
    portfolio.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");capture(page,'overview-download')
    receipt['desktop'].append({'page':'overview','single_bottom_excel_action':True})
    for company in load_companies():
        page.goto('http://127.0.0.1:8502/?page=company&company='+company.id+'&finding=10000')
        desktop=page.locator('.st-key-desktop_company_detail')
        expect(desktop.get_by_role('heading',name='Investment Detail',exact=True,level=1)).to_be_visible(timeout=60000)
        expect(desktop.locator('.investment-company-name')).to_have_text(company.name)
        expect(page.locator('.gp-breadcrumb')).to_contain_text('Portfolio / Investment Detail')
        expect(page.get_by_role('combobox',name='Company',exact=True)).to_have_value(company.name)
        assert 'page=company' in page.url and 'company='+company.id in page.url
        expect(desktop.get_by_role('button',name='View in Source',exact=True)).to_have_count(len(company.review.package['ai_insights']),timeout=60000)
        ready(page);capture(page,company.id+'-detail')
        download=desktop.get_by_role('button',name='Download Excel',exact=True)
        expect(download).to_have_count(1)
        last=desktop.locator('.st-key-finding_panel_'+str(company.review.package['ai_insights'][-1]['id']))
        assert download.bounding_box()['y']>=last.bounding_box()['y']+last.bounding_box()['height']
        receipt['styles'].append(style(download))
        first=desktop.locator('.st-key-finding_panel_10000');actions=first.locator('.st-key-finding_actions_10000')
        actions.get_by_text('Follow Up',exact=True).click()
        expect(first.get_by_text(company.review.package['ai_insights'][0]['action'],exact=True)).to_be_visible()
        actions.get_by_text('Follow Up',exact=True).click()
        target=evidence_locations(company,company.review.package['ai_insights'][0]['fact_ids'])[0][0]
        actions.get_by_role('button',name='View in Source',exact=True).click()
        dialog=page.get_by_role('dialog',name='Source inspection',exact=True)
        expect(dialog.get_by_role('textbox',name='Selected cell',exact=True)).to_have_value(target['cell'],timeout=60000)
        expect(dialog.get_by_role('tab',name=target['sheet'],exact=True)).to_have_attribute('aria-selected','true')
        receipt['source_targets'].append({'company':company.id,'sheet':target['sheet'],'cell':target['cell']})
        page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
        download.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})");capture(page,company.id+'-download')
        receipt['desktop'].append({'page':'investment','company':company.id,'h1_and_company_heading':True,'bottom_download':True,'followup_and_source':True})
    page.goto('http://127.0.0.1:8502/?page=excel')
    expect(page.get_by_role('heading',name='Source Documents',exact=True)).to_be_visible(timeout=60000);ready(page)
    for company in load_companies():
        row=page.locator('.st-key-source_document_'+company.id)
        expect(row.get_by_role('button',name='Download Original',exact=True)).to_be_visible()
        expect(row.get_by_role('button',name='Preview',exact=True)).to_be_visible()
    assert page.get_by_role('button',name='Download Excel',exact=True).count()==0
    assert page.get_by_role('combobox',name='Company report',exact=True).count()==0
    capture(page,'documents-reports')
    receipt['desktop'].append({'page':'documents','original_actions_beside_sources':True,'source_library_only':True})
    assert len({json.dumps(s,sort_keys=True) for s in receipt['styles']})==1,receipt['styles']
    assert receipt['styles'][0]['background']=='rgb(37, 59, 88)'
    for width in (390,430):
        page.set_viewport_size({'width':width,'height':1100})
        for route,slug in [('overview',None),('company','summit'),('company','tallis'),('company','harrow'),('excel',None)]:
            url='http://127.0.0.1:8502/?page='+route+('&company='+slug if slug else '')
            page.goto(url)
            heading={'overview':'Portfolio Overview','company':'Investment Detail','excel':'Source Documents'}[route]
            expect(page.get_by_role('heading',name=heading,level=1,exact=True)).to_be_visible(timeout=60000);ready(page)
            assert page.get_by_role('button',name='Download Excel',exact=True).count()==0
            if route=='company':
                mobile=page.locator('.st-key-mobile_company_detail')
                expect(mobile.locator('.investment-company-name')).to_have_text(next(c.name for c in load_companies() if c.id==slug))
                assert page.get_by_role('button',name='View in Source',exact=True).count()==0
                assert page.get_by_role('combobox',name='Company Excel format',exact=True).count()==0
            if width==390:capture(page,(slug or route)+'-390')
            receipt['phone'].append({'page':route,'company':slug,'width':width,'generated_controls_hidden':True,'no_overflow':True})
    assert not receipt['errors'] and not receipt['external_requests']
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
