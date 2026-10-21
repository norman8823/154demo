"""Deterministic, separate synthetic sponsor ledger. No operating-data imports.

XIRR solves sum(CF_i / (1+r)**((date_i-date_0).days/365)) = 0.
Only conventional investment schedules (negative flows followed by positive
flows, after same-day netting) receive a certified unique root. Other schedules
remain unavailable: a Newton guess must not choose silently among possible IRRs.
"""
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import hashlib
import json
import math
import re

LEDGER_PATH = Path(__file__).resolve().parent/'demo_investments/ledger.json'
NOTICE = 'SYNTHETIC ILLUSTRATIVE DATA · Fictional sponsor investments; not 154 Partners holdings or returns. Separate from verified operating financials.'
METHOD = 'Gross sponsor returns · ACT/365 dated cash flows · before fees, carry and fund expenses · no net fund or LP returns'


@dataclass(frozen=True)
class CashFlow:
    date: date
    amount: float
    kind: str
    description: str = ''


@dataclass(frozen=True)
class IRRResult:
    rate: float | None
    status: str
    detail: str


@dataclass(frozen=True)
class Investment:
    investment_id: str
    company_id: str
    company_name: str
    sector: str
    sponsor: str
    fund: str
    asset_class: str
    investment_date: date
    valuation_date: date
    status: str
    currency: str
    ownership: float
    enterprise_value: float
    gross_debt: float
    cash: float
    assumptions: str
    cash_flows: tuple[CashFlow, ...]
    ledger_sha256: str

    @property
    def total_common_equity(self):
        return max(0., self.enterprise_value-self.gross_debt+self.cash)

    @property
    def current_equity_value(self):
        return self.total_common_equity*self.ownership

    @property
    def return_cash_flows(self):
        return self.cash_flows+(CashFlow(self.valuation_date,self.current_equity_value,'terminal_value','Unrealized sponsor equity; not a cash distribution'),)


def _date(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        raise ValueError('Ledger dates must be ISO calendar dates.')
    return date.fromisoformat(value)


def _number(value, name, positive=False):
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or value<0 or (positive and value==0):
        raise ValueError('Invalid ledger '+name)
    return float(value)


def load_investments(path=LEDGER_PATH):
    raw=Path(path).read_bytes();data=json.loads(raw)
    if data['schema_version']!='illustrative-investments-1.0' or data['provenance']!='synthetic_illustrative' or data['currency']!='USD':
        raise ValueError('Unsupported synthetic investment ledger contract.')
    valuation=_date(data['valuation_date']);investments=[];ids=set();companies=set()
    for row in data['investments']:
        company=row['company_id'];identity=row['investment_id'];start=_date(row['investment_date'])
        if identity in ids or company in companies or start>valuation:raise ValueError('Duplicate investment/company or future investment date.')
        ids.add(identity);companies.add(company)
        ownership=_number(row['ownership'],'ownership',positive=True)
        if ownership>1:raise ValueError('Ownership must be in (0,1].')
        flows=[]
        for f in row['cash_flows']:
            day=_date(f['date']);amount=f['amount'];kind=f['kind']
            if not start<=day<=valuation:raise ValueError('A ledger cash flow falls outside the investment/valuation dates.')
            magnitude=_number(abs(amount) if isinstance(amount,(float,int)) and not isinstance(amount,bool) else amount,'cash flow',positive=True)
            if kind not in ('contribution','distribution') or (kind=='contribution' and amount>=0) or (kind=='distribution' and amount<=0):
                raise ValueError('Contribution signs must be negative; distribution signs positive.')
            flows.append(CashFlow(day,-magnitude if kind=='contribution' else magnitude,kind,f['description']))
        flows=tuple(sorted(flows,key=lambda f:f.date))
        if not flows or flows[0].date!=start or flows[0].kind!='contribution':raise ValueError('Initial sponsor contribution must establish the investment date.')
        investments.append(Investment(identity,company,row['company_name'],row['sector'],data['sponsor'],data['fund'],data['asset_class'],start,valuation,row['status'],data['currency'],ownership,
                                      _number(row['enterprise_value'],'enterprise value'),_number(row['gross_debt'],'gross debt'),_number(row['cash'],'cash'),row['valuation_assumptions'],flows,hashlib.sha256(raw).hexdigest()))
    if companies!={'summit','tallis','harrow'}:raise ValueError('Ledger must cover the three registered fictional companies exactly.')
    return tuple(investments)


def xirr(flows):
    """Bracket/bisect log(1+r); no guess-dependent root selection or dependencies."""
    groups={}
    for f in flows:
        if not isinstance(f.date,date) or isinstance(f.amount,bool) or not math.isfinite(f.amount):raise ValueError('Invalid dated return cash flow.')
        groups.setdefault(f.date,[]).append(f.amount)
    rows=[(day,math.fsum(amounts)) for day,amounts in sorted(groups.items()) if math.fsum(amounts)!=0]
    if len(rows)<2:return IRRResult(None,'unavailable','At least two distinct nonzero cash-flow dates are required.')
    if not any(a<0 for _,a in rows) or not any(a>0 for _,a in rows):return IRRResult(None,'unavailable','Both negative and positive cash flows are required; a complete loss has no finite IRR.')
    changes=sum((a<0)!=(b<0) for (_,a),(_,b) in zip(rows,rows[1:]))
    if changes!=1 or rows[0][1]>=0:
        return IRRResult(None,'uniqueness_not_certified','Non-conventional signs after same-day netting: multiple or no IRRs may exist. No rate is selected.')
    norm=max(abs(a) for _,a in rows);start=rows[0][0]
    values=[((day-start).days/365,amount/norm) for day,amount in rows]
    def npv_sign(log_rate):
        exponents=[-years*log_rate for years,_ in values];shift=max(exponents)
        return math.fsum(amount*math.exp(exponent-shift) for (_,amount),exponent in zip(values,exponents))
    low,high=math.log(1e-12),math.log1p(1e6)
    if npv_sign(low)<=0 or npv_sign(high)>=0:return IRRResult(None,'unavailable','Unique root is outside supported rates (-1+1e-12, 1,000,000).')
    for _ in range(220):
        mid=(low+high)/2
        if npv_sign(mid)>0:low=mid
        else:high=mid
        if high-low<1e-14:break
    return IRRResult(math.expm1((low+high)/2),'unique','Conventional investment signs; unique root bracketed and bisected using actual days / 365.')


def investment_summary(investments):
    """Portfolio MOIC and IRR use underlying dollars/dates, never company averages."""
    investments=tuple(investments)
    if len({i.company_id for i in investments})!=len(investments):raise ValueError('Duplicate investment in return aggregation.')
    if len({(i.currency,i.valuation_date) for i in investments})>1:raise ValueError('A common currency and valuation date are required.')
    paid=math.fsum(-f.amount for i in investments for f in i.cash_flows if f.kind=='contribution')
    realized=math.fsum(f.amount for i in investments for f in i.cash_flows if f.kind=='distribution')
    unrealized=math.fsum(i.current_equity_value for i in investments)
    irr=xirr([f for i in investments for f in i.return_cash_flows])
    return dict(invested_capital=paid,realized_proceeds=realized,current_equity_value=unrealized,total_value=realized+unrealized,
                gross_moic=(realized+unrealized)/paid if paid else None,gross_irr=irr.rate,irr_status=irr.status,irr_detail=irr.detail,
                valuation_date=investments[0].valuation_date.isoformat() if investments else None,currency=investments[0].currency if investments else 'USD')
