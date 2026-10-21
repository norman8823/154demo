"""Automatic workbook recognition through real upload, generation and both Excel downloads."""
import os
from pathlib import Path
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts';OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100})
    page.goto(os.environ.get('COPILOT_TEST_URL','http://127.0.0.1:8501'))
    expect(page.get_by_role('heading',name='Generate a portfolio review',exact=True)).to_be_visible(timeout=30000)
    page.locator('input[type=file]').first.set_input_files(ROOT/'tests/fixtures/Tallis_Brook_Accounting_Sep2026.xlsx')
    expect(page.get_by_text('✓ Income statement recognized',exact=True)).to_be_visible()
    panel=page.locator('details').filter(has=page.get_by_text('Review Account Mappings',exact=True))
    assert panel.get_attribute('open') is None
    page.get_by_role('button',name='Generate Portfolio Review').click()
    expect(page.get_by_role('heading',name='September 2026 Portfolio Review',exact=True)).to_be_visible(timeout=30000)
    expect(page.get_by_text('$3.48M',exact=True)).to_be_visible()
    expect(page.get_by_text('$684K',exact=True)).to_be_visible()
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)
    page.screenshot(path=str(OUT/'tallis-automatic-results.png'),full_page=True)
    def download(name):
        with page.expect_download() as result:page.get_by_role('button',name='Download Excel Report').first.click()
        result.value.save_as(OUT/name);w=load_workbook(OUT/name)
        assert any(str(row[0]).endswith('2026-09 · actual · revenue') and row[1]==3475418 for row in w['Financial Performance'].values)
        assert any(str(row[0]).endswith('2026-09 · actual · ebitda') and row[1]==684306 for row in w['Financial Performance'].values)
        return w
    download('tallis-standard.xlsx')
    page.get_by_role('button',name='View Evidence').first.click()
    expect(page.get_by_role('heading',name='See where every conclusion came from',exact=True)).to_be_visible()
    page.get_by_text('01  Upload & Setup',exact=True).click()
    page.get_by_text('Use existing firm template',exact=True).click()
    page.locator('input[type=file]').nth(1).set_input_files(ROOT/'sample_templates/Sample_Firm_Review_Template.xlsx')
    expect(page.get_by_role('button',name='Remove Sample_Firm_Review_Template.xlsx',exact=True)).to_be_visible()
    page.get_by_role('button',name='Generate Portfolio Review').click()
    expect(page.get_by_role('heading',name='September 2026 Portfolio Review',exact=True)).to_be_visible(timeout=30000)
    assert download('tallis-custom.xlsx')['Partner Review']['C16'].data_type=='f'
    print('PASS: Tallis upload -> Generate without configuration -> source evidence -> standard/custom Excel with verified reported totals.')
    browser.close()
