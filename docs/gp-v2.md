# Portfolio Intelligence Workflow v2

This demo accelerates an investment team's operating review: approved company Excel packages → prepared AI assessment and verification → portfolio exceptions → management follow-up → source-linked Excel handoff. It preserves the original company analyses and does not run a new analyst request.

## Morning inspection

1. Open **http://127.0.0.1:8502**. Review reporting coverage, same-period EBITDA exceptions and the three Actual/Budget charts. Summit and Tallis are September monthly; Harrow is FY2026 annual. Each chart has its own zero-based dollar axis. Revenue, EBITDA and margin are never consolidated.
2. Open Tallis from its company card. Review the original Investment Summary, Priority Findings and Management Questions. The headline monthly shortfall and a finding's YTD impact have different scopes, which remain explicit.
3. Use the visible Company selector to switch to Harrow and Summit. Findings, financials, evidence selection and the standard/custom company downloads switch together.
4. Open **Investment Issues**. All 17 accepted findings are grouped by company (5 Summit, 5 Tallis, 7 Harrow), with original classification, impact, question, action, qualification and source quotations. Open a finding's evidence; return through its summary without losing the selected finding.
5. Download the GP workbook. Follow an Investment Issues source ID → Source References → the original source cell, or a calculation definition with individual operand links. Everything needed is included in the XLSX and works without a network connection.
6. In Company Comparison, click Tallis revenue budget (D8). Its reporting-metric block identifies the budget scenario; the operand links through financial_36 to **TBA 03 Practice P&L!I12**. EBITDA budget (D11) similarly ends at **I41**, rather than the actuals in column G.

## What changed

The overview now shows operational review KPIs, paired Actual/Budget charts, a sortable numeric comparison table, period labels and a concise management-follow-up preview for each company. A separate comparison view puts companies across columns. Navigation is persistent, with explicit company selectors and retained finding deep links. The design uses the supplied white/navy references and public institutional dashboard research; see [design research](gp-v2-design-research.md). It remains a Streamlit workflow demonstration.

The GP workbook has nine review/index sheets and 24 company-namespaced source snapshots:

- Portfolio Overview, including three native Excel charts and separate company-period financials
- Company Comparison, a financial-attribute matrix with links to company sheets and exact scenario/metric provenance
- Investment Issues, including all original accepted narratives, questions, actions, source quotations and qualifications
- Summit Home Services, Tallis Brook Accounting and Harrow Ridge Environmental
- Source References, including analyst calculations and transparent reporting-metric arithmetic
- Source Snapshots, a navigable catalog of approved source worksheets
- Reporting Output, nine numeric metric rows for copying or mapping into an existing reporting template

All six existing company-specific standard/custom exports remain available. Reporting Output provides a simple handoff; there is no claimed automatic platform integration. No valuation, invested capital, MOIC, IRR, fund accounting or new synthetic financial history was added.

## Evidence design

Only the canonical workbook paths and hashes in `demo_results/manifest.json` are accepted. Source snapshots preserve original worksheet cell coordinates, original source-unit values, styles, merges and comments. Company prefixes (SHS, TBA, HRE) plus sheet ordinals avoid collisions within Excel's 31-character limit.

The 1,755 original formula cells display approved retained observed values. Comments retain original formula text, original-unit observations and validated base-unit values. There are no active source formulas, macros or external-workbook relationships in the GP file. Snapshot sheets are visible and protected for review; protection is not encryption. The navigation gutter sits outside the original source grid.

Native internal Excel hyperlinks lead from each issue to its company-qualified source index, then to an original included cell. Derived analyst calculations show their exact original expression, scope, assumptions, limitations and individual operand links, recursively where necessary. Presentation-only margins/variances have separate reporting-metric blocks with exact actual/budget operands; they are not presented as native source observations. Unsupported references, missing operands, provenance mismatches or source changes fail with an explicit error.

## Verification and review

Verified October 21, 2026:

