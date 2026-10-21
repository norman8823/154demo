# Portfolio Intelligence v3 — morning handoff

V3 adds gross sponsor investment performance and a portable operating-data handoff to the existing prepared-analysis workflow. The three original company Reviews, findings, source verification and company reports remain unchanged. Everything is synthetic demo data; investment assumptions have their own clearly separate provenance.

## Five-minute inspection

1. Open **http://127.0.0.1:8502**. The four headline cards show illustrative current sponsor equity, gross MOIC, gross IRR and paid-in capital. Expand the optional investment-value chart; the holdings table shows company returns beside separately labeled operating figures.
2. Open **Data Foundation**. Inspect the normalized preview and the distinction between checked source values, automatic acceptance, unresolved mappings and absent human approval. Download the ZIP, extract it and run `python3 example_consumer.py` from that directory. The output is a separate, period-aware three-company financial comparison.
3. Open Tallis through Company Detail. Expand its synthetic investment section: it is below cost, with a negative gross IRR. Switch companies using the selector, then inspect the original Investment Summary, findings and Management Questions.
4. Open **Investment Issues**, choose a material issue and follow its original evidence. The 17 accepted findings remain grouped 5 Summit / 5 Tallis / 7 Harrow. Preserve the distinction between a headline monthly period and an issue's YTD/LTM or other scope.
5. Download the GP workbook. Review the separate **Investment Ledger**, valuation bridges and dated cash-flow/PV schedules. Follow an Investment Issue → Source References → included original source cell, or a derived calculation's individual operands. Company Comparison's Tallis budget revenue/EBITDA links still end at Practice P&L I12/I41 through the correct budget provenance.

The demonstrated sequence is: **Messy Excel → Verified normalized data → Reusable data package → Prepared AI investment analysis → Portfolio performance and issues → Source-linked Excel handoff.** The analysis stage reuses the committed approved results; viewing/exporting does not run a new analyst model.

## Synthetic investment results

All figures below are **synthetic illustrative USD sponsor investment data**, as of **September 30, 2026**. The fictional sponsor/fund and valuations do not describe 154 Partners or any real holdings. They are not supported by the operating workbooks.

| Company | Invested | Realized | Current equity | Total value | Gross MOIC | Gross IRR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Summit Home Services | $12m | $3m | $27m | $30m | 2.50x | 21.77% |
| Tallis Brook Accounting | $21m | $0 | $15m | $15m | 0.71x | -9.54% |
| Harrow Ridge Environmental | $25m | $2m | $40m | $42m | 1.68x | 13.80% |
| Portfolio | **$58m** | **$5m** | **$82m** | **$87m** | **1.50x** | **10.95%** |

The versioned input contract is [demo_investments/ledger.json](../demo_investments/ledger.json). It exposes dates, signed sponsor contributions/distributions, ownership, enterprise value, gross debt, cash, investment status and assumptions. Summit is a mature positive holding with partial realizations; Tallis is below cost after follow-on funding; Harrow has a moderate positive outcome.

Company common equity is `max(0, enterprise value − gross debt + cash)`; sponsor equity is common equity times ownership. The illustrative bridges are Summit $52m − $20m + $1.75m = $33.75m × 80%; Tallis $47m − $28m + $1m = $20m × 75%; Harrow $110m − $50m + $4m = $64m × 62.5%. These are independent scenario assumptions, not reported debt/cash balances or EBITDA-based analyst valuations. Sponsor flows are already ownership-specific and are not multiplied by ownership again.

Contributions are negative, distributions positive. Current unrealized sponsor equity is added exactly once on the valuation date for IRR, and is never counted as realized proceeds. Portfolio MOIC is aggregate total value / paid-in capital. Portfolio IRR solves the combined underlying dated cash flows and terminal values; neither metric averages company ratios.

XIRR uses ACT/365 and brackets/bisects `log(1+r)`, with same-day netting and scaled exponentials. Only conventional investment signs receive a certified unique rate. Non-conventional schedules report `uniqueness_not_certified`; missing signs, no distinct dates, complete losses without positive proceeds, or out-of-range roots remain explicitly unavailable. See [return methodology and limitations](gp-v3-investments.md). Returns are gross before fees, carry and fund expenses; no net fund or LP return is calculated.

## Reusable AI-ready operating data

The Data Foundation page exports these six files:

