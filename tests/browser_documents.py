"""Actual Chrome: desktop Excel scrollbars/tabs, source integrity and phone exclusion."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlencode,urlparse
from openpyxl import load_workbook
from openpyxl.utils import coordinate_to_tuple,get_column_letter
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/final-source';OUT.mkdir(parents=True,exist_ok=True)
IMAGES=ROOT/'docs/images/final-source';IMAGES.mkdir(parents=True,exist_ok=True)
MANIFEST=json.loads((ROOT/'demo_results/manifest.json').read_text())
TARGETS=[('summit','Summit Home Services','Income Statement','D15'),('tallis','Tallis Brook Accounting','Practice P&L','G12'),('harrow','Harrow Ridge Environmental','P&L Summary','F13')]
receipt={'desktop':[],'downloads':[],'citations':[],'mobile':[],'errors':[],'external_requests':[]}
BOOKS={slug:load_workbook(ROOT/next(e['workbook'] for e in MANIFEST['runs'] if e['run'].startswith(slug+'-')),data_only=False,keep_links=False) for slug,_,_,_ in TARGETS}


def ready(page):
 expect(page.locator('[data-testid="stApp"]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
 expect(page.locator('[data-testid="stException"]')).to_have_count(0)


def direct(page,slug,sheet,cell):
 page.goto('http://127.0.0.1:8502/?'+urlencode({'page':'source','company':slug,'sheet':sheet,'cell':cell}))
 dialog=page.get_by_role('dialog',name='Source inspection',exact=True)
 expect(dialog.locator('.source-target')).to_have_attribute('data-coordinate',cell,timeout=60000)
 return dialog


def selected(dialog,sheet,cell,visible=True):
 expect(dialog.get_by_role('textbox',name='Selected cell',exact=True)).to_have_value(cell)
 value=sheet[cell].value
 expect(dialog.locator('.formula-bar')).to_have_text('' if value is None else str(value))
 expect(dialog.get_by_role('tab',name=sheet.title,exact=True)).to_have_attribute('aria-selected','true')
 if visible is None:visible=dialog.locator('[role="gridcell"][data-coordinate="'+cell+'"]').count()>0
 if visible:expect(dialog.locator('.source-target')).to_have_attribute('data-coordinate',cell)
 else:expect(dialog.locator('.source-target')).to_have_count(0)
 assert dialog.locator('[role="gridcell"]').count()<=72
 assert not dialog.locator('.source-grid').evaluate('(e)=>e.scrollWidth>e.clientWidth+1')


def jump(dialog,sheet,cell):
 field=dialog.get_by_role('textbox',name='Selected cell',exact=True);field.fill(cell);field.press('Enter');selected(dialog,sheet,cell)


def drag(page,bar,end):
 thumb=bar.locator('.scrollbar-thumb').bounding_box();track=bar.bounding_box()
 vertical=bar.get_attribute('aria-orientation')=='vertical'
 x=thumb['x']+thumb['width']/2;y=thumb['y']+thumb['height']/2
 page.mouse.move(x,y);page.mouse.down()
 if vertical:y=track['y']+thumb['height']/2 if end=='start' else track['y']+track['height']-thumb['height']/2
 else:x=track['x']+thumb['width']/2 if end=='start' else track['x']+track['width']-thumb['width']/2
 page.mouse.move(x,y,steps=8);page.mouse.up()
 expect(bar).to_have_attribute('aria-valuenow','1' if end=='start' else bar.get_attribute('aria-valuemax'))


def track_end(bar):
 box=bar.bounding_box();vertical=bar.get_attribute('aria-orientation')=='vertical'
 bar.click(position={'x':box['width']/2 if vertical else box['width']-2,'y':box['height']-2 if vertical else box['height']/2})
 expect(bar).to_have_attribute('aria-valuenow',bar.get_attribute('aria-valuemax'))


def native_scroll_offset(dialog):
 return dialog.evaluate('''e=>{let sum=0;for(let p=e;p;p=p.parentElement)sum+=p.scrollTop;for(const p of e.querySelectorAll('*'))if(/auto|scroll/.test(getComputedStyle(p).overflowY))sum+=p.scrollTop;return sum;}''')


with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
 page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
 def local(route):
  if urlparse(route.request.url).hostname not in ('127.0.0.1','localhost'):
   receipt['external_requests'].append(route.request.url);route.abort()
  else:route.continue_()
 page.route('**/*',local)
 for width in (1280,1440):
  page.set_viewport_size({'width':width,'height':1000})
  for index,(slug,company,sheet_name,cell) in enumerate(TARGETS):
   sheet=BOOKS[slug][sheet_name];dialog=direct(page,slug,sheet_name,cell);selected(dialog,sheet,cell)
   expect(dialog.get_by_role('heading',name=company,exact=True)).to_be_visible()
   expect(dialog.get_by_text('Read-only · Verified original',exact=True)).to_be_visible()
   assert dialog.get_by_role('combobox',name='Worksheet',exact=True).count()==0
   assert dialog.get_by_role('button',name='Close',exact=True).count()==1 # Native X only.
   assert dialog.locator('button').filter(has_text=re.compile(r'^Close$')).count()==0
   assert dialog.get_by_text('Original source workbook',exact=True).count()==0
   assert dialog.get_by_text('Original formula text',exact=True).count()==0
   assert dialog.locator('.range-navigation').count()==0
   assert dialog.get_by_role('tab').all_text_contents()==BOOKS[slug].sheetnames
   heading=dialog.locator('h2[slot="title"]')
   assert heading.evaluate('(e)=>getComputedStyle(e).clip')=='rect(0px, 0px, 0px, 0px)'
   vertical=dialog.get_by_role('scrollbar',name='Worksheet rows',exact=True)
   horizontal=dialog.get_by_role('scrollbar',name='Worksheet columns',exact=True)
   expect(vertical).to_be_visible();expect(horizontal).to_be_visible()
   grid=dialog.locator('.source-grid').bounding_box();v=vertical.bounding_box();h=horizontal.bounding_box();tabs=dialog.locator('.worksheet-tabrail').bounding_box()
   assert v['x']>=grid['x']+grid['width']-1 and abs(v['height']-grid['height'])<3
   assert h['y']>=grid['y']+grid['height']-1 and tabs['y']>=h['y']+h['height']-1
   assert int(vertical.get_attribute('aria-valuemax'))==sheet.max_row-12+1
   # Authentic cited-cell screenshot, including both scrollbars and bottom tabs.
   if width==1440 or slug=='summit':page.screenshot(path=str(IMAGES/(slug+'-'+str(width)+'-cited.png')),full_page=True)
   # Dragging/track-clicking moves the viewport while preserving selection/formula.
   drag(page,vertical,'end');selected(dialog,sheet,cell,False)
   drag(page,vertical,'start');selected(dialog,sheet,cell,None)
   track_end(vertical);selected(dialog,sheet,cell,False)
   dialog.locator('.source-grid').focus();page.keyboard.press('ArrowDown')
   r,c=coordinate_to_tuple(cell);next_cell=get_column_letter(c)+str(r+1);selected(dialog,sheet,next_cell)
   jump(dialog,sheet,cell)
   drag(page,horizontal,'end');selected(dialog,sheet,cell,None)
   drag(page,horizontal,'start');selected(dialog,sheet,cell,None)
   track_end(horizontal);selected(dialog,sheet,cell,None)
   dialog.locator('.source-grid').focus();page.keyboard.press('ArrowLeft');selected(dialog,sheet,get_column_letter(c-1)+str(r))
   # Each grid edge shifts the range; unrelated focused controls leave it alone.
   jump(dialog,sheet,cell)
   corner=dialog.locator('[role="gridcell"]').last.get_attribute('data-coordinate');rr,cc=coordinate_to_tuple(corner)
   dialog.locator('[role="gridcell"]').last.click();page.keyboard.press('ArrowDown');selected(dialog,sheet,get_column_letter(cc)+str(rr+1))
   if cc<sheet.max_column:page.keyboard.press('ArrowRight');selected(dialog,sheet,get_column_letter(cc+1)+str(rr+1))
   corner=dialog.locator('[role="gridcell"]').first.get_attribute('data-coordinate');rr,cc=coordinate_to_tuple(corner)
   dialog.locator('[role="gridcell"]').first.click();page.keyboard.press('ArrowUp');selected(dialog,sheet,get_column_letter(cc)+str(rr-1))
   if cc>1:page.keyboard.press('ArrowLeft');selected(dialog,sheet,get_column_letter(cc-1)+str(rr-1))
   jump(dialog,sheet,cell);dialog.locator('.formula-bar').focus();page.keyboard.press('ArrowDown');selected(dialog,sheet,cell)
   dialog.locator('.source-target').click();page.keyboard.type('=2+2');selected(dialog,sheet,cell) # No editing.
   # Native dialog scrolling remains available; wheel never navigates worksheet.
   dialog.locator('.source-details summary').click();expect(dialog.locator('.source-details')).to_contain_text('Verified standardized value')
   assert sheet[cell].value not in dialog.locator('.source-details').inner_text()
   dialog.get_by_role('button',name='Download Original',exact=True).scroll_into_view_if_needed()
   before=native_scroll_offset(dialog);before_view=(vertical.get_attribute('aria-valuenow'),horizontal.get_attribute('aria-valuenow'))
   grid=dialog.locator('.source-grid').bounding_box();page.mouse.move(grid['x']+grid['width']/2,max(100,min(800,grid['y']+grid['height']/2)));page.mouse.wheel(90,-230);page.wait_for_timeout(250)
   assert before_view==(vertical.get_attribute('aria-valuenow'),horizontal.get_attribute('aria-valuenow'))
   assert native_scroll_offset(dialog)!=before,(width,slug,'wheel over grid trapped')
   dialog.get_by_role('button',name='Download Original',exact=True).scroll_into_view_if_needed();before=native_scroll_offset(dialog)
   point=dialog.locator('.source-details summary').bounding_box();page.mouse.move(point['x']+100,min(900,point['y']+10));page.mouse.wheel(0,-180);page.wait_for_timeout(250)
   assert native_scroll_offset(dialog)!=before,(width,slug,'outside dialog scrolling failed')
   assert before_view==(vertical.get_attribute('aria-valuenow'),horizontal.get_attribute('aria-valuenow'))
   dialog.locator('.source-details summary').click()
   # Tabs use real source sheets, including the one-column narrative.
   dialog.get_by_role('tab',name=BOOKS[slug].sheetnames[0],exact=True).click()
   selected(dialog,BOOKS[slug].worksheets[0],'A1');expect(horizontal).to_have_attribute('aria-disabled','true')
   dialog.locator('.source-target').click();page.keyboard.press('ArrowRight');selected(dialog,BOOKS[slug].worksheets[0],'A1')
   if slug=='harrow':
    next_tabs=dialog.get_by_role('button',name='Next worksheets',exact=True)
    if next_tabs.count():
     expect(next_tabs).to_be_visible();next_tabs.click()
     assert dialog.locator('.worksheet-tabs').evaluate('(e)=>e.scrollLeft')>0
    else:
     assert dialog.locator('.worksheet-tabs').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
    dialog.get_by_role('tab',name=BOOKS[slug].sheetnames[-1],exact=True).click();selected(dialog,BOOKS[slug].worksheets[-1],'A1')
   dialog.get_by_role('tab',name=sheet_name,exact=True).click();selected(dialog,sheet,cell)
   # Original bytes and local cursor survive Download Original.
   entry=next(e for e in MANIFEST['runs'] if e['run'].startswith(slug+'-'))
   with page.expect_download() as download:dialog.get_by_role('button',name='Download Original',exact=True).click()
   path=OUT/(slug+'-'+str(width)+'-original.xlsx');download.value.save_as(path)
   assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['workbook_sha256']
   selected(dialog,sheet,cell);receipt['downloads'].append({'company':slug,'width':width,'sha256':entry['workbook_sha256'],'viewer_selection_preserved':True})
   # Native dismissal modes, with no custom close button.
   dismissal=['X','Escape','outside'][index]
   if dismissal=='X':dialog.get_by_role('button',name='Close',exact=True).click()
   elif dismissal=='Escape':page.keyboard.press('Escape')
   else:page.mouse.click(5,500)
   expect(page.get_by_role('dialog')).to_have_count(0)
   receipt['desktop'].append({'company':slug,'width':width,'citation':sheet_name+'!'+cell,'drag_track_bounds':'pass','independent_viewport_selection':'pass','click_arrows_edge_reveal':'pass','wheel_changes_worksheet':False,'native_dialog_scrolling':'pass','tabs_and_citation_return':'pass','read_only':'pass','dismissal':dismissal})
   print('desktop PASS',width,slug,flush=True)
 # Existing accepted finding / derived operand routes.
 page.set_viewport_size({'width':1440,'height':1000})
 for route,key in [('issues','issue_source_summit_'),('company&company=summit&finding=10000','company_source_summit_')]:
  page.goto('http://127.0.0.1:8502/?page='+route)
  button=page.locator('[class*="st-key-'+key+'"][class*="_view"] button').first;expect(button).to_be_visible(timeout=60000)
  operand=page.locator('[class*="st-key-'+key+'"][class*="_operand"]').first.get_by_role('combobox',name='Original source cell',exact=True).input_value()
  button.click();dialog=page.get_by_role('dialog');expect(dialog.locator('.source-target')).to_have_count(1,timeout=60000)
  cell=dialog.get_by_role('textbox',name='Selected cell',exact=True).input_value();sheet_name=dialog.get_by_role('tab',selected=True).inner_text()
  assert cell in operand and sheet_name in operand;selected(dialog,BOOKS['summit'][sheet_name],cell)
  page.keyboard.press('Escape');expect(page.get_by_role('dialog')).to_have_count(0);receipt['citations'].append({'route':route,'operand':sheet_name+'!'+cell})
 # Fail-closed direct invalid source citations.
 page.goto('http://127.0.0.1:8502/?'+urlencode({'page':'source','company':'summit','sheet':'No such worksheet','cell':'D15'}))
 expect(page.get_by_text('Source preview unavailable:',exact=False)).to_be_visible(timeout=60000);assert page.locator('.source-grid').count()==0
 # Resize an open desktop viewer: remove it, then show the direct-route message.
 direct(page,'summit','Income Statement','D15');page.set_viewport_size({'width':430,'height':950})
 expect(page.locator('.source-grid')).to_have_count(0,timeout=60000)
 expect(page.get_by_text('Source inspection is available on desktop.',exact=True)).to_be_visible(timeout=60000)
 for width in (390,430):
  page.set_viewport_size({'width':width,'height':1000})
  for route in ('excel','foundation','issues','company&company=summit','source&company=summit&sheet=Income%20Statement&cell=D15'):
   page.goto('http://127.0.0.1:8502/?page='+route)
   expect(page.locator('.gp-breadcrumb')).to_be_attached(timeout=60000);ready(page)
   assert page.get_by_role('button',name='Preview',exact=True).count()==0
   assert page.get_by_role('button',name='View in Source',exact=True).count()==0
   assert page.locator('.excel-viewer').count()==0 and page.locator('.source-grid').count()==0
   if route.startswith('source'):
    expect(page.get_by_text('Source inspection is available on desktop.',exact=True)).to_be_visible()
    if width==390:page.screenshot(path=str(IMAGES/'phone-source-inspection-message.png'),full_page=True)
   assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
   receipt['mobile'].append({'width':width,'route':route,'worksheet_mounted':False,'preview_actions':False,'horizontal_overflow':False})
 assert not receipt['errors'] and not receipt['external_requests'],receipt
 (OUT/'browser-documents.json').write_text(json.dumps(receipt,indent=2));browser.close();print(json.dumps(receipt,indent=2))
