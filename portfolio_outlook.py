"""Business-led demo editorial views; approved findings and ledger remain separate."""
from dataclasses import dataclass
from html import escape
from portfolio_investments import investments_for

SECTIONS=(
    ('Business Overview','Illustrative business context'),
    ("What's Working",'Reported indicators · Illustrative investment context'),
    ("What's Under Pressure",'Source-backed operating review'),
    ('Operational Priorities','Proposed initiatives · Not established causes'),
)


@dataclass(frozen=True)
class Outlook:
    headline: str
    paragraphs: tuple[str,...]
    finding_ids: tuple[int,...]
    ledger_sha256: str


def investment_outlook(company):
    investment=investments_for([company])[0]
    if company.id=='summit':
        headline='Strong illustrative returns need service and installation discipline'
        paragraphs=(
            'Summit’s reported services span residential HVAC and plumbing repairs, replacement installations and maintenance agreements. In this illustrative business model, homeowners and selected builder accounts are served through local branches; value depends on productive technician time, installation contribution and recurring service relationships.',
            'The illustrative sponsor ledger shows value above cost and positive gross returns. Reported ticket and backlog growth offer an opportunity to turn demand into completed work; larger tickets may reflect price or job mix rather than improved service-call productivity.',
            'The September monthly review shows EBITDA below budget, alongside YTD margin and equipment-cost pressure. Lakeshore’s callbacks and utilization, weakening maintenance renewals and aged receivables challenge the earnings-to-cash story. Weather and staffing explanations do not establish the causes of the full shortfall; branch reporting differences also limit performance attribution.',
            'Test technician scheduling against completed calls and repeat visits; review replacement installation margins and equipment procurement by job type. Assign owners for maintenance agreement renewals and past-due collections, and reconcile branch results before allocating recovery targets. These are proposed management initiatives, not verified explanations of the earnings miss.')
        ids=(10000,10001,10002,10003,10004)
    elif company.id=='tallis':
        headline='A below-cost investment needs better engagement economics and cash delivery'
        paragraphs=(
            'Tallis provides tax, accounting, audit and advisory services. In this illustrative business model, business owners, trusts and individual clients buy professional time, recurring compliance work and selected advisory projects; returns depend on billable utilization, realization and durable partner-led client relationships.',
            'Legacy September revenue growth is a favorable single-month indicator. The range of services creates a potential opportunity to deepen client relationships, but cross-selling and sustained organic growth have not been demonstrated. Those opportunities matter because the illustrative investment remains below cost, with a negative gross IRR.',
            'The September monthly review and YTD earnings comparison both miss plan. Partner-compensation pressure, Redfern’s weak realization and aged work-in-progress, and Ashcombe’s retention gap put recovery at risk. Acquisition effects cloud growth comparisons, while prospective compensation savings do not establish realized earnings or a dependable recovery run rate.',
            'Review engagement staffing and billing: compare billable utilization with realization, clear aged work-in-progress and assign collection owners. Test fixed-fee job economics before repricing, align partner compensation with evidenced performance, and review at-risk client relationships. Treat cross-selling and prospective savings as initiatives to validate, not committed earnings.')
        ids=(10000,10001,10002,10003,10004)
    elif company.id=='harrow':
        headline='Positive illustrative returns need reliable fleet capacity and cash conversion'
        paragraphs=(
            'Harrow’s reported activities include commercial collection, roll-off and industrial work, recycling and processing. The illustrative business model serves commercial and industrial customers through trucks, routes and customer contracts; economics depend on route density, fleet utilization, disposal costs and disciplined asset replacement.',
            'North’s higher tons per route-day is an observed physical productivity improvement, and the illustrative ledger shows positive investment returns. Listed contract wins offer potential growth, but their commencement, retention and cash contribution remain unverified. Route-density gains or benefits from routing software have not been established.',
            'FY2026 annual EBITDA missed budget despite revenue growth. South’s downtime and rental needs, weaker cash conversion after obligations and capital requirements temper the investment case. Major-account contract renewals and East’s disposal-cost pressure require attention. Rental and commodity adjustments should not substitute for demonstrated operating improvement.',
            'Prioritize maintenance triage and measure completed repairs against availability, rentals and truck utilization. Test route density and service profitability before adding capacity; sequence capital spending against cash available after debt obligations. Prepare account-specific renewal plans and validate new-contract start dates, service costs and realized contribution.')
        ids=(10000,10001,10002,10003,10004,10005,10006)
    else:
        raise ValueError('No reviewed editorial outlook is available for this company.')
    accepted={f['id'] for f in company.review.package['ai_insights']}
    if not set(ids)<=accepted:raise ValueError('An outlook supporting finding is unavailable.')
    return Outlook(headline,paragraphs,ids,investment.ledger_sha256)


def render_outlook(company, *, compact=False):
    import streamlit as st
    value=investment_outlook(company)
    def safe(text):return escape(text).replace('$','&#36;')
    # Phones add business context once; the unchanged prepared assessment below
    # already carries the detailed risks, conclusions and management actions.
    indices=(0,) if compact else range(len(SECTIONS))
    sections=''.join('<div class="outlook-section"><h4>'+safe(SECTIONS[i][0])+'</h4><small>'+safe(SECTIONS[i][1])+'</small><p>'+safe(value.paragraphs[i])+'</p></div>' for i in indices)
    note=('Illustrative business context. Source-backed conclusions and management follow-up appear in the assessment below.' if compact else
          'Editorial view for the synthetic demo. Business context and proposed initiatives are illustrative; operating observations come from the accepted review. Sponsor returns are illustrative and gross of fees and carry.')
    st.subheader('Investment Outlook')
    st.markdown('<section class="investment-outlook" data-company="'+safe(company.id)+'" data-compact="'+str(compact).lower()+'"><h3>'+safe(value.headline)+'</h3><div class="outlook-sections">'+sections+'</div><small class="outlook-note">'+safe(note)+'</small></section>',unsafe_allow_html=True)
