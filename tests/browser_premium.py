import json,sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
phase=sys.argv[1] if len(sys.argv)>1 else 'after';root=Path(__file__).resolve().parents[1];out=root/'artifacts/premium-polish'/phase;out.mkdir(parents=True,exist_ok=True)
r={'phase':phase,'screens':[],'errors':[],'external_requests':[]}
def wait(page):
 expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
 expect(page.locator('[data-testid="stException"]')).to_have_count(0)
 page.wait_for_timeout(250)
def shot(page,name,locator=None):
 (locator.screenshot(path=str(out/(name+'.png'))) if locator else page.screenshot(path=str(out/(name+'.png')),full_page=True));r['screens'].append(name)
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':1200},permissions=['clipboard-read','clipboard-write'])
 page.on('pageerror',lambda e:r['errors'].append(str(e)))
 def local(route):
  if urlparse(route.request.url).hostname not in ('localhost','127.0.0.1'):r['external_requests'].append(route.request.url);route.abort()
  else:route.continue_()
 page.route('**/*',local)
 for name in ('overview','foundation'):
  page.goto('http://127.0.0.1:8502/?page='+name)
  expect(page.get_by_role('heading',name='Portfolio Overview' if name=='overview' else 'Data Landscape',exact=True)).to_be_visible(timeout=60000);wait(page)
  shot(page,name+'-1440')
  if name=='overview':shot(page,'sidebar',page.locator('[data-testid="stSidebar"]'));shot(page,'operating-cards',page.locator('.st-key-operating_cards'))
  else:
   shot(page,'mapping-detail',page.locator('.foundation-detail-grid'))
   if phase=='after':
    shot(page,'catalog-workflow-context',page.locator('.st-key-catalog_workflow_context'))
    assert page.locator('.catalog-company-source').count()==3
    expect(page.get_by_text('76/100',exact=True)).to_be_visible()
    expect(page.get_by_text('67%',exact=True)).to_be_visible()
  if phase=='after':
   assert page.locator('.gp-brand').inner_text()=='154 Partners\nPortfolio Reporting Copilot\nby NL Intelligence'
   expect(page.locator('.gp-note')).to_have_text('For demo only. All portfolio companies, investment data, and financial figures are synthetic. Any resemblance to real companies or investments is coincidental.')
  page.set_viewport_size({'width':390,'height':1200});wait(page)
  if page.locator('[data-testid="stSidebar"]').get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
  page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0');shot(page,name+'-390')
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
  page.set_viewport_size({'width':1440,'height':1200})
 page.goto('http://127.0.0.1:8503/?page=overview');expect(page.get_by_role('button',name='View on Mobile',exact=True)).to_be_visible(timeout=60000);wait(page)
 if phase=='after':
  foot=page.locator('.st-key-sidebar_footer').bounding_box();assert foot['y']>750 and foot['y']+foot['height']<1210,foot
 shot(page,'qr-sidebar',page.locator('[data-testid="stSidebar"]'));shot(page,'mobile-qr-panel',page.locator('.st-key-mobile_access'))
 page.get_by_role('button',name='View on Mobile',exact=True).click();d=page.get_by_role('dialog');expect(d).to_be_visible();expect(d.get_by_text('https://demo.example.com/?page=overview',exact=True)).to_be_visible();d.locator('[data-testid="stCode"]').hover();shot(page,'qr-dialog');page.keyboard.press('Escape');expect(d).not_to_be_visible()
 assert not r['errors'] and not r['external_requests'];(out/'capture.json').write_text(json.dumps(r,indent=2));b.close();print(json.dumps(r,indent=2))
