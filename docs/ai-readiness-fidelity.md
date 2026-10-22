# Data Foundation — visual fidelity correction

Presentation-only follow-up to `5d45486`, on `feat/ai-workflow-readiness`, tracked by the reopened Harmony **#45**.

## Preview and process verification

Open **http://127.0.0.1:8502/?page=foundation**.

Before editing, port 8502 was confirmed as PID **70437**, `python -m streamlit run portfolio_app.py --server.address 127.0.0.1 --server.port 8502`, with the portfolio worktree on clean branch `feat/ai-workflow-readiness` at exact commit `5d454863ebc1691de26da29daacbf7a4ab34878e`. The serving checkout was correct. Imported presentation modules were subsequently cleared by restarting only that preview after styling changes. Final preview PID: **74549**.

Port **8501**, PID **20385**, continues to serve `app.py` from the separate frozen-engine worktree. It was never stopped or changed. Restart the portfolio preview with `./scripts/run_portfolio_demo.sh` from the portfolio worktree.

## Visual changes

- Stronger navy title/subtitle hierarchy, three aligned KPI cards, measured coverage bar, explicit partial-assessment treatment and a compact workflow-scope strip.
- Bordered white panels on a restrained blue background. Styles are scoped to the Data Foundation route; other investment pages retain their presentation and navigation.
- Compact mapping table with colored source/period states and separate period/scenario columns. All twelve candidates remain available. Six actual rows across all three companies appear first; budgets remain directly below in the scrollable table and in the scenario filter.
- Source inspection opens by default with three columns: original workbook/cell/value/formula, retained normalization and metric semantics, and standardized output with separate source/mapping status. Entity, unknown basis and unrecorded human approval remain explicit; full provenance remains expandable.
- Company-grouped issues with Review Required / Blocked badges and the existing source-backed narratives, actions, caveats, operand tables and original-finding navigation.
- Compact six-file export inventory and full-width download, with the unchanged data package and potential downstream-use qualifications.

The supplied polished mockup guided layout, hierarchy, colors and density. Its illustrative figures, scores, issue descriptions and cell references were not copied. The total score remains **Not Evaluated**, monthly coverage **67% (8/12)**, and known issue groups **4**. Streamlit's native table, filters and expanders are retained.

## Actual visual review

The original live page was captured at `artifacts/ai-readiness-fidelity/before-desktop.png`. The first styled capture revealed inherited Streamlit Markdown/caption margins crowding adjacent elements and native filter markup differing from older BaseWeb selectors. The bounded correction reset those margins, aligned filters with the mapping heading, styled the installed React Aria controls, tightened detail headings, and ensured mobile title clearance below the toolbar. The preview was restarted before final capture to avoid stale presentation imports.

Final actual Chrome captures from **port 8502**:

- [Desktop, including mapping detail and all four areas](images/ai-readiness/fidelity-desktop.png)
- [Mobile](images/ai-readiness/fidelity-mobile.png)

## Verification

- **27 focused regressions passed** in 69.20 seconds: Data Foundation contracts/readiness, navigation, company switching, investment dashboard/Excel reconciliation, GP Excel structure, source snapshots and metric hyperlinks.
- After the final spacing pass, the **10 page/data tests passed again** in 21.32 seconds. Presentation assertions now check the separately displayed period and scenario; financial values are unchanged.
- Actual Chrome passed desktop/mobile, three-column source inspection, original issue deep link, ZIP download and standalone independent consumer; **zero browser errors and external requests**.
- Existing investment-workspace Chrome journey was rerun to check all three company reviews/selectors, six company-specific downloads, GP workbook and evidence hyperlinks, plus the data package.
- Backend/readiness module, configured data model, normalized records, analytical snapshots, financial/return calculations, investment ledger, company pages, shared dashboard/navigation, source adapter and exporters are unchanged against `5d45486`.
- **29 pinned source/workbook/snapshot hashes** match. The downloaded package remains byte-identical to the preceding implementation, SHA-256 `b2e5da282e8b950dbae6a4c48cd45d4694a0441ac8cdbe35bc2d26fe72811a7b`.
- **Zero fresh analyst inference**. Full local receipts and generated downloads remain in ignored `artifacts/ai-readiness-fidelity/`.

No backend redesign, additional data features, merge or deployment.