| File | Purpose |
| --- | --- |
| `financial_facts.csv` | 1,002 retained normalized observations, with canonical category IDs, entity/role, period/grain/scenario, value/unit/currency/basis, source IDs and verification/approval distinctions |
| `metric_definitions.json` | Schema `operating-data-1.0`, metric/field definitions, enums and scale/sign/selection conventions |
| `source_lineage.csv` | 1,002 matching lineage records: original aliases, retained observed-fact IDs, workbook/sheet/cell/header references, original values/formula provenance, workbook and snapshot hashes |
| `quality_report.json` | Checked-source results, blank/unresolved observations, original limitations, approval distinctions and content hashes |
| `example_consumer.py` | Standalone standard-library comparison, with package hash validation and no application or workbook dependencies |
| `README.md` | Schema usage, field semantics, qualifications and reuse boundaries |

There are **996 checked numeric observations, six blanks and 204 observation rows with unresolved mappings**. These are row counts, not counts of distinct source accounts. All unresolved mappings are retained; none is silently accepted by this feature. Human mapping approval is **`not_recorded`** throughout, with **zero asserted human-approved mappings**. Approval of a prepared demo checkpoint is not evidence of human sign-off on every mapping or narrative conclusion.

The export reads existing normalized Review contracts and retained checked source facts. It performs no new raw extraction or reinterpretation. Financial IDs are qualified by stable company ID and approved run; aliases are stable within that version, not guarantees of cross-cycle mapping persistence. Canonical metric IDs name retained categories, not new GAAP definitions. `unmapped.source_observation` is explicitly unstandardized. Unknown basis and the original `$`/`USD` labels remain unchanged; no FX conversion is inferred.

The 12 `comparison_selected` records are the existing report adapter's current-period revenue/EBITDA actual/budget operands. This avoids summing duplicate dashboard/statement totals, detail or subtotals. The full file also retains history and fiscal-quarter records. The consumer preserves September monthly Summit/Tallis versus annual FY2026 Harrow, and produces no cross-company financial total. The illustrative investment ledger is excluded entirely from this operating-data ZIP.

Independent reuse is proved twice: an extracted-package test runs with `-I -S`, an empty credential environment and audit hooks denying nonstdlib/app imports, Excel reads, out-of-package data access and socket creation; the actual browser-downloaded ZIP's consumer also runs successfully. Both outputs reconcile to verified company comparison records. A downstream engineer needs only the six exported files and Python's standard library.

## Dashboard and workbook

The v2 layout and operating workflow are retained. Four return cards, one optional investment-value chart, return columns and compact company investment details are added. The operating Actual/Budget charts retain independent zero-based company-period axes. The native sortable holdings table places returns first so company outcomes are immediately visible. The Data Foundation preview puts periods, scenarios and values before long definitions.

The GP workbook now has **34 sheets**: the nine v2 review/index/output sheets, a separate **Investment Ledger**, and the same 24 canonical read-only source snapshots. Portfolio Overview and Company Comparison add distinctly labeled investment sections; company sheets link to their ledger assumptions and schedules. The original six company-specific standard/custom downloads remain intact.

The Investment Ledger is a **calculated snapshot, not a live financial model**. Inputs, enterprise/common/sponsor equity bridges, contribution/distribution/terminal rows, actual day counts, year fractions, discount factors and signed PVs are transparent. PVs use the full-precision stored rate; headline displays are rounded. NPV residuals reconcile to approximately zero. Formula definitions are explanatory text; the GP workbook has no active cell formulas or external-workbook relationships. Source snapshot formulas retain observed values and original formula comments as before. All **1,136 native internal XLSX hyperlinks** resolve to existing nonempty targets.

## Verification, review and limits

Validated October 21, 2026:

