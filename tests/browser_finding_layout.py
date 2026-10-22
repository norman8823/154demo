"""Actual Chrome compact finding cards, original source targets and phone view."""
import json,sys,hashlib
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_documents import evidence_locations,original_document
OUT=ROOT/'artifacts/compact-findings';OUT.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images/compact-findings';IMAGES.mkdir(parents=True,exist_ok=True)
receipt={'desktop':[],'phone':[],'source_targets':[],'original_downloads':[],'errors':[],'external_requests':[]}

def ready(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
    page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
    def local(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',local)
    for index,company in enumerate(load_companies()):
        if index:
            # Independent direct-link sessions keep prior dialog dismissal events
            # from racing the next company's initial widget hydration.
            page.close()
            page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
            page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
            page.route('**/*',local)
        page.goto('http://127.0.0.1:8502/?page=company&company='+company.id)
        expect(page.locator('.st-key-desktop_company_detail .investment-company-name')).to_have_text(company.name,timeout=60000)
        expect(page.get_by_role('combobox',name='Company',exact=True)).to_have_value(company.name)
        desktop=page.locator('.st-key-desktop_company_detail');findings=company.review.package['ai_insights']
        expect(desktop.get_by_role('button',name='View in Source',exact=True)).to_have_count(len(findings),timeout=60000);ready(page)
        for i,f in enumerate(findings):
            card=desktop.locator('.st-key-finding_panel_'+str(f['id']))
            assert card.locator('.st-key-finding_analysis_'+str(f['id'])).count()==(1 if i==0 else 0)
            if i:expect(card.get_by_text(f['conclusion'],exact=True)).to_be_visible()
        desktop.get_by_role('heading',name='Priority findings',exact=True).evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})")
        page.screenshot(path=str(IMAGES/(company.id+'-desktop.png')),full_page=True,animations='disabled')
        for i,f in enumerate(findings):
            card=desktop.locator('.st-key-finding_panel_'+str(f['id']))
            toolbar=card.locator('.st-key-finding_actions_'+str(f['id']))
            buttons=[toolbar.get_by_role('button',name=label,exact=True) for label in ('Read Full Analysis','Follow Up','View in Source')]
            boxes=[b.bounding_box() for b in buttons]
            assert max(b['y'] for b in boxes)-min(b['y'] for b in boxes)<=2,boxes
            assert all(a['x']+a['width']<=b['x'] for a,b in zip(boxes,boxes[1:]))
            assert boxes[-1]['x']+boxes[-1]['width']-boxes[0]['x']<650
            if i:buttons[0].click()
            body=card.locator('.st-key-finding_analysis_'+str(f['id']))
            expect(body.get_by_text(f['text'],exact=True)).to_be_visible(timeout=60000);ready(page)
            assert body.bounding_box()['y']+body.bounding_box()['height']<=toolbar.bounding_box()['y']+1
            buttons[0].click()
            expect(card.get_by_text(f['conclusion'],exact=True)).to_be_visible(timeout=60000)
            buttons[1].click();followup=card.locator('.st-key-finding_followup_'+str(f['id']))
            expect(followup.get_by_text(f['action'],exact=True)).to_be_visible(timeout=60000)
            expect(followup.get_by_text(f['management_question'],exact=True)).to_be_visible()
            assert followup.bounding_box()['y']>=toolbar.bounding_box()['y']+toolbar.bounding_box()['height']
            buttons[1].click();expect(followup).to_have_count(0,timeout=60000);ready(page)
            target=evidence_locations(company,f['fact_ids'])[0][0]
            buttons[2].click();dialog=page.get_by_role('dialog',name='Source inspection',exact=True)
            expect(dialog.get_by_role('textbox',name='Selected cell',exact=True)).to_have_value(target['cell'],timeout=60000)
            expect(dialog.get_by_role('tab',name=target['sheet'],exact=True)).to_have_attribute('aria-selected','true')
            receipt['source_targets'].append({'company':company.id,'finding':f['id'],'sheet':target['sheet'],'cell':target['cell']})
            page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0);ready(page)
            if card.get_by_text('Evidence details',exact=True).count():
                notice=card.get_by_text('supporting records have no supported single-cell location',exact=False)
                expect(notice).not_to_be_visible()
                card.get_by_text('Evidence details',exact=True).click();expect(notice).to_be_visible()
                card.get_by_text('Evidence details',exact=True).click()
        receipt['desktop'].append({'company':company.id,'first_default_expanded':True,'others_default_collapsed':True,'original_text_takeaway_actions':True,'toolbar_horizontal_beneath_content':True,'optional_evidence_details':True,'no_overflow':True})
        print('desktop PASS',company.id,flush=True)
    page.goto('http://127.0.0.1:8502/?page=excel')
    expect(page.get_by_role('heading',name='Source Documents',level=1,exact=True)).to_be_visible(timeout=60000)
    expect(page.get_by_role('button',name='Preview',exact=True)).to_have_count(3,timeout=60000);ready(page)
    assert page.get_by_role('heading',name='Generated Reports',exact=True).count()==0
    assert page.get_by_role('button',name='Download Excel',exact=True).count()==0
    assert page.get_by_role('combobox',name='Company report',exact=True).count()==0
    assert page.locator('.st-key-workspace_navigation button').all_text_contents()==['Portfolio Overview','Investment Detail','Data Landscape','Source Documents']
    for c in load_companies():
        with page.expect_download() as d:page.locator('.st-key-source_document_'+c.id).get_by_role('button',name='Download Original',exact=True).click()
        path=OUT/(c.id+'-original.xlsx');d.value.save_as(path)
        assert path.read_bytes()==original_document(c).data
        receipt['original_downloads'].append({'company':c.id,'byte_identical':True,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    page.screenshot(path=str(IMAGES/'source-documents-desktop.png'),full_page=True,animations='disabled')
    for width in (390,430):
        page.set_viewport_size({'width':width,'height':1100})
        for c in load_companies():
            page.goto('http://127.0.0.1:8502/?page=company&company='+c.id)
            mobile=page.locator('.st-key-mobile_company_detail')
            expect(mobile.get_by_role('heading',name='Investment Assessment',exact=True)).to_be_visible(timeout=60000);ready(page)
            assert not page.locator('.st-key-desktop_company_detail').is_visible()
            assert page.get_by_role('button',name='View in Source',exact=True).count()==0
            assert page.get_by_role('button',name='Download Excel',exact=True).count()==0
            assert page.get_by_role('button',name='Read Full Analysis',exact=True).count()==0
            if width==390:
                mobile.get_by_role('heading',name='Investment Assessment',exact=True).evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})")
                page.screenshot(path=str(IMAGES/(c.id+'-390.png')),full_page=True,animations='disabled')
            receipt['phone'].append({'company':c.id,'width':width,'simplified_original_assessment':True,'desktop_actions_hidden':True,'no_overflow':True})
        page.goto('http://127.0.0.1:8502/?page=excel')
        expect(page.get_by_role('heading',name='Source Documents',level=1,exact=True)).to_be_visible(timeout=60000);ready(page)
        expect(page.get_by_role('button',name='Download Original',exact=True)).to_have_count(3)
        assert page.get_by_role('button',name='Preview',exact=True).count()==0
        assert page.get_by_role('button',name='Download Excel',exact=True).count()==0
        if width==390:page.screenshot(path=str(IMAGES/'source-documents-390.png'),full_page=True,animations='disabled')
    assert not receipt['errors'] and not receipt['external_requests']
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
