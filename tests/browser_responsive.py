"""Actual Chrome viewport and scroll-surface audit for the existing local app."""
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/mobile-investment-detail/responsive';OUT.mkdir(parents=True,exist_ok=True)
ROUTES={'overview':'overview','foundation':'foundation','issues':'issues','summit':'company&company=summit','tallis':'company&company=tallis','harrow':'company&company=harrow','excel':'excel'}
receipt={'viewports':[],'external_requests':[],'errors':[]}


def settle(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    page.wait_for_timeout(150)


def audit(page,label,width):
    settle(page)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),label
    assert page.locator('[data-testid="stDataFrame"]').count()==0,label
    traps=page.evaluate('''() => [...document.querySelectorAll('*')].filter(e=>{
      const s=getComputedStyle(e),r=e.getBoundingClientRect();
      return r.width>0 && r.height>40 && e.scrollHeight>e.clientHeight+3 && /auto|scroll/.test(s.overflowY)
        && !['stMain','stAppViewContainer','stApp','stSidebar','stSidebarContent','stSidebarUserContent'].includes(e.dataset.testid)
        && !['HTML','BODY'].includes(e.tagName) && !e.closest('[data-testid="stSidebar"]');
    }).map(e=>({tag:e.tagName,test:e.dataset.testid,cls:e.className,height:e.clientHeight,content:e.scrollHeight}))''')
    assert not traps,(label,width,traps)
    over=page.locator('.gp-table-wrap').evaluate_all('(es)=>es.filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>({width:e.clientWidth,content:e.scrollWidth}))')
    assert not over,(label,width,over)
    assert page.locator('.katex').count()==0,(label,'Currency rendered as math')
    if label=='overview':
        expect(page.locator('.gp-holdings')).to_have_count(0)
        expect(page.locator('.v3-card-returns')).to_have_count(3)
        if width>=1280:
            rects=page.locator('[class*="st-key-gp_company_"]').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect()).map(r=>({width:r.width,height:r.height}))')
            assert max(r['height'] for r in rects)-min(r['height'] for r in rects)<4
        if width<=768:
            cards=page.locator('[class*="st-key-gp_company_"]').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().top)')
            assert cards==sorted(cards) and len(set(cards))==3
        page.locator('.st-key-gp_company_summit').screenshot(path=str(OUT/f'operating-card-{width}.png'))
    page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
    page.screenshot(path=str(OUT/f'{label}-{width}.png'),full_page=True)
    receipt['viewports'].append({'page':label,'width':width,'document_overflow':False,'nested_vertical_scroll':False,'table_overflow':False})


def wheel_check(page,label,width):
    table=page.locator('.st-key-gp_company_summit') if label=='overview' else page.locator('.gp-table-wrap').first
    table.scroll_into_view_if_needed()
    offset='(e)=>{let n=0;for(let p=e.parentElement;p;p=p.parentElement)n+=p.scrollTop;return n;}'
    before=table.evaluate(offset)
    box=table.bounding_box()
    page.mouse.move(min(width-30,box['x']+100),min(900,max(120,box['y']+80)))
    page.mouse.wheel(0,280);page.wait_for_timeout(200)
    after=table.evaluate(offset)
    assert after>before,(label,width,'Wheel failed to move the page',before,after)


with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    for width in (390,430,768,1280,1440):
        page=browser.new_page(viewport={'width':width,'height':1100},accept_downloads=True)
        page.on('pageerror',lambda error:receipt['errors'].append(str(error)))
        def local_only(route):
            if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
                receipt['external_requests'].append(route.request.url);route.abort()
            else:route.continue_()
        page.route('**/*',local_only)
        for label,route in ROUTES.items():
            page.goto('http://127.0.0.1:8502/?page='+route)
            expect(page.locator('.gp-brand')).to_be_visible(timeout=60000) if width>900 else None
            settle(page)
            sidebar=page.locator('[data-testid="stSidebar"]')
            if width<=900 and sidebar.get_attribute('data-collapsed')=='false':
                page.get_by_role('button',name='Collapse sidebar',exact=True).click();page.wait_for_timeout(250)
            audit(page,label,width)
            if label in ('overview','foundation'):
                wheel_check(page,label,width)
            if label=='overview':
                page.locator('.st-key-open_summit button').click()
                expect(page.get_by_role('heading',name='Summit Home Services',exact=True)).to_be_visible(timeout=60000)
                assert 'company=summit' in page.url
                page.goto('http://127.0.0.1:8502/?page=overview');settle(page)
            if label in ('summit','tallis','harrow') and width>=768:
                page.get_by_role('button',name='View source evidence',exact=True).click()
                expect(page.get_by_role('heading',name='See where every conclusion came from',exact=True)).to_be_visible(timeout=60000)
                audit(page,label+'-evidence',width)
            if label=='foundation':
                expect(page.get_by_text('Normalization & transformation',exact=True)).to_be_visible()
                assert page.locator('.gp-catalog-sources tbody tr').count()==3
                page.locator('.foundation-detail-grid').screenshot(path=str(OUT/f'mapping-detail-{width}.png'))
                page.get_by_text('Review Required · Supporting observations lack accepted financial classifications',exact=True).click()
                settle(page)
                assert page.locator('[data-testid="stDataFrame"]').count()==0
                audit(page,'foundation-expanded',width)
            if label=='excel':
                for sheet in ['Company Comparison','Investment Issues','Source References']:
                    page.get_by_role('combobox',name='Worksheet preview',exact=True).click()
                    page.get_by_role('option',name=sheet,exact=True).click()
                    audit(page,'excel-'+sheet.replace(' ','-'),width)
        # Native mobile navigation stays reachable after all page transitions.
        if width<=900:
            page.get_by_role('button',name='Expand sidebar',exact=True).click()
            expect(page.get_by_role('button',name='Portfolio Overview',exact=True)).to_be_visible()
            assert page.get_by_role('button',name='Company Comparison',exact=True).count()==0
        page.goto('http://127.0.0.1:8502/?page=comparison')
        expect(page.get_by_role('heading',name='Portfolio Overview',exact=True)).to_be_visible(timeout=60000)
        assert 'page=overview' in page.url
        page.close()
    assert not receipt['errors'] and not receipt['external_requests']
    (OUT/'responsive-receipt.json').write_text(json.dumps(receipt,indent=2))
    browser.close()
    print(json.dumps(receipt,indent=2))