- Final release regression: **388 passed in 227.86 seconds**. The two earlier integration/presentation runs also passed all 388 tests. The final literal-currency correction passed **9 company/navigation/export tests in 40.53 seconds**; the mobile/data presentation pass additionally passed 8 tests in 15.06 seconds.
- Investment calculations: independent high-precision Decimal direct-rate fixtures, Microsoft's irregular-date XIRR example, leap-year dates, negative returns, known multiple roots, signs/date/ownership checks and company/portfolio reconciliations.
- Actual Chrome: all three company summaries/evidence/return paths, selectors, original finding deep links, 17-finding grouping, six company XLSX exports, GP XLSX and Data ZIP — **eight downloads**. Desktop/mobile have no document overflow; browser exceptions and external requests are zero. Fresh-process final screenshots confirm the corrected mobile chart.
- Data package: every normalized value and lineage record reconciles; schema/hash/approval/blank distinctions and corruption fail-safe checks pass. Isolated consumer audit reports zero workbook reads, socket calls or nonstdlib imports, and no credentials are supplied.
- Spreadsheet renderer: the actual downloaded workbook was rendered by **LibreOffice Calc 26.8.1**. Native charts, ledger totals/PV schedules, comparison and original source sheets were inspected. Its PDF export has 1,090 resolved internal destinations, including 14 into Investment Ledger, with zero broken GoTo destinations. The renderer was a temporary QA tool, not an application dependency.
- One independent substantive read-only review at `62e7dc9` found **no material defects**. Its separate 45-digit Decimal reconstruction gave NPV residuals below $0.000001 for all company/portfolio rates. It verified all 1,136 XLSX links, source/period/scenario selection and approval distinctions. Parent screenshot QA improved holdings visibility, mobile labels and ledger spacing, and corrected Streamlit math interpretation of multiple dollar amounts by reusing the existing literal-currency renderer. Expanded details now show the complete assumptions/cash-flow table and pass zero-KaTeX checks for all three companies. Financial logic did not change.
- All three approved Reviews and the **23 manifest-pinned analytical files** verify unchanged. Current analyst inference is **0 calls / $0**; original historical inference receipts remain provenance. No frozen model, prompt, analytical calculation methodology, source-verification rule, company result or original report exporter changed.
- Precise staging and high-confidence secret-pattern audits exclude credentials, runtime caches/logs, generated workbooks and data ZIPs. Complete local run receipts remain in ignored `artifacts/gp-v3/`.

Remaining boundaries: the ledger is illustrative, not a valuation opinion; gross returns exclude net-fund economics. Unresolved mappings, unknown accounting bases and narrative qualifications still require judgment. First and subsequent reporting cycles are **not fully automated**; persistent analyst-approved mapping reuse has not been built or validated. Interactive Microsoft Excel mouse click-through is not certified in this environment; native Calc rendering/link import and exhaustive XLSX target checks were used. No material implementation blocker remains. No database, API/MCP server, mapping approval system or MLOps pipeline was added.

## Harmony and Git

Canonical parent **#40** has four children. Previous v1/v2 tasks remain Done and were not reopened.

| Card | Work package | Evidence commit |
| --- | --- | --- |
| #41 | V3-01 Synthetic Investment Ledger & Returns | `46d6d78` |
| #42 | V3-02 Dashboard and Excel Integration | `c6be486` |
| #43 | V3-03 AI-Ready Data Foundation | `62e7dc9` |
| #44 | V3-04 Integration, Independent Review & QA | `fb14a68`, `d938cff` plus this rendered-evidence/handoff commit |

Branch: **`feat/portfolio-intelligence-v3`**, created from exact v2 checkpoint `870921e19a7a202c3e325d5118eeec1768e6ede2`. V2, v1 (`0ea827b6f0492871132572196a67d85646ad9760`) and the frozen engine branch (`e59d651944fe786e3b7d50735cfbfe0505990748`) are preserved. No merge or deployment is part of this work. Harmony's connected API exposes card status/evidence, not subscription-token telemetry; no usage totals are invented.

## Preview and restart

From `/Users/norman/main/154demo-portfolio`:

```sh
COPILOT_ENV_FILE='' .venv/bin/python scripts/seed_demo_results.py --verify-only
./scripts/run_portfolio_demo.sh
```

The launcher serves only `127.0.0.1:8502` without loading API credentials. Leave the existing analytical instance on 8501 untouched. Restart after editing imported presentation/exporter modules to refresh the development process and cached workbook.

```sh
.venv/bin/python -m pytest -q
.venv/bin/python tests/browser_portfolio.py
```

The browser check uses local Chrome/Playwright. Reviewable screenshots:

- [Portfolio overview and holdings](images/gp-v3/overview.png)
- [Investment-value chart](images/gp-v3/investment-chart.png)
- [Tallis negative-return investment detail](images/gp-v3/company-investment.png)
- [Data Foundation](images/gp-v3/data-foundation.png)
- [Mobile overview](images/gp-v3/mobile.png), [investment chart](images/gp-v3/mobile-investment-chart.png) and [Data Foundation](images/gp-v3/mobile-data-foundation.png)
- [Excel reporting page](images/gp-v3/excel-preview.png)
- [Native spreadsheet ledger](images/gp-v3/investment-ledger.png) and [original source snapshot](images/gp-v3/source-cell.png)

Local test/browser/consumer/renderer/audit logs, actual downloaded artifacts, before/after images and review receipts remain under `artifacts/gp-v3/`; generated workbooks and ZIPs are deliberately not committed. The user-facing improvement is reuse: another engineer can build a new comparison directly from the normalized, versioned, source-linked package, while an investment professional can review separate gross sponsor outcomes and operating issues without manually re-keying either into the GP handoff.
