from datetime import date
from decimal import Decimal, localcontext
from dataclasses import replace
import json
import math
import pytest
from portfolio_investments import CashFlow, LEDGER_PATH, load_investments, investment_summary, xirr


def cf(day, amount):
    return CashFlow(date.fromisoformat(day),amount,'fixture')


def decimal_fixture(flows):
    """Independent direct-rate/Decimal NPV fixture, not the scaled log solver."""
    with localcontext() as context:
        context.prec=48
        start=min(d for d,a in flows);lo=Decimal('-.99');hi=Decimal('2')
        def npv(r):
            return sum(Decimal(str(a))/(1+r)**(Decimal((d-start).days)/365) for d,a in flows)
        assert npv(lo)>0 and npv(hi)<0
        for _ in range(180):
            mid=(lo+hi)/2
            if npv(mid)>0:lo=mid
            else:hi=mid
        return float((lo+hi)/2)


def test_ledger_values_reconcile_and_returns_match_independent_decimal_fixtures():
    investments=load_investments();all_flows=[]
    expected={'summit':(12000000,3000000,27000000,2.5),'tallis':(21000000,0,15000000,15/21),'harrow':(25000000,2000000,40000000,1.68)}
    raw=json.loads(LEDGER_PATH.read_text())
    for investment,row in zip(investments,raw['investments']):
        result=investment_summary([investment]);paid,realized,equity,moic=expected[investment.company_id]
        assert result['invested_capital']==paid
        assert result['realized_proceeds']==realized
        assert result['current_equity_value']==equity
        assert result['total_value']==realized+equity
        assert result['gross_moic']==pytest.approx(moic)
        # Build fixture inputs directly from JSON, independent of dataclass methods.
        terminal=max(0,row['enterprise_value']-row['gross_debt']+row['cash'])*row['ownership']
        flows=[(date.fromisoformat(f['date']),f['amount']) for f in row['cash_flows']]+[(date(2026,9,30),terminal)]
        assert result['gross_irr']==pytest.approx(decimal_fixture(flows),abs=2e-13)
        assert result['irr_status']=='unique'
        all_flows.extend(flows)
    portfolio=investment_summary(investments)
    assert [portfolio[k] for k in ('invested_capital','realized_proceeds','current_equity_value','total_value','gross_moic')]==[58000000,5000000,82000000,87000000,1.5]
    assert portfolio['gross_irr']==pytest.approx(decimal_fixture(all_flows),abs=2e-13)
    assert portfolio['gross_irr']!=pytest.approx(sum(investment_summary([i])['gross_irr'] for i in investments)/3)
    assert portfolio['gross_moic']!=pytest.approx(sum(investment_summary([i])['gross_moic'] for i in investments)/3)


def test_irregular_dates_leap_year_and_microsoft_xirr_example():
    flows=[cf('2008-01-01',-10000),cf('2008-03-01',2750),cf('2008-10-30',4250),cf('2009-02-15',3250),cf('2009-04-01',2750)]
    assert xirr(flows).rate==pytest.approx(.373362535,abs=1e-8)
    # 366 days must not silently become one year.
    result=xirr([cf('2023-09-30',-100),cf('2024-09-30',110)])
    assert result.rate==pytest.approx(1.1**(365/366)-1,abs=1e-13)
    assert xirr(list(reversed(flows))).rate==pytest.approx(xirr(flows).rate)
    assert xirr([cf('2021-01-01',-60),cf('2021-01-01',-40),cf('2022-01-01',120)]).rate==pytest.approx(.2)


def test_nonunique_unavailable_and_invalid_cash_flows_are_explicit():
    # Known annual roots 10% and 20%; neither may be silently selected.
    multi=xirr([cf('2021-01-01',-100),cf('2022-01-01',230),cf('2023-01-01',-132)])
    assert multi.rate is None and multi.status=='uniqueness_not_certified'
    for flows in [[],[cf('2021-01-01',-100)],[cf('2021-01-01',-100),cf('2022-01-01',0)],[cf('2021-01-01',-100),cf('2021-01-01',110)]]:
        assert xirr(flows).rate is None
    with pytest.raises(ValueError):xirr([cf('2021-01-01',float('nan'))])
    i=load_investments()[0]
    assert replace(i,gross_debt=1e9).current_equity_value==0
    with pytest.raises(ValueError):investment_summary([i,i])
    with pytest.raises(ValueError):investment_summary([i,replace(load_investments()[1],valuation_date=date(2026,8,31))])


@pytest.mark.parametrize('change', ['sign','future','ownership','duplicate','currency','nan'])
def test_ledger_contract_rejects_invalid_inputs(tmp_path,change):
    data=json.loads(LEDGER_PATH.read_text())
    if change=='sign':data['investments'][0]['cash_flows'][0]['amount']=100
    if change=='future':data['investments'][0]['cash_flows'][0]['date']='2027-01-01'
    if change=='ownership':data['investments'][0]['ownership']=1.1
    if change=='duplicate':data['investments'][1]['company_id']='summit'
    if change=='currency':data['currency']='EUR'
    if change=='nan':data['investments'][0]['cash']=float('nan')
    path=tmp_path/'ledger.json';path.write_text(json.dumps(data))
    with pytest.raises(ValueError):load_investments(path)
