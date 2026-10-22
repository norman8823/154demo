"""Actual local Chrome outlook hierarchy, company switching and mobile layout."""
import json,sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_outlook import investment_outlook
OUT=ROOT/'artifacts/outlook';IMAGES=ROOT/'docs/images/outlook';IMAGES.mkdir(parents=True,exist_ok=True)
companies=load_companies();receipt={'desktop':[],'phone':[],'errors':[],'external_requests':[]}

def ready(page):
 expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
 expect(page.locator('[data-testid="stException"]')).to_have_count(0)
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
 assert page.locator('.katex:visible').count()==0

with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1200})
 page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
 def local(route):
  if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
   receipt['external_requests'].append(route.request.url);route.abort()
  else:route.continue_()
 page.route('**/*',local)
 page.goto('http://127.0.0.1:8502/')
 expect(page.get_by_role('button',name='View Investment Detail →',exact=True)).to_have_count(3,timeout=60000)
 assert page.get_by_role('button',name='Investment Issues',exact=True).count()==0
 assert page.get_by_role('heading',name='Investment Issues',exact=True).count()==0
 assert page.locator('.st-key-issues_preview').count()==0
 page.locator('.st-key-open_summit button').click()
 for company in companies:
  if company.id!='summit':
   page.get_by_role('combobox',name='Company',exact=True).click()
   page.get_by_role('option',name=company.name,exact=True).click()
  desktop=page.locator('.st-key-desktop_company_detail');outlook=desktop.locator('.investment-outlook')
  expect(outlook).to_have_attribute('data-company',company.id,timeout=60000)
  expected=investment_outlook(company)
  expect(outlook.get_by_role('heading',name=expected.headline,exact=True)).to_be_visible()
  for paragraph in expected.paragraphs:expect(outlook.get_by_text(paragraph,exact=True)).to_be_visible()
  ready(page)
  order=desktop.locator('[data-testid="stHeading"] h3').all_text_contents()
  assert order[:3]==['Investment Outlook','Investment Summary','Priority findings'],order
  assert page.get_by_role('button',name='Investment Issues',exact=True).count()==0
  first=desktop.locator('.st-key-finding_panel_10000')
  first.get_by_text('Follow Up',exact=True).click()
  finding=company.review.package['ai_insights'][0]
  expect(first.get_by_text(finding['action'],exact=True)).to_be_visible()
  first.get_by_text('Follow Up',exact=True).click()
  page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
  page.screenshot(path=str(IMAGES/(company.id+'-desktop.png')),full_page=True)
  receipt['desktop'].append({'company':company.id,'same_company_outlook':True,'heading_order':order[:3],'original_management_action':True,'no_page_overflow':True})
  print('desktop PASS',company.id,flush=True)
 # Compatibility URLs retain all accepted findings without a promoted nav item.
 for route in ('issues','watchlist'):
  page.goto('http://127.0.0.1:8502/?page='+route)
  expect(page.get_by_text('17 findings shown',exact=False)).to_be_visible(timeout=60000)
  assert page.get_by_role('button',name='Investment Issues',exact=True).count()==0
 receipt['legacy_issue_routes']='issues/watchlist: 17 original findings retained'
 for width in (390,430):
  page.set_viewport_size({'width':width,'height':1100})
  for company in companies:
   page.goto('http://127.0.0.1:8502/?page=company&company='+company.id)
   mobile=page.locator('.st-key-mobile_company_detail');outlook=mobile.locator('.investment-outlook')
   expect(outlook).to_have_attribute('data-company',company.id,timeout=60000)
   expect(outlook).to_be_visible()
   expected=investment_outlook(company)
   for paragraph in expected.paragraphs:expect(outlook.get_by_text(paragraph,exact=True)).to_be_visible()
   sidebar=page.locator('[data-testid="stSidebar"]')
   if sidebar.get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
   ready(page)
   assert not page.locator('.st-key-desktop_company_detail').is_visible()
   assert mobile.locator('.v2-figures,.v3-card-returns,[data-testid="stMetric"]').count()==0
   assert page.locator('.source-grid').count()==0
   page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
   page.screenshot(path=str(IMAGES/(company.id+'-'+str(width)+'.png')),full_page=True)
   receipt['phone'].append({'company':company.id,'width':width,'same_outlook_as_desktop':True,'no_repeated_overview_metrics':True,'no_page_overflow':True})
   print('phone PASS',width,company.id,flush=True)
 assert not receipt['errors'] and not receipt['external_requests']
 browser.close()
(OUT/'browser-outlook-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
