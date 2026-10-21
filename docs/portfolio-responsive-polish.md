# Portfolio Intelligence — responsive UI polish

Presentation/navigation refinement from checkpoint `98d06792084eafc414b553da8b178c6fb4c0b425`, on `feat/ai-workflow-readiness`. Dedicated Harmony **#46**; completed #45 remains closed.

## What changed

- Removed **Company Comparison** from the sidebar. Existing `?page=comparison` URLs route to Overview. The comparison calculations and **Company Comparison Excel worksheet remain unchanged**.
- The Overview holdings table displays nine concise columns: **Company, Invested, Equity value, Gross MOIC, Gross IRR, EBITDA, Margin, Revenue vs plan, Sector**. The five requested redundant columns are omitted only from this UI. Company names remain complete; numeric fields use compact monetary/percentage formatting, with gross IRR retained to two decimals. Names open the existing company route in the same window.
- Replaced independently scrolling dataframes with naturally sized semantic tables. Small tables display all records. Larger evidence sets use filtering and pagination, with long provenance text in native disclosures. **Sorting and the previous table CSV download remain available in Table options**. No table or evidence panel has a fixed scrolling height.
- At phone/tablet widths, the same table records become vertically labeled cards. Operating company cards stack, KPI cards resize, native sidebar navigation remains reachable, and controls remain touch-sized. Desktop and mobile share the same data functions and DOM records, with CSS controlling layout.
- Data Foundation retains its polished three-column source → transformation → output inspection on desktop; the columns stack on phones. All **twelve filtered mapping candidates** display naturally. The **204 unresolved observation rows** are paginated ten at a time rather than placed in a scrolling panel or rendered as one enormous table.
- Excel previews use a worksheet selector instead of a horizontally scrolling tab strip. Wide records preserve additional fields in expandable details; large source indexes are paginated. Downloads still use the original exporters.
- Consolidated the two conflicting global CSS blocks into `portfolio_layout.css`: consistent navy/white surfaces, heading hierarchy, 12–16px card padding, disciplined section/bottom spacing, readable table text, and responsive controls. Corrected a legacy card selector that also applied oversized borders/padding to company selector/format/radio widgets. Improved sidebar contrast and width; sidebar aliases are concise while company-page headings remain complete.
- Kept the frozen company presentation functions, with a display-only adapter for their tables/JSON and secondary heading level. Source/analytical code is untouched. Made the existing company-format reset explicit after Chrome caught a prior custom-template selection surviving a company switch.

## Actual screenshots

Before/after captures are from the existing local app in **Google Chrome**, not generated mockups:

| View | Before | After |
| --- | --- | --- |
| Overview desktop, 1440px | [Before](images/ui-polish/before-overview-desktop.png) | [After](images/ui-polish/overview-desktop.png) |
| Overview phone, 390px | [Before](images/ui-polish/before-overview-mobile.png) | [After](images/ui-polish/overview-mobile.png) |

Focused final views: [1280px holdings table](images/ui-polish/holdings-laptop.png), [mobile holding](images/ui-polish/holding-mobile.png), [mobile operating chart](images/ui-polish/operating-mobile.png), [Data Foundation desktop detail](images/ui-polish/foundation-detail-desktop.png), [Data Foundation mobile detail](images/ui-polish/foundation-detail-mobile.png), [Company Detail mobile](images/ui-polish/company-mobile.png), [Investment Issues mobile](images/ui-polish/issues-mobile.png), [Excel preview mobile](images/ui-polish/excel-mobile.png).

All page/width captures, including Summit, Tallis and Harrow summaries/evidence, remain in ignored `artifacts/ui-polish/before/` and `artifacts/ui-polish/after/`.

## Verification evidence

- **398 full offline regressions passed** in **273.09s**. Initial focused suite: **23 passed**. After the final navigation/table-toolbar correction: **11 passed** in **38.01s**.
- **70 actual Chrome page/viewport cases passed** across **390, 430, 768, 1280 and 1440px**: Overview, Data Foundation, Investment Issues, all three company summaries and evidence views, the four Excel preview choices, and expanded Data Issues.
- At **1280 and 1440px**, all nine Overview holdings columns fit; DOM geometry confirms no horizontal table overflow. On narrow screens the table becomes labeled company records. No page-level horizontal overflow, currency-as-math rendering, or unintended nested vertical scroll containers were found.
- Actual mouse-wheel checks over holdings and mapping records move the **page**, at all five widths. Native mobile sidebar access, same-window company links and legacy comparison URLs passed.
- Actual download journey passed: **six company Excel files**, the **GP workbook**, and the **data ZIP**. The GP workbook retains **34 sheets** and all **17 tested issue → source chains**. Company switching and exact finding/evidence navigation passed.
- All seven downloaded Excel files have **identical cell values, number formats and hyperlink targets** to the preceding implementation. The six-file data ZIP remains **byte-identical**, SHA-256 `b2e5da282e8b950dbae6a4c48cd45d4694a0441ac8cdbe35bc2d26fe72811a7b`. The independent consumer still runs from the extracted ZIP.
- All **29 pinned analytical source/workbook/snapshot hashes** match. Operating adapters/calculations, investment ledger/returns, source contracts, prepared reviews and Excel exporters are unchanged. **Zero fresh analyst inference**.
- The final live smoke check also downloaded the holdings CSV and confirmed its three original companies/nine raw-value fields, laptop table fit and company navigation.

Detailed receipts: `artifacts/ui-polish/full-regression.txt`, `final-table-tests.txt`, `after/responsive-receipt.json`, `download-journey/browser-results.json`, `preservation-receipt.json`, `final-preview-smoke.json` and the secret audit. Runtime artifacts remain excluded from commits.

## Preview and limits

Open **http://127.0.0.1:8502**. Restart from `/Users/norman/main/154demo-portfolio` using `./scripts/run_portfolio_demo.sh`. Only the portfolio preview was restarted. The analytical application on **8501**, PID **20385**, remains untouched.

The responsive presentation is validated in Chrome at the requested sizes; physical-device Safari/other browsers were not separately tested. Sorting now uses **Table options**, rather than clickable dataframe headers. Large evidence sets require paging/filtering or opening record details; full original data remains in the existing downloads. Long source/JSON disclosures deliberately grow the page when opened. No separate mobile app, hosting, QR code, tunnel, deployment or backend feature was introduced.
