"""Actual Chrome business outlooks and fully visible approved findings."""
import json,sys,hashlib
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_documents import evidence_locations,original_document
from portfolio_outlook import investment_outlook,SECTIONS
from card_presentation import card_metric
from executive import present
OUT=ROOT/'artifacts/business-outlook';OUT.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images/business-outlook';IMAGES.mkdir(parents=True,exist_ok=True)
receipt={'desktop':[],'phone':[],'source_targets':[],'errors':[],'external_requests':[]}

def ready(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    def fresh(width=1440):
        page=browser.new_page(viewport={'width':width,'height':1200})
        page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
        def local(route):
            if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
                receipt['external_requests'].append(route.request.url);route.abort()
            else:route.continue_()
        page.route('**/*',local)
        return page
    for company in load_companies():
        page=fresh();page.goto('http://127.0.0.1:8502/?page=company&company='+company.id)
        desktop=page.locator('.st-key-desktop_company_detail');outlook=desktop.locator('.investment-outlook')
        expect(outlook).to_have_attribute('data-company',company.id,timeout=60000)
        expect(outlook).to_have_attribute('data-compact','false')
        expected=investment_outlook(company)
        for (heading,basis),paragraph in zip(SECTIONS,expected.paragraphs):
            expect(outlook.get_by_role('heading',name=heading,exact=True)).to_be_visible()
            expect(outlook.get_by_text(paragraph,exact=True)).to_be_visible()
            expect(outlook.get_by_text(basis,exact=True)).to_be_visible()
        findings=company.review.package['ai_insights']
        expect(desktop.get_by_role('button',name='View in Source',exact=True)).to_have_count(len(findings),timeout=60000);ready(page)
        page.screenshot(path=str(IMAGES/(company.id+'-outlook.png')),full_page=True,animations='disabled')
        summary=present(company.review);cards={c['id']:c for c in summary['cards']+summary.get('secondary',[])}
        previous=None
        for f in findings:
            card=desktop.locator('.st-key-finding_panel_'+str(f['id']))
            for field in ('text','action','management_question'):
                expect(card.get_by_text(f[field],exact=True)).to_be_visible()
            assert card.get_by_role('button').all_text_contents()==['View in Source']
            assert card.locator('[data-testid="stExpander"]').count()==0
            expect(card.get_by_text('Follow Up',exact=True)).to_be_visible()
            title=card.get_by_role('heading',name=f['title'],exact=True).bounding_box()
            impact,_=card_metric(cards[f['id']],company.review)
            if impact:
                box=card.locator('.finding-impact').bounding_box()
                assert 0<=box['x']-title['x']-title['width']<=18
            target=evidence_locations(company,f['fact_ids'])[0][0]
            card.get_by_role('button',name='View in Source',exact=True).click()
            dialog=page.get_by_role('dialog',name='Source inspection',exact=True)
            expect(dialog.get_by_role('textbox',name='Selected cell',exact=True)).to_have_value(target['cell'],timeout=60000)
            expect(dialog.get_by_role('tab',name=target['sheet'],exact=True)).to_have_attribute('aria-selected','true')
            receipt['source_targets'].append({'company':company.id,'finding':f['id'],'sheet':target['sheet'],'cell':target['cell']})
            page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0);ready(page)
        desktop.get_by_role('heading',name='Priority findings',exact=True).evaluate("e=>e.scrollIntoView({block:'start',behavior:'instant'})")
        page.screenshot(path=str(IMAGES/(company.id+'-findings.png')),full_page=True,animations='disabled')
        receipt['desktop'].append({'company':company.id,'four_business_sections':True,'illustrative_vs_reported_labels':True,'all_original_text_action_questions_visible':True,'only_source_action':True,'impact_near_title':True,'no_overflow':True})
        page.close();print('desktop PASS',company.id,flush=True)
    for width in (390,430):
        for company in load_companies():
            page=fresh(width);page.goto('http://127.0.0.1:8502/?page=company&company='+company.id)
            mobile=page.locator('.st-key-mobile_company_detail');outlook=mobile.locator('.investment-outlook')
            expect(outlook).to_have_attribute('data-company',company.id,timeout=60000)
            expect(outlook).to_have_attribute('data-compact','true')
            assert outlook.locator('.outlook-section').count()==1
            expect(outlook.get_by_text(investment_outlook(company).paragraphs[0],exact=True)).to_be_visible()
            expect(mobile.get_by_role('heading',name='Investment Assessment',exact=True)).to_be_visible()
            ready(page)
            assert not page.locator('.st-key-desktop_company_detail').is_visible()
            assert page.get_by_role('button',name='View in Source',exact=True).count()==0
            assert page.get_by_role('button',name='Download Excel',exact=True).count()==0
            if width==390:page.screenshot(path=str(IMAGES/(company.id+'-390.png')),full_page=True,animations='disabled')
            receipt['phone'].append({'company':company.id,'width':width,'one_business_context_section':True,'original_prepared_assessment_retained':True,'no_repeated_full_outlook':True,'no_overflow':True})
            page.close()
    assert not receipt['errors'] and not receipt['external_requests']
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
