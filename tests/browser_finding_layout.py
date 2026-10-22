"""Actual Chrome memo-row geometry, follow-up/source actions and phone exclusion."""
import json,sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_documents import evidence_locations,original_document,source_books
OUT=ROOT/'artifacts/findings-layout';OUT.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images/findings-layout';IMAGES.mkdir(parents=True,exist_ok=True)
receipt={'desktop':[],'phone':[],'source_targets':[],'errors':[],'external_requests':[]}
companies=load_companies()

def ready(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100})
    page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
    def local(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',local)
    for width in (1440,1280):
        page.set_viewport_size({'width':width,'height':1100})
        for company in companies:
            page.goto('http://127.0.0.1:8502/?page=company&company='+company.id)
            desktop=page.locator('.st-key-desktop_company_detail')
            findings=company.review.package['ai_insights']
            expect(desktop.get_by_role('button',name='View in Source',exact=True)).to_have_count(len(findings),timeout=60000)
            ready(page)
            assert desktop.get_by_text('Management follow-up',exact=True).count()==0
            rows=[desktop.locator('.st-key-finding_panel_'+str(f['id'])).bounding_box() for f in findings]
            for previous,current in zip(rows,rows[1:]):
                assert current['y']>=previous['y']+previous['height']
                assert abs(current['x']-previous['x'])<=1 and abs(current['width']-previous['width'])<=1
            for finding in findings:
                card=desktop.locator('.st-key-finding_panel_'+str(finding['id']))
                analysis=card.locator('.st-key-finding_analysis_'+str(finding['id']))
                actions=card.locator('.st-key-finding_actions_'+str(finding['id']))
                bounds=card.bounding_box();left=analysis.bounding_box();right=actions.bounding_box()
                assert left['x']+left['width']<right['x']
                assert abs(left['y']-right['y'])<=2
                assert 0.65<left['width']/(left['width']+right['width'])<0.75
                expect(analysis.get_by_text(finding['text'],exact=True)).to_be_visible()
                assert actions.get_by_role('button',name='View in Source',exact=True).count()==1
                actions.get_by_text('Follow Up',exact=True).click()
                expect(actions.get_by_text(finding['action'],exact=True)).to_be_visible()
                expect(actions.get_by_text(finding['management_question'],exact=True)).to_be_visible()
                expanded=actions.bounding_box();assert abs(expanded['x']-right['x'])<=1
                ready(page)
                if finding==findings[0]:
                    page.wait_for_timeout(400)  # Native expander height transition.
                    desktop.get_by_role('heading',name='Priority findings',exact=True).evaluate("(e)=>e.scrollIntoView({block:'start'})")
                    page.screenshot(path=str(IMAGES/(company.id+'-'+str(width)+'.png')),full_page=True,animations='disabled')
                actions.get_by_text('Follow Up',exact=True).click()
                if width==1440:
                    targets,_,_=evidence_locations(company,finding['fact_ids']);target=targets[0]
                    actions.get_by_role('button',name='View in Source',exact=True).click()
                    dialog=page.get_by_role('dialog',name='Source inspection',exact=True)
                    expect(dialog.locator('.source-target')).to_have_attribute('data-coordinate',target['cell'],timeout=60000)
                    expect(dialog.get_by_role('textbox',name='Selected cell',exact=True)).to_have_value(target['cell'])
                    expect(dialog.get_by_role('tab',name=target['sheet'],exact=True)).to_have_attribute('aria-selected','true')
                    source,_=source_books(original_document(company));raw=source[target['sheet']][target['cell']].value
                    expect(dialog.locator('.formula-bar')).to_have_text('' if raw is None else str(raw))
                    receipt['source_targets'].append({'company':company.id,'finding':finding['id'],'source_id':target['id'],'sheet':target['sheet'],'cell':target['cell']})
                    page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
            receipt['desktop'].append({'company':company.id,'width':width,'findings':len(findings),'full_width_rows':True,'analysis_actions_70_30':True,'all_followups_expand':True,'no_overflow':True})
            print('desktop PASS',width,company.id,flush=True)
    for width in (390,430):
        page.set_viewport_size({'width':width,'height':1100})
        for company in companies:
            page.goto('http://127.0.0.1:8502/?page=company&company='+company.id)
            mobile=page.locator('.st-key-mobile_company_detail')
            expect(mobile.get_by_role('heading',name='Investment Assessment',exact=True)).to_be_visible(timeout=60000)
            ready(page)
            assert not page.locator('.st-key-desktop_company_detail').is_visible()
            assert page.get_by_role('button',name='View in Source',exact=True).count()==0
            assert page.locator('.source-grid').count()==0
            lead=company.review.package['ai_insights'][0]
            # All original remaining findings remain discoverable in native mobile expanders.
            assert len(mobile.locator('[data-testid="stExpander"]').all())==len(company.review.package['ai_insights'])
            if width==390:
                mobile.get_by_role('heading',name='Investment Assessment',exact=True).evaluate("(e)=>e.scrollIntoView({block:'start'})")
                page.screenshot(path=str(IMAGES/(company.id+'-390.png')),full_page=True,animations='disabled')
            receipt['phone'].append({'company':company.id,'width':width,'original_assessment_retained':True,'no_desktop_source_controls':True,'no_overflow':True})
            print('phone PASS',width,company.id,flush=True)
    assert not receipt['errors'] and not receipt['external_requests']
    browser.close()
(OUT/'browser-results.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
