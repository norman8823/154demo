"""Synthetic ledger supporting schedules, separate from source-verified sheets."""
import math
from openpyxl.styles import Alignment
from portfolio_investments import investments_for, investment_summary, NOTICE, METHOD


def attach_investment_excel(wb,companies):
    from portfolio_excel import literal,link,headers,row_values,narrative,MONEY,PERCENT,COMPANY_SHEETS
    investments=investments_for(companies);portfolio=investment_summary(investments)
    ws=wb['Investment Ledger'];ws['A2']=NOTICE;ws['A3']='Calculated snapshot, not a live financial model. All inputs are fictional USD sponsor amounts. Original company operating reports are separate. '+METHOD
    ws.row_dimensions[2].height=36;ws.row_dimensions[3].height=44
    labels=['Company','Invested capital','Realized proceeds','Current sponsor equity','Total value','Gross MOIC','Gross IRR','Valuation date','IRR status / qualification','Detail']
    headers(ws,5,labels)
    for row,(name,summary) in enumerate([(i.company_name,investment_summary([i])) for i in investments]+[('Portfolio',portfolio)],6):
        row_values(ws,row,[name]+[summary[k] for k in ('invested_capital','realized_proceeds','current_equity_value','total_value','gross_moic','gross_irr','valuation_date')]+[summary['irr_detail'],'See supporting schedules'],62)
        for col in range(2,6):ws.cell(row,col).number_format=MONEY
        ws.cell(row,6).number_format='0.00"x"';ws.cell(row,7).number_format='0.00%'
        for col in (6,7,8):ws.cell(row,col).alignment=Alignment(horizontal='center',vertical='top',wrap_text=True)
    narrative(ws,11,'Definitions','Invested = absolute contributions; total value = realized + current unrealized equity; MOIC = total value / invested. Terminal fair value is included once for dated IRR and is not a realized distribution.',10)
    narrative(ws,12,'Valuation bridge','Common equity = max(0, illustrative enterprise value − illustrative gross debt + illustrative cash); sponsor equity = common equity × ownership. Cash flows are already sponsor amounts; do not apply ownership twice.',10)
    narrative(ws,13,'IRR method','ACT/365: solve sum(CF / (1+r)^(days/365)) = 0. Log-rate bracketing/bisection; same-day netting. Only one negative-to-positive sign change certifies uniqueness. Non-conventional/undefined results are unavailable. No fees, carry, LP accounting or net returns.',10)
    narrative(ws,14,'Ledger provenance','demo_investments/ledger.json · schema illustrative-investments-1.0 · SHA-256 '+investments[0].ledger_sha256+' · Not a company workbook source.',10)

    def schedule(start,flows,rate,label):
        narrative(ws,start,'Dated return schedule',label+' · Terminal value is unrealized, not a cash distribution. PV columns use the full-precision stored gross IRR; the headline display is rounded.',10)
        headers(ws,start+1,['Date','Company / investment','Cash-flow type','Signed sponsor USD','Actual days','Days / 365','Discount factor','Signed present value','Description','Calculation definition'])
        origin=min(f.date for name,f in flows);pvs=[]
        for row,(name,f) in enumerate(sorted(flows,key=lambda item:item[1].date),start+2):
            days=(f.date-origin).days;years=days/365
            factor=(1+rate)**(-years) if rate is not None else None
            pv=f.amount*factor if factor is not None else None
            if pv is not None:pvs.append(pv)
            row_values(ws,row,[f.date,name,f.kind,f.amount,days,years,factor,pv,f.description,'PV = signed amount × (1 + full-precision stored IRR)^(-actual days / 365)'],56)
            ws.cell(row,1).number_format='yyyy-mm-dd';ws.cell(row,1).alignment=Alignment(horizontal='center',vertical='top')
            for col in (2,3,9,10):ws.cell(row,col).alignment=Alignment(horizontal='left',vertical='top',wrap_text=True,indent=1)
            ws.cell(row,4).number_format=MONEY;ws.cell(row,6).number_format='0.000000';ws.cell(row,7).number_format='0.000000000';ws.cell(row,8).number_format='#,##0.000000;[Red](#,##0.000000)'
        end=start+2+len(flows)
        row_values(ws,end,['NPV residual at displayed IRR','','','','','','',math.fsum(pvs) if rate is not None else None,'Approximately zero when a finite IRR is available','Supporting values are computed snapshots; no live worksheet formulas.'],48)
        ws.cell(end,8).number_format='0.000000;[Red](0.000000)'
        return end+3

    cursor=schedule(17,[(i.company_name,f) for i in investments for f in i.return_cash_flows],portfolio['gross_irr'],'Combined portfolio flows; this is not an average of company returns')
    starts={}
    for investment in investments:
        start=cursor;starts[investment.company_id]=start;summary=investment_summary([investment])
        narrative(ws,start,'Company investment',investment.company_name+' · '+investment.investment_id,10)
        link(ws.cell(start,2),COMPANY_SHEETS[investment.company_id],1)
        narrative(ws,start+1,'Fictional sponsor / fund',investment.sponsor+' · '+investment.fund+' · '+investment.asset_class+' · '+investment.sector,10)
        headers(ws,start+3,['Enterprise value','Gross debt','Cash','Total common equity','Ownership','Current sponsor equity','Valuation date','Investment date','Status','Provenance'])
        row_values(ws,start+4,[investment.enterprise_value,investment.gross_debt,investment.cash,investment.total_common_equity,investment.ownership,investment.current_equity_value,investment.valuation_date,investment.investment_date,investment.status,'Synthetic illustrative assumption'],58)
        for col in (1,2,3,4,6):ws.cell(start+4,col).number_format=MONEY
        ws.cell(start+4,5).number_format=PERCENT
        for col in (7,8):ws.cell(start+4,col).number_format='yyyy-mm-dd'
        narrative(ws,start+6,'Valuation assumptions',investment.assumptions,10)
        narrative(ws,start+7,'Gross return result',f'Invested USD {summary["invested_capital"]:,.0f}; realized {summary["realized_proceeds"]:,.0f}; unrealized {summary["current_equity_value"]:,.0f}; MOIC {summary["gross_moic"]:.6f}x; IRR '+(f'{summary["gross_irr"]:.10%}' if summary['gross_irr'] is not None else 'Unavailable')+'. '+summary['irr_detail'],10)
        cursor=schedule(start+9,[(investment.investment_id,f) for f in investment.return_cash_flows],summary['gross_irr'],investment.company_name)
    for row,i in enumerate(investments,6):link(ws.cell(row,10),'Investment Ledger',starts[i.company_id],'Open investment →')
    ws.freeze_panes='B6';ws.auto_filter.ref='A5:J9'

    # Extend existing comparison without moving its operating rows or evidence links.
    matrix=wb['Company Comparison']
    narrative(matrix,22,'Investment section',NOTICE+' · Valuation date 2026-09-30 · '+METHOD,2+len(companies))
    for row,(label,key) in enumerate([('Illustrative invested capital','invested_capital'),('Illustrative current sponsor equity','current_equity_value'),('Illustrative realized proceeds','realized_proceeds'),('Illustrative gross MOIC','gross_moic'),('Illustrative gross IRR','gross_irr')],24):
        row_values(matrix,row,[label,'Synthetic illustrative USD' if key not in ('gross_moic','gross_irr') else 'Gross sponsor return'],38)
        for col,i in enumerate(investments,3):
            cell=literal(matrix,row,col,investment_summary([i])[key]);cell.number_format='0.00%' if key=='gross_irr' else ('0.00"x"' if key=='gross_moic' else MONEY)
            link(cell,'Investment Ledger',starts[i.company_id])
    for i in investments:
        company=wb[COMPANY_SHEETS[i.company_id]];row=company.max_row+3
        narrative(company,row,'Illustrative investment',NOTICE,6)
        summary=investment_summary([i])
        narrative(company,row+1,'Sponsor return snapshot',f'As of {i.valuation_date}: invested USD {summary["invested_capital"]:,.0f}; realized {summary["realized_proceeds"]:,.0f}; current equity {summary["current_equity_value"]:,.0f}; MOIC {summary["gross_moic"]:.2f}x; gross IRR '+(f'{summary["gross_irr"]:.2%}' if summary['gross_irr'] is not None else 'Unavailable')+'. Open for assumptions and dated cash flows.',6)
        link(company.cell(row+1,2),'Investment Ledger',starts[i.company_id])

    overview=wb['Portfolio Overview']
    narrative(overview,48,'Illustrative investments',NOTICE+' · Common valuation date 2026-09-30',12)
    headers(overview,50,['Company','Invested capital','Realized proceeds','Current sponsor equity','Total value','Gross MOIC','Gross IRR','Valuation date','IRR status','Ledger details'])
    for row,(name,summary) in enumerate([(i.company_name,investment_summary([i])) for i in investments]+[('Portfolio',portfolio)],51):
        row_values(overview,row,[name]+[summary[k] for k in ('invested_capital','realized_proceeds','current_equity_value','total_value','gross_moic','gross_irr','valuation_date')]+[summary['irr_status'],'Open investment ledger →'],62)
        for col in range(2,6):overview.cell(row,col).number_format=MONEY
        overview.cell(row,6).number_format='0.00"x"';overview.cell(row,7).number_format='0.00%'
        link(overview.cell(row,10),'Investment Ledger',5)
    narrative(overview,57,'Return scope',METHOD+' · Portfolio ratios are recomputed from combined underlying cash flows, not averaged company ratios.',12)
    overview.print_area='A1:L59'
