"""Editorial demo outlooks over existing ledger/results; never analyst inference.

This presentation is separate from approved findings. References identify the
accepted finding groups used in the editorial judgment; no new causes or
calculations are introduced.
"""
from dataclasses import dataclass
from datetime import date
from html import escape
from portfolio_comparison import comparison,money
from portfolio_investments import investments_for,investment_summary


@dataclass(frozen=True)
class Outlook:
    headline: str
    paragraphs: tuple[str,...]
    finding_ids: tuple[int,...]
    ledger_sha256: str


def investment_outlook(company):
    investment=investments_for([company])[0]
    result=investment_summary([investment]);operating=comparison(company)
    moic=f'{result["gross_moic"]:.2f}x';irr=f'{result["gross_irr"]:.2%}'
    equity=money(result['current_equity_value'])
    valuation=date.fromisoformat(result['valuation_date']).strftime('%B %d, %Y')
    shortfall=f'{abs(operating["ebitda"].variance_pct):.1%}'
    period=operating['period_label'].replace(' · ',' ')
    if company.id=='summit':
        headline='Strong illustrative returns; margins and collections need attention'
        paragraphs=(
            f'Summit shows strong illustrative sponsor returns: {moic} gross MOIC, {irr} gross IRR and {equity} of current equity value as of {valuation}. These synthetic ledger values are separate from the verified operating review. {period} reported EBITDA was {shortfall} below budget; attractive investment marks sit alongside current operating pressure.',
            'Margin pressure, aging receivables and weaker renewals are the principal concerns in the accepted findings. Management should prioritize a documented margin recovery bridge, subsequent cash collections and retention cohorts, while reconciling branch and consolidated EBITDA. The available evidence does not establish the causes or durability of a recovery.')
        ids=(10000,10001,10002,10004)
    elif company.id=='tallis':
        headline='Below-cost investment requires a substantiated operating recovery'
        paragraphs=(
            f'Tallis is a below-cost illustrative investment: {moic} gross MOIC, {irr} gross IRR and {equity} of current equity value as of {valuation}. These synthetic sponsor marks are distinct from the verified operating results. {period} reported EBITDA was {shortfall} below budget; the accepted review also identifies a substantial YTD earnings shortfall.',
            'The investment case needs an evidenced operational recovery. Unverified EBITDA adjustments, prospective compensation savings, aged WIP and client retention gaps limit confidence. Management should reconcile the earnings variance, substantiate adjustments and demonstrate billing, collections and retention progress. The package does not establish how much of the shortfall is recoverable.')
        ids=(10000,10001,10002,10003)
    elif company.id=='harrow':
        headline='Positive illustrative returns face cash and capital demands'
        paragraphs=(
            f'Harrow has positive illustrative sponsor returns of {moic} gross MOIC and {irr} gross IRR, with {equity} of current equity value as of {valuation}. The ledger is synthetic; the verified {period} operating results show reported EBITDA {shortfall} below budget.',
            'Cash conversion, scheduled principal payments and fleet investment needs temper the outlook. South territory disruption and major-account renewal exposure warrant attention, while North\'s listed wins remain a qualified opportunity. Management should reconcile cash available after obligations, separate cash capex from noncash lease additions, and verify recovery and renewal assumptions. Reported EBITDA and cash should anchor follow-up until proposed adjustments are substantiated.')
        ids=(10000,10001,10002,10003,10004,10006)
    else:
        raise ValueError('No reviewed editorial outlook is available for this company.')
    accepted={f['id'] for f in company.review.package['ai_insights']}
    if not set(ids)<=accepted:raise ValueError('An outlook supporting finding is unavailable.')
    return Outlook(headline,paragraphs,ids,investment.ledger_sha256)


def render_outlook(company):
    import streamlit as st
    value=investment_outlook(company)
    def safe(text):return escape(text).replace('$','&#36;')
    st.subheader('Investment Outlook')
    st.markdown('<section class="investment-outlook" data-company="'+safe(company.id)+'"><h3>'+safe(value.headline)+'</h3>'+''.join('<p>'+safe(p)+'</p>' for p in value.paragraphs)+'<small>Editorial outlook for the synthetic demo · Gross sponsor returns before fees, carry and fund expenses. Operating observations remain source-backed.</small></section>',unsafe_allow_html=True)
