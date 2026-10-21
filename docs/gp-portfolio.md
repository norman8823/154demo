# GP Portfolio Intelligence — review handoff

Open **http://127.0.0.1:8502**. The prepared-only GP application is separate from
the unchanged analytical-engine preview on 8501.

## Five-minute review

1. Compare the three aligned company cards: Summit and Tallis are **September
   2026 monthly**; Harrow is **FY2026 annual**. Revenue, reported EBITDA, margins
   and plan comparisons retain their source periods. There is no financial total.
2. Open Tallis, inspect its existing Investment Summary, Priority Findings,
   Investment Assessment and Management Questions, then follow **View Evidence**.
   Use **Portfolio Overview** to return.
3. Open **Portfolio Watchlist**, filter by company, expand a finding and follow
   its evidence action. The 17 findings retain their original language, questions,
   caveats, quotes and source IDs. Priority and disposition come from the approved
   analyst output; the application does not assign scores or sum impacts.
4. Download **Portfolio Excel**. Inspect the four worksheets, follow a company
   link into Company Comparison, then follow a source link to Source References.
   The Watchlist includes an index and full original finding narratives below it.
5. In a company drilldown, switch between the original standard and supplied firm
   template exports. An optional uploaded firm template still uses the unchanged
   company exporter.

## Run and reproduce

```sh
cd /Users/norman/main/154demo-portfolio
./scripts/run_portfolio_demo.sh
```

The launcher binds to loopback on 8502 and disables local environment-file loading.
The GP path needs no API credential: it reads only the committed, approved prepared
Reviews through `verify_prepared()`, preserving original provider receipts and
recording **zero current model calls / $0 current inference**. There is no upload,
analysis-generation or cache-miss inference path in the GP application. Company
Excel template upload affects formatting only.

For a fresh checkout:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
COPILOT_ENV_FILE='' .venv/bin/python scripts/seed_demo_results.py --verify-only
./scripts/run_portfolio_demo.sh
```

The original application retains its documented credential-scoped cache setup;
see [the frozen checkpoint](skill-engine-checkpoint.md). GP viewing does not
depend on that private cache. Changed/missing source packages fail verification
with a visible recovery instruction. Prepared verification covers sources,
arithmetic and quotes; it does not certify every investment interpretation.

## Compatibility boundary

All source files pinned by `demo_results/manifest.json` remain byte-identical to
checkpoint `e59d651944fe786e3b7d50735cfbfe0505990748`, including `app.py`, the
analytical core, cache, presentation contracts and company exporters. No AI
model, prompt, methodology, source-verification rule or dependency was changed.

`portfolio_company.py` reuses six allowlisted UI function definitions from the
verified monolithic `app.py`. It does not execute the app's module body, credential
loader, upload screen or compute function. This preserves the existing company
screen while leaving the frozen source hashes valid. If the frozen UI contract
changes, this boundary and the prepared checkpoint must be reviewed together.

Comparison reuses `excel_layout.financial_table` and its existing comparability
guards. The additional EBITDA margin is simply same-source reported EBITDA divided
by revenue; its budget variance is in percentage points. Unknown or incompatible
bases, units and missing denominators are handled explicitly. No annualization,
currency conversion, adjusted-EBITDA substitution or consolidation is performed.

## Harmony and commits

Canonical parent **#26 GP Portfolio Roll-Up** contains these linked work packages:

| Package | Card | Implementation commit | Dependency |
|---|---:|---|---|
| GP-01 Registry and prepared adapter | #27 | `323dfbe` | frozen checkpoint #25 |
| GP-02 Comparability and periods | #28 | `90d7ce8` | GP-01 |
| GP-03 GP overview | #29 | `a885cd0` | GP-01/02 |
| GP-04 Cross-company watchlist | #30 | `9c3afcb` | GP-01/02 |
| GP-05 Reused company drilldowns | #31 | `d039094` | GP-03/04 |
| GP-06 GP Excel workbook | #32 | `edc8985` | GP-02/04 |
| GP-07 Integration, review and QA | #33 | final QA commit in branch history | GP-01–06 |

Scopes, deliverables, acceptance criteria, dependencies, progress and evidence are
recorded on these existing-board cards. The connected Harmony API exposes only
list/start/update/complete operations, with no structured hierarchy, task-graph,
budget or usage mutation fields. Parent relationships and dependencies are recorded
in card details; factual test timings and review outcomes are recorded in progress
notes. No replacement board, ticket store or invented quota reading was created.

## Validation and review

- Checkpoint's three prepared results verified offline; dependency check passed.
- Full final suite: **365 passed in 192.83 seconds**. The repository's autouse
  fixture blocks real HTTP calls. GP adapter and navigation tests additionally
  forbid analysis/configuration entrypoints.
- Comparison checks cover exact prepared figures, budget math, period labels,
  missing comparisons, incompatible basis, unknown units and invalid denominators.
- All 17 original findings and their recursive calculation/source closure are
  retained. Identical IDs in different companies remain company-qualified.
- Workbook tests reopen all four worksheets, compare dashboard values, preserve
  original narratives and quotes, validate hyperlink targets, verify formatting,
  and ensure source formulas stay literal text.
- Actual Chrome QA downloads/reopens the GP workbook and all six company exports,
  checks summary/evidence/return navigation, exact finding links, currency rendering,
  all four worksheet previews and mobile overflow. Run with:

  ```sh
  COPILOT_ENV_FILE='' .venv/bin/python tests/browser_portfolio.py
  ```

- All four actual XLSX worksheets were rendered with the macOS Quick Look XLSX
  importer and visually inspected. This inspection uses the generated workbook,
  not a separately authored HTML mockup.
- One independent Sol integration review identified two P2 issues: currency prose
  interpreted as math and evidence navigation resetting after a finding deep link.
  Both were fixed, covered by regressions and independently revalidated. No other
  material review findings remained.

Complete local receipts are preserved under `artifacts/gp-portfolio/`: full-suite
logs, earlier failed attempts, browser log/JSON, downloaded XLSX files, desktop/
mobile screenshots, Quick Look renders and render metadata. They remain ignored.
Selected synthetic screenshots are included below for independent review.

The initial full run overlapped UI module edits and produced five stale-import
failures; its log is retained separately. The final release run passed all 365, including the additional formatted-preview regression. An earlier stable run passed 364 before that presentation improvement.
Browser-driver corrections wait for Streamlit rerender completion before download
and click visible radio labels instead of hidden native inputs. No financial
result was changed to satisfy a test.

## Visual differences and limits

The overview follows the reference's navy navigation, aligned stacked company
cards, restrained variances and clear period guardrail, with the requested white
background. It uses actual accepted lead findings, rather than illustrative
reference wording or figures. The full watchlist is expandable and filterable.

Company detail preserves the existing, more detailed analytical presentation,
including its gross-margin KPI, lengthy source-backed narratives and visible
limitations. Its layout is therefore longer than the static detail reference.
The Excel page previews actual generated tables, rather than an imitation Excel
ribbon. The native workbook includes all original narratives and source detail,
making its supporting worksheets wider and longer than the reference image.

There are no new investment-analysis costs. Codex subscription token/quota values
are not exposed by the connected Harmony tools, so no numerical usage is claimed.
No deployment or merge is included.

## Selected actual screenshots

- [GP overview](images/gp-portfolio/overview.png)
- [Existing company findings, investment assessment and questions](images/gp-portfolio/company-detail.png)
- [Generated workbook preview](images/gp-portfolio/excel-preview.png)
- [Responsive mobile overview](images/gp-portfolio/mobile.png)
