"""Synthetic industrial development regression; expectations not derived from parser output."""
from pathlib import Path
import json
from openpyxl import Workbook
ROOT=Path(__file__).parent/'fixtures'

def create():
    expected=dict(revenue=620000,ebitda=85000,ebitda_gap=-25000,over90=40000,over90_share=.2,renewal_start=.95,renewal_end=.82,prior_contract_max=1100,current_contracts=1000)
    (ROOT/'expected_package.json').write_text(json.dumps(expected,indent=2))
    w=Workbook();s=w.active;s.title='Board economics'
    s.append(['Northgate Precision Components']);s.append(['USD whole units; accrual basis'])
    s.append(['Account','Jun-27 Actual','Jun-27 Budget','May-27 Actual'])
    for row in [('Revenue',620000,600000,610000),('Cost of sales',390000,355000,375000),('Gross profit',230000,245000,235000),('Operating expenses',145000,135000,140000),('EBITDA',85000,110000,95000)]:s.append(row)
    s=w.create_sheet('Factory scorecard');s.append(['Northgate Precision Components']);s.append(['Manufacturing and contract measures'])
    s.append(['Measure','Unit','Jan-27','Feb-27','Mar-27','Apr-27','May-27','Jun-27'])
    rows=[('First-pass yield','%',.92,.90,.87,.82,.76,.70),('Repeat order retention','%',.95,.93,.91,.88,.85,.82),('Active contracts','#',1100,1090,1070,1050,1020,1000),('Installation backlog','USD',200000,230000,250000,290000,320000,350000)]
    for row in rows:s.append(row)
    for row in [4,5]:
        for col in range(3,9):s.cell(row,col).number_format='0.0%'
    s=w.create_sheet('Customer balances');s.append(['Northgate Precision Components']);s.append(['Trade receivables as of June 30, 2027']);s.append(['USD whole units'])
    s.append(['Customer','Type','Current','31-60','61-90','Over 90','Total'])
    s.append(['Orion Fabrication','Industrial',60000,10000,10000,40000,120000]);s.append(['Vega Systems','Industrial',70000,10000,0,0,80000]);s.append(['Total receivables','',130000,20000,10000,40000,200000])
    s.append(['AR per GL',None,None,None,None,None,200000]);s.append(['Allowance for doubtful accounts',None,None,None,None,None,-15000])
    s=w.create_sheet('Leadership update');s.append(['Northgate Precision Components — June 2027'])
    s.append(['The active contract base reached a record 1,000 active contracts in June, reflecting the continued strength of our recurring customer relationships.'])
    s.append(['We expect factory performance to recover next quarter, but there is no approved forecast or hiring plan included in this package.'])
    w.save(ROOT/'C_Northgate.xlsx')

if __name__=='__main__':create()
