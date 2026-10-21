# Synthetic investment ledger and return conventions

`demo_investments/ledger.json` is a separate, versioned set of **synthetic illustrative data**. The sponsor, fund, investment histories, enterprise values, debt, cash and ownership assumptions are fictional. They do not describe 154 Partners or any real fund and are not supported by the company operating workbooks. All marks are post-distribution illustrative values as of September 30, 2026, in USD.

| Company | Sponsor paid-in | Realized proceeds | Current sponsor equity | Gross MOIC | Gross IRR |
| --- | ---: | ---: | ---: | ---: | ---: |
| Summit Home Services | $12m | $3m | $27m | 2.50x | 21.77% |
| Tallis Brook Accounting | $21m | $0 | $15m | 0.71x | -9.54% |
| Harrow Ridge Environmental | $25m | $2m | $40m | 1.68x | 13.80% |
| Portfolio | $58m | $5m | $82m | 1.50x | 10.95% |

The underlying records expose dates, contributions, distributions and the independent valuation assumptions. Total company common equity is `max(0, enterprise value − gross debt + cash)`; current sponsor equity equals that amount times ownership. Sponsor cash flows already reflect the sponsor's interest and are not scaled by ownership again. All common equity is assumed pari passu; no preferred claims, transaction costs, tax or liquidation discount is modeled.

Contributions are negative; realized distributions are positive. Invested capital is the absolute sum of contributions. Realized proceeds are the sum of distributions. Total value is realized proceeds plus current unrealized sponsor equity. Gross MOIC is total value divided by paid-in capital. Terminal unrealized equity is added exactly once on the valuation date for IRR; it is not a cash distribution.

Gross IRR solves `sum(CF_i / (1+r)^((date_i − first_date).days / 365)) = 0`. The [ACT/365 dated-cash-flow convention](https://support.microsoft.com/en-us/excel/functions/xirr-function) matches the XIRR definition. The implementation brackets and bisects `log(1+r)` with scaled exponentials to avoid overflow, without a guess-dependent Newton root. Inputs are sorted, same-day flows are netted and zero net dates removed. Only conventional investment schedules with one negative-to-positive sign change receive a certified unique root. Non-conventional signs are labeled `uniqueness_not_certified`, because multiple or no IRRs may exist; no arbitrary rate is displayed. Missing positive/negative flows, no distinct dates, or a root outside `(-1+1e-12, 1,000,000)` are explicitly unavailable. A complete loss has no finite IRR.

Portfolio MOIC uses aggregate dollars. Portfolio IRR is recomputed from all underlying dated sponsor cash flows and terminal values, after same-day netting. Neither metric averages company ratios. A common valuation date and currency are required; duplicate holdings are refused.

These are gross investment returns before management fees, carried interest and fund expenses. No net fund or LP return, waterfall or accounting system is implied. The operating Review snapshots, analyst calculations, financial definitions and source verification remain unchanged.

Tests independently reconstruct cash flows from the JSON and use high-precision Decimal direct-rate NPV fixtures, plus Microsoft's irregular-date XIRR example, a leap-year case, known multiple roots, negative returns, signs, dates, ownership, aggregation and enterprise-to-equity reconciliation.