- Full regression: **373 passed in 214.16 seconds**. After native chart-label polishing, the eight workbook/source/metric-link tests passed again (13.28 seconds).
- Actual Chrome workflow: all three company summaries, questions/evidence, return navigation, finding deep links, explicit selector switching, all six original company exports and the GP export. No browser exceptions or external requests. Mobile viewport 390px has no document overflow.
- Downloaded GP workbook: 33 sheets; all internal link targets resolve; financial/margin/variance values reconcile; monthly/annual data remains separate; all accepted finding fields and source quotations are retained.
- Exhaustive source checks: original cell observations, coordinates, formula provenance and safe unique names across all three canonical workbooks; representative multi-operand/nested calculations; unsupported references and noncanonical paths fail safely.
- Prepared verification: all three approved results verified with **0 new model calls / $0 current analyst inference**. The 23 manifest-pinned analytical files and approved snapshots remain unchanged. Original inference receipts remain historical provenance.
- Native spreadsheet inspection: the actual downloaded XLSX was opened/rendered by macOS Quick Look and **LibreOffice Calc 26.8.1**. Calc rendered the three positive Actual/Budget charts and the complete workbook. Its PDF export retained 1,057 resolved native internal link destinations. The temporary Calc renderer is a QA tool, not an application dependency.
- One substantive independent read-only review identified a material comparison-link defect: budget/derived numeric cells opened actuals. Corrected with scenario-specific support and explicit calculation blocks; focused regressions assert Tallis I12/I41 destinations and all four margin-variance operands. Optional blank-cell source formatting was also preserved.
- Screenshot review corrected sidebar wrapping/label contrast and native chart labels. See the retained rendered images below.

Microsoft Excel and Numbers AppleScript opens timed out in this environment. Their interactive mouse click-through was therefore not certified; Calc supplied native rendering and link-import verification. Quick Look omits charts, so it was not used to judge chart rendering. A proposed screenshot of an unnamed Excel window was rejected by automatic approval review to avoid capturing unrelated user content; that screenshot was not taken.

These checks verify sources, arithmetic, presentation and navigation. Original causal interpretations, sensitivities and management explanations retain their original qualifications and require investment-team judgment. Subscription quota/token telemetry was not exposed by Harmony; no usage amount is invented.

## Task tracking and commits

Existing Harmony milestone #34 records the authoritative five-task scope. V1 #27–33 remain Done.

| Card | Work package | Implementation evidence |
| --- | --- | --- |
| #35 | V2-01 Portfolio Dashboard Presentation | `0853331`; source-backed KPIs/charts/comparison tests |
| #36 | V2-02 Investment Issues and Company Navigation | `e567037`; switching/deep-link/export regressions |
| #37 | V2-03 GP Excel Restructuring | `f2f06f5`; workbook parity and original narrative retention |
| #38 | V2-04 Excel Source-Cell Deep Linking | `103d322`; exhaustive snapshots/internal source and calculation links |
| #39 | V2-05 Integration, Visual Review and QA | `ed50375`; final review correction, 373-test regression, browser/native-render receipts and screenshots |

The feature branch is `feat/portfolio-dashboard-v2`, created at exact v1 checkpoint `0ea827b6f0492871132572196a67d85646ad9760`. V1 and the frozen analytical-engine branch are preserved. No merge or deployment is part of this work.

Compared with the supplied visual references, the implementation uses genuine operating-review KPIs, native Streamlit selectors/sortable tables, and the existing company-report presentation. The Excel reporting page previews real generated tables; the downloaded workbook contains actual native charts. White backgrounds, navy typography, aligned company cards and restrained variance colors carry through the workflow.

## Preview and receipts

From `/Users/norman/main/154demo-portfolio`:

```sh
COPILOT_ENV_FILE='' .venv/bin/python scripts/seed_demo_results.py --verify-only
./scripts/run_portfolio_demo.sh
```

The launcher binds only `127.0.0.1:8502` and loads no API credentials. Leave the existing analytical app on 8501 alone. For a fresh checkout, create `.venv` and install `requirements-dev.txt` first. Restart the preview after editing exporter modules so its cached workbook refreshes.

```sh
.venv/bin/python -m pytest -q
.venv/bin/python tests/browser_portfolio.py
```

The browser check requires the local Chrome/Playwright setup. Full local receipts, failures/corrections, research captures, generated XLSX files, native renders and the actual downloaded workbook remain in ignored `artifacts/gp-v2/`. Owner input duplicates were preserved reversibly under `artifacts/v2-intake-preserved/`; their receipt is `artifacts/gp-v2/intake-preservation.json`. Generated workbooks, runtime logs, credentials and caches are excluded from commits.

Rendered screenshots retained for independent review:

- [Desktop overview](images/gp-v2/overview.png)
- [Company detail](images/gp-v2/company-detail.png) and [management questions](images/gp-v2/management-questions.png)
- [Investment Issues](images/gp-v2/investment-issues.png)
- [Excel reporting page](images/gp-v2/excel-preview.png)
- [Mobile overview](images/gp-v2/mobile.png)
- [Native spreadsheet charts](images/gp-v2/xlsx-native-dashboard.png), [comparison](images/gp-v2/xlsx-native-comparison.png) and [original source snapshot](images/gp-v2/xlsx-native-source.png)

The workflow removes manual compilation of three operating summaries, regrouping of 17 findings and re-keying of a GP reporting workbook, while keeping the original evidence and management follow-up attached. No time-saving estimate has been measured or claimed.
