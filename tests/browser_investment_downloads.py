"""Actual source bytes, documents reports and final download-area screenshots."""
import json,sys,hashlib,os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from portfolio_data import load_companies
from portfolio_documents import original_document
OUT=ROOT/'artifacts/investment-ui';IMAGES=Path(os.environ.get('COPILOT_DEMO_SCREENSHOT_DIR',ROOT/'docs/images/investment-ui'))
IMAGES.mkdir(parents=True,exist_ok=True)
BASE_URL=os.environ.get('COPILOT_GP_TEST_URL','http://127.0.0.1:8502')
receipt={'original_downloads':[],'errors':[],'external_requests':[]}
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':1280,'height':1100},accept_downloads=True)
 page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
 def local(route):
  if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
   receipt['external_requests'].append(route.request.url);route.abort()
  else:route.continue_()
 page.route('**/*',local)
 page.goto(BASE_URL+'/?page=excel')
 expect(page.get_by_role('heading',name='Source Documents',exact=True)).to_be_visible(timeout=60000)
 for c in load_companies():
  original=original_document(c)
  with page.expect_download() as d:page.locator('.st-key-source_document_'+c.id).get_by_role('button',name='Download Original',exact=True).click()
  target=OUT/(c.id+'-original.xlsx');d.value.save_as(target)
  assert target.read_bytes()==original.data
  receipt['original_downloads'].append({'company':c.id,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'byte_identical':True})
 assert page.get_by_role('button',name='Download Excel',exact=True).count()==0
 assert page.get_by_role('combobox',name='Company report',exact=True).count()==0
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
 receipt['source_library_only']='pass'
 page.screenshot(path=str(IMAGES/'source-documents-1280.png'),full_page=True,animations='disabled')
 page.goto(BASE_URL+'/?page=company&company=tallis')
 expect(page.get_by_role('heading',name='Investment Detail',level=1,exact=True)).to_be_visible(timeout=60000)
 assert page.get_by_role('combobox',name='Company Excel format',exact=True).count()==0
 assert page.get_by_text('Use supplied firm template',exact=True).count()==0
 assert page.locator('input[type=file]').count()==0
 with page.expect_download() as d:page.get_by_role('button',name='Download Excel',exact=True).click()
 d.value.save_as(OUT/'investment-tallis-standard.xlsx')
 receipt['investment_standard_download']='pass'
 page.goto(BASE_URL+'/?page=issues')
 expect(page.get_by_role('heading',name='Investment Issues',exact=True)).to_be_visible(timeout=60000)
 download=page.get_by_role('button',name='Download Excel',exact=True)
 assert download.bounding_box()['y']>page.get_by_role('button',name='View source evidence →',exact=True).last.bounding_box()['y']
 receipt['legacy_issues_download_at_bottom']='pass'
 page.set_viewport_size({'width':1440,'height':1100})
 for route,company,filename,label in [('overview',None,'overview-download','Download Excel'),('company','tallis','tallis-download','Download Excel')]:
  page.goto(BASE_URL+'/?page='+route+('&company='+company if company else ''))
  button=page.get_by_role('button',name=label,exact=True);expect(button).to_be_visible(timeout=60000)
  page.locator('[data-testid="stMain"]').evaluate('(e)=>e.scrollTo(0,e.scrollHeight)')
  button.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})")
  page.wait_for_timeout(200)
  assert button.bounding_box()['y']+button.bounding_box()['height']<=1100
  page.screenshot(path=str(IMAGES/(filename+'.png')),full_page=True,animations='disabled')
 assert not receipt['errors'] and not receipt['external_requests']
 b.close()
(OUT/'final-downloads.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
