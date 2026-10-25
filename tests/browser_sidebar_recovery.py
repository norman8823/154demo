"""Actual Chrome native locked/sidebar recovery checks; local preview only."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/sidebar-recovery';OUT.mkdir(parents=True,exist_ok=True)
SHOTS=ROOT/'docs/images/sidebar-recovery';SHOTS.mkdir(parents=True,exist_ok=True)
results=[]

def ready(page):
 expect(page.get_by_role('heading',name='Portfolio Overview',exact=True)).to_be_visible(timeout=60000)
 expect(page.locator('[data-testid=stApp]')).to_have_attribute('data-test-script-state','notRunning',timeout=60000)
 expect(page.locator('[data-testid=stException]')).to_have_count(0)
 assert not page.evaluate('document.documentElement.scrollWidth > innerWidth+1')


def opened(page):
 expect(page.locator('[data-testid=stSidebar]')).to_have_attribute('data-collapsed','false')
 expect(page.get_by_role('button',name='Data Landscape',exact=True)).to_be_in_viewport()
 page.wait_for_function("document.querySelector('[data-testid=stSidebar]').getBoundingClientRect().left >= -1")

def closed(page):
 expect(page.locator('[data-testid=stSidebar]')).to_have_attribute('data-collapsed','true')
 page.wait_for_function("document.querySelector('[data-testid=stSidebar]').getBoundingClientRect().right <= 1")
 expect(page.get_by_role('button',name='Expand sidebar',exact=True)).to_be_in_viewport()
 assert page.locator('[data-testid=stHeader]').bounding_box()['height'] >= 44

with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 for width in (390,430,1280,1440):
  context=browser.new_context(viewport={'width':width,'height':1000})
  context.add_init_script("localStorage.setItem('stSidebarCollapsed-/', 'true')")
  page=context.new_page()
  page.goto('http://127.0.0.1:8502/');ready(page)
  sidebar=page.locator('[data-testid=stSidebar]')
  if width<768:
   closed(page)
   expand=page.get_by_role('button',name='Expand sidebar',exact=True)
   expect(expand).to_be_in_viewport();expand.click();opened(page)
   page.screenshot(path=str(SHOTS/f'mobile-open-{width}.png'))
   collapse=page.get_by_role('button',name='Collapse sidebar',exact=True)
   expect(collapse).to_be_visible();collapse.click()
   closed(page)
   page.reload();ready(page)
   expect(expand).to_be_in_viewport();expand.click();opened(page)
   page.get_by_role('button',name='Source Documents',exact=True).click()
   expect(page.get_by_role('heading',name='Source Documents',exact=True)).to_be_visible()
   # Close/open remains available after route changes.
   if sidebar.get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
   expect(expand).to_be_visible();expand.click()
   page.get_by_role('button',name='Portfolio Overview',exact=True).click();ready(page)
   if sidebar.get_attribute('data-collapsed')=='false':page.get_by_role('button',name='Collapse sidebar',exact=True).click()
   closed(page)
   page.screenshot(path=str(SHOTS/f'mobile-closed-{width}.png'))
   # A real collapsed state becomes expanded when resized to desktop.
   page.set_viewport_size({'width':1280,'height':1000});opened(page)
   expect(page.get_by_role('button',name='Collapse sidebar',exact=True)).to_have_count(0)
   page.reload();ready(page);opened(page)
  else:
   opened(page)
   expect(page.get_by_role('button',name='Collapse sidebar',exact=True)).to_have_count(0)
   expect(page.get_by_role('button',name='Expand sidebar',exact=True)).to_have_count(0)
   page.reload();ready(page);opened(page)
   expect(page.get_by_role('button',name='Collapse sidebar',exact=True)).to_have_count(0)
   page.get_by_role('button',name='Data Landscape',exact=True).click()
   expect(page.get_by_role('heading',name='Data Landscape',exact=True)).to_be_visible();opened(page)
   page.get_by_role('button',name='Portfolio Overview',exact=True).click();ready(page)
   page.screenshot(path=str(SHOTS/f'desktop-{width}.png'))
  assert 'NL Intelligence' in page.locator('.gp-brand').inner_text()
  assert 'Portfolio Reporting Copilot' in page.locator('.gp-brand').inner_text()
  assert 'linear-gradient' in sidebar.evaluate('(e)=>getComputedStyle(e).backgroundImage')
  assert page.locator('.st-key-sidebar_footer').count()==1
  results.append({'width':width,'stored_collapsed_state':True,'refresh_recovery':'pass','navigation':'pass','mobile_toggle_or_desktop_lock':'pass','branding_gradient_footer':'preserved'})
  context.close()
 browser.close()
(OUT/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
