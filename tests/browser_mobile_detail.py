"""Actual Chrome phone journeys and unchanged desktop reports on localhost8502."""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_mobile_detail import assessment_items
from portfolio_investments import investments_for,investment_summary
from portfolio_comparison import money
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/mobile-investment-detail/browser';OUT.mkdir(parents=True,exist_ok=True)
receipt={'phone_cases':[],'desktop_cases':[],'errors':[],'external_requests':[]}


def settle(page):
    expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    page.wait_for_timeout(180)


def audit(page):
    settle(page)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
    assert page.locator('.katex:visible').count()==0
    traps=page.evaluate('''()=>[...document.querySelectorAll('*')].filter(e=>{let s=getComputedStyle(e),r=e.getBoundingClientRect();return r.width>0&&r.height>40&&e.scrollHeight>e.clientHeight+3&&/auto|scroll/.test(s.overflowY)&&!['stMain','stAppViewContainer','stApp','stSidebar','stSidebarContent','stSidebarUserContent'].includes(e.dataset.testid)&&!['HTML','BODY'].includes(e.tagName)&&!e.closest('[data-testid="stSidebar"]');}).map(e=>({tag:e.tagName,test:e.dataset.testid}))''')
    assert not traps,traps

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':390,'height':1200},accept_downloads=True)
    page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
    def local(route):
        if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
            receipt['external_requests'].append(route.request.url);route.abort()
        else:route.continue_()
    page.route('**/*',local)
    companies=load_companies()
    for width in (390,430):
        page.set_viewport_size({'width':width,'height':1200})
        for company in companies:
            print('Phone',width,company.id,flush=True)
            page.goto('http://127.0.0.1:8502/?page=overview')
            expect(page.locator('.st-key-open_'+company.id+' button')).to_be_visible(timeout=60000)
            settle(page)
            if page.locator('[data-testid="stSidebar"]').get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
            card=page.locator('.st-key-gp_company_'+company.id)
            for text in ('REVENUE','REPORTED EBITDA','EBITDA MARGIN','GROSS MOIC','GROSS IRR'):assert text in card.inner_text()
            expect(card.get_by_role('button',name='View Investment Detail →',exact=True)).to_be_visible()
            if company.id=='summit' and width==390:card.screenshot(path=str(OUT/'company-card-390.png'))
            page.locator('.st-key-open_'+company.id+' button').click()
            mobile=page.locator('.st-key-mobile_company_detail')
            expect(mobile).to_be_visible(timeout=60000)
            expect(mobile.get_by_role('heading',name=company.name,exact=True)).to_be_visible()
            expect(mobile.get_by_role('heading',name='Investment Assessment',exact=True)).to_be_visible()
            assert 'company='+company.id in page.url
            assert not page.locator('.st-key-desktop_company_detail').is_visible()
            assert page.get_by_role('combobox',name='Company Excel format',exact=True).count()==0
            assert page.locator('[data-testid="stMetric"]:visible,.gp-table:visible,[data-testid="stDownloadButton"]:visible').count()==0
            assert mobile.locator('.v2-figures,.v3-card-returns').count()==0
            lead=assessment_items(company)[0]
            for text in (lead['conclusion'],lead['assessment'],lead['action'],lead['management_question']):expect(mobile.get_by_text(text,exact=True)).to_be_visible()
            context=mobile.locator('.mobile-investment-context').inner_text()
            result=investment_summary(investments_for([company]))
            for key in ('invested_capital','realized_proceeds','current_equity_value'):assert money(result[key]) in context
            assert len(mobile.locator('[data-testid="stExpander"]').all())==len(company.review.package['ai_insights'])
            audit(page)
            page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
            page.screenshot(path=str(OUT/f'{company.id}-{width}.png'),full_page=True)
            page.get_by_role('button',name='← Back to portfolio',exact=True).click()
            expect(page.get_by_role('heading',name='Portfolio Overview',exact=True)).to_be_visible()
            receipt['phone_cases'].append({'company':company.id,'width':width,'card_action_and_back':'pass','original_assessment_and_incremental_context':'pass','full_report_controls_hidden':True,'no_overflow_or_nested_scrolling':True})
        # A finding deep link becomes the primary assessment rather than technical evidence.
        page.goto('http://127.0.0.1:8502/?page=company&company=summit&finding=10004')
        expect(page.locator('.st-key-mobile_primary_summit_10004')).to_be_visible(timeout=60000)
        expect(page.get_by_role('heading',name='Branch and consolidated EBITDA schedules do not reconcile',exact=True)).to_be_visible()
        assert page.get_by_role('heading',name='See where every conclusion came from',exact=True).count()==0
        # Contextual switching drops the prior company's finding route and contents.
        field=page.get_by_role('combobox',name='Company',exact=True);field.click()
        page.get_by_role('option',name='Tallis Brook Accounting',exact=True).click()
        expect(page.locator('.st-key-mobile_primary_tallis_10000')).to_be_visible()
        assert 'company=tallis' in page.url and 'finding=' not in page.url
        assert page.locator('.st-key-mobile_primary_summit_10004').count()==0
        audit(page)
        receipt['phone_deep_link_and_switching']='pass'
    page.set_viewport_size({'width':1440,'height':1200})
    for company in companies:
        print('Desktop',company.id,flush=True)
        page.goto('http://127.0.0.1:8502/?page=company&company='+company.id)
        expect(page.get_by_role('heading',name=company.name,exact=True)).to_be_visible(timeout=60000)
        assert not page.locator('.st-key-mobile_company_detail').is_visible()
        expect(page.get_by_role('heading',name='Investment Summary',exact=True)).to_be_visible()
        expect(page.get_by_role('combobox',name='Company Excel format',exact=True)).to_be_visible()
        expect(page.get_by_role('button',name='↓  Download Excel Report',exact=True)).to_be_visible()
        audit(page)
        if company.id=='summit':page.screenshot(path=str(OUT/'desktop-complete-1440.png'),full_page=True)
        page.get_by_role('button',name='View in Source',exact=True).first.click()
        expect(page.get_by_role('dialog').locator('.source-target')).to_have_count(1,timeout=60000)
        page.keyboard.press('Escape')
        expect(page.get_by_role('dialog')).to_have_count(0)
        audit(page)
        receipt['desktop_cases'].append({'company':company.id,'full_summary_exports_and_evidence':'pass'})
    assert not receipt['errors'] and not receipt['external_requests']
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2));browser.close()
