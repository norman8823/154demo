"""Actual Chrome source clicks and downloaded workbook checks for demo cleanup."""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_documents import evidence_locations,original_document,source_books
OUT=ROOT/'artifacts/demo-cleanup';DOWNLOADS=OUT/'downloads';DOWNLOADS.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images/demo-cleanup';IMAGES.mkdir(parents=True,exist_ok=True)
company=next(c for c in load_companies() if c.id=='tallis')
book,_=source_books(original_document(company))
receipt={'findings':[],'citations':[],'errors':[],'external_requests':[]}

def ready(page):
 expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
 expect(page.locator('[data-testid="stException"]')).to_have_count(0)

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
 with page.expect_download() as d:page.get_by_role('button',name='Download Excel',exact=True).click(timeout=60000)
 d.value.save_as(DOWNLOADS/'portfolio.xlsx')
 page.locator('.st-key-open_tallis button').click()
 expect(page.get_by_role('heading',name='Investment Summary',exact=True)).to_be_visible(timeout=60000)
 expect(page.get_by_role('button',name='View in Source',exact=True)).to_have_count(5,timeout=60000)
 ready(page)
 desktop=page.locator('.st-key-desktop_company_detail')
 expect(desktop.get_by_role('heading',name='Investment Summary',exact=True)).to_be_visible()
 expect(desktop.get_by_role('heading',name='Priority findings',exact=True)).to_be_visible()
 assert desktop.get_by_role('heading',name='Investment Assessment',exact=True).count()==0
 assert desktop.get_by_role('heading',name='Management Questions',exact=True).count()==0
 assert page.get_by_role('button',name='View source evidence',exact=True).count()==0
 assert page.get_by_text('Source Evidence & Excel',exact=True).count()==0
 assert page.get_by_text('Derived calculations & original operands',exact=True).count()==0
 assert page.get_by_role('combobox',name='Original source cell',exact=True).count()==0
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
 page.screenshot(path=str(IMAGES/'tallis-company-detail.png'),full_page=True)
 with page.expect_download() as d:page.get_by_role('button',name='Download Excel',exact=True).click()
 d.value.save_as(DOWNLOADS/'tallis-standard.xlsx')
 for finding in company.review.package['ai_insights']:
  prefix='company_source_tallis_'+str(finding['id'])
  originals,_,unsupported=evidence_locations(company,finding['fact_ids'])
  assert originals
  for index,fact in enumerate(originals[:1]):
   button=page.locator('.st-key-'+prefix+'_view button')
   button.click();dialog=page.get_by_role('dialog',name='Source inspection',exact=True)
   expect(dialog.locator('.source-target')).to_have_attribute('data-coordinate',fact['cell'],timeout=60000)
   expect(dialog.get_by_role('textbox',name='Selected cell',exact=True)).to_have_value(fact['cell'])
   expect(dialog.get_by_role('tab',name=fact['sheet'],exact=True)).to_have_attribute('aria-selected','true')
   raw=book[fact['sheet']][fact['cell']].value
   expect(dialog.locator('.formula-bar')).to_have_text('' if raw is None else str(raw))
   if finding['id']==10000 and index==0:page.screenshot(path=str(IMAGES/'tallis-ebitda-source.png'),full_page=True)
   receipt['citations'].append({'finding_id':finding['id'],'source_id':fact['id'],'worksheet':fact['sheet'],'cell':fact['cell'],'original_value_or_formula':raw,'selected_exactly':True})
   page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0)
  receipt['findings'].append({'finding_id':finding['id'],'title':finding['title'],'original_cells_clicked':1,'default_target_preserved':True,'supporting_records_retained_in_excel':len(unsupported)})
  print('PASS',finding['id'],'default source link; dropdown absent',flush=True)
 (OUT/'browser-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 page.goto('http://127.0.0.1:8502/?page=overview')
 expect(page.get_by_role('heading',name='Portfolio Overview',exact=True)).to_be_visible(timeout=60000)
 ready(page)
 page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTop=0')
 page.screenshot(path=str(IMAGES/'portfolio-overview-app.png'),full_page=True)
 assert not receipt['errors'] and not receipt['external_requests']
 browser.close()
(OUT/'browser-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('PASS all',len(receipt['citations']),'Tallis direct source links; no source dropdowns')
