# Portfolio Intelligence Copilot

A local Streamlit application for monthly portfolio financial review. Upload conventional income statements, generate immediately from supported source financials, optionally review account mappings, inspect calculated findings and source cells, and download an editable standard or firm-template Excel report. The original three-file demonstration remains available. Setup uses three stacked steps: Upload Financial Files, Choose Output Format, and Generate Portfolio Review. Optional mappings and template guidance are collapsed; results prioritize financial metrics, material findings, the Investment Assessment, and Excel downloads. Recognition summaries describe supported statements, not validation of every worksheet. Full limitations and extraction details remain available in collapsed sections.

## Launch

Python 3.11 or later:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run app.py --server.address 127.0.0.1
```

Open **http://127.0.0.1:8501**. Once installed, the last command launches the app. No database or account is needed. Calculations, manual mapping and Excel exports work offline.

## Onboard a company

1. Upload one or more supported `.xlsx` or financial CSV files.
2. Click **Generate Portfolio Review**. Reported Revenue, Gross Profit, Operating Income and EBITDA are prioritized; source detail and formula arithmetic are reconciled where available. No blanket account approval is required.
3. Review findings and the prominent data-quality limitations; download the standard Excel report or your supported template.
4. Optionally expand **Review Account Mappings** to inspect source references, explanations, material ambiguities, period interpretation and editable mappings. Unconfirmed ambiguous accounts never enter calculated totals. Affected detail-based metrics remain unavailable; independently supported reported metrics continue.
5. Optional **Confirm and save mappings locally** stores accepted decisions in `.local/account_mappings.json`. Reuse is scoped to company/worksheet/account context. Dates and numeric amounts are reread from source.

Unrecognized files or isolated uncertain rows do not invalidate other supported statements. A file with no usable financial table or dated columns still needs source/table interpretation; this is not a requirement to recreate a chart of accounts.

Use **Use Demo Files** to load the original reports. Uploaded bytes are actually used and remain available across the three views during the session. Uploading a replacement invalidates the previous report.

## Automatic workbook recognition

Upload and Generate use the same content-based interpretation without mandatory column, currency, scale or accounting-basis approval. Conventional `Metric`, `Measure`, `Line` and blank-label headers require corroborating financial labels; safely evaluated formula totals count as table evidence. Fee revenue and reported/consolidated presentation qualifiers are recognized without treating adjusted EBITDA as ordinary EBITDA. Dates attached to acquisitions or entity inception are excluded from reporting-column detection. Numeric data rows cannot become headers by inheriting a date from above.

Explicit denomination phrases such as “US dollars” establish USD whole source dollars; thousands/millions remain explicit multipliers. Consistent masthead units can be reused across sheets with the same stated company, with the original metadata references retained. Mixed denominations and companies are not collapsed. Currency number formats can identify denomination; a bare dollar symbol does not establish USD. No currency, multiplier or accounting basis is inferred from financial magnitude. Unknown metadata stays labeled source units and supported calculations/exports continue; comparisons that require unestablished monetary comparability remain unavailable.

The latest actual period with populated reported revenue/EBITDA headlines is the default. Blank or partially populated later headline columns are disclosed and skipped; populated contradictions stay current and visible rather than disappearing behind an older healthy period. This is a statement-headline availability check, not an assertion that every schedule is complete. Same-file agreeing totals can corroborate a statement with unstated accounting basis; explicit basis conflicts remain blocked and no basis is filled in.

The existing optional structured AI fallback can propose unfamiliar table coordinates or account labels. Python rereads the source, validates dated columns and reported financial labels, and calculates amounts. One usable reported headline supports a partial review without requiring approval of unrelated ambiguous fields. A model cannot supply unstated dates, amounts, units or ordinary EBITDA. That recognition-only change introduced no new model integration; the subsequent AI activation and its separate validation are described below.

Recognition regression includes Tallis Brook's September 2026 source revenue **$3,475,418** and reported EBITDA **$684,306**, automatic generation and both Excel formats, plus the original event-staffing, Summit and synthetic development fixtures. Tallis was a failed blind recognition case and is now development regression data, not independent validation after these fixes. Corrected monetary recognition also enables existing receivables/YTD observations in the original demo; its original financial, covenant and billing checks remain unchanged.

All worksheets continue through the existing bounded schedule/commentary reader. This does not establish exhaustive analysis: static mixed-unit operating tables, complex multi-block WIP/realization schedules, transposed statements, ambiguous competing financial tables, undated headers and unsupported formulas can still require optional interpretation or remain unavailable. An absent date that prevents defensible period attribution still requires source clarification. Inspect Data Quality & Coverage for actual recognized structures.

## Investment Summary and financial context

Results begin with a compact **Investment Summary**: the source-referenced business description, up to three available financial KPIs calculated by Python, and an optional operating-structure summary. The existing interpretation request supplies descriptions; there is no extra profile API call. Geography, operating branches, acquired practices/businesses, subsidiaries and independent companies are distinguished only when source text establishes the relationship. Missing attributes are omitted. Exact descriptive quotations retain original filename, worksheet and source location in Source Evidence. Investment Assessment remains the section for conclusions and management actions.

Standard Excel includes concise context near the top of Executive Summary and an Investment Summary worksheet with descriptions, operating units, financial metrics and evidence references. Custom templates support `{{INVESTMENT_SUMMARY}}`; the accompanying summary worksheet also preserves context when the original template has no field. Existing formulas and formatting remain protected.

Conventional annual and fiscal-quarter statement headers now retain separate period keys, actual/budget/prior-year roles, stated units and accounting basis. Fiscal years are not silently converted to December or compared with monthly observations. Existing monthly reporting remains supported. Finding validation distinguishes exact cited quarter/age-bucket/entity labels from financial quantities. Unsupported amounts and unknown financial fact IDs are rejected; an invalid management question is repaired separately rather than discarding a supported financial finding.

The current four-package evaluation is development regression testing, not an independent blind benchmark. Earlier Harrow, Tallis, Summit and event-staffing outputs are preserved under `artifacts/`; new versions have separate records and code fingerprints. Source bounds still limit coverage, ambiguous multi-block statements may need review, unknown units/basis remain unknown, and organization descriptions and investment interpretations require human review. Unstated causal effects, write-offs, forecast recoveries and valuation changes are not calculated. Persistent cache keys include the profile/analysis version and changed source code, so old reasoning is not silently reused.

## Executive results

The dashboard and Excel Executive Summary use the same concise, source-grounded presentation. Related EBITDA and budget-margin findings are combined only when the cited financial records support common direct-cost pressure. Separate reconciliation exceptions remain visible; their repeated category differences are never added together as losses. Cards link to the original evidence, with grouped financial sources available in the same evidence path. Detailed checks, exact amounts, definitions and source cells remain in the supporting Excel sheets.

The dashboard selects up to three distinct investment themes, with secondary insights, positive developments and scoped commentary checks in **Additional insights & commentary**. Data-quality exceptions remain separate unless they undermine core financial conclusions. Full-package briefings target 150–200 words; sparse inputs receive shorter narratives rather than invented explanations. Missing coverage and accounting limitations remain visible under **Data Quality & Coverage**.

## Supported structures and boundaries

| Structure | Behavior |
|---|---|
| Horizontal monthly P&L: account labels in one column, dated actual / budget / prior-period columns | Automatic detection of conventional headers, financial sections and standard totals; mapping review for ambiguity |
| QuickBooks-style export with company/basis text above a sectioned monthly table | Automatic period and section extraction; subtotal exclusion and total/detail reconciliation |
| Two-level period + Actual/Budget headers, including merged period labels | Detected where month/year is explicit; otherwise review column interpretation |
| Multiple monthly statements / financial worksheets | Compared for the same company only when dates, basis, currency, scale and EBITDA definitions are comparable |
| Multiple companies | Separate financial records and findings; no combined revenue/EBITDA or ambiguous company-wide template headline |
| Financial CSV with a conventional account/description header and period columns | Same normalized financial path; physical CSV row numbers correspond to its worksheet-style row references |
| Unfamiliar header/account vocabulary | Automatic interpretation where source-validated; optional worksheet/header/account review for material uncertainty |
| Original platform workbook, rate card and scheduling CSV | Existing guarded adapters preserve the three priority checks and known-format partial upload support |
| New covenant or scheduling schema | Requires a supported specialized schema; general account mapping alone does not establish covenant compliance or invoice matching |
| Transposed financials, arbitrary bookkeeping exports, annual/YTD/quarter mixtures, PDFs, `.xls`, macros, images | Not automatically supported. Reshape into a conventional monthly financial table or supply an explicit supported mapping; no universal parser is claimed |

Automatic discovery searches the first 60 rows for conventional account headers and period columns, with label columns in the first eight columns. A human can select another table explicitly. Competing table headers can be selected optionally. Overlapping company/period statements are not summed: agreeing reported figures are corroborated and used once, while conflicting metrics are withheld and explained. A yearless Actual/Budget header does not acquire a year from the computer clock.

Amounts preserve raw values, file/sheet/cell, period header references, classification, role, scale and basis. Supported arithmetic formulas are recalculated locally using a bounded expression reader; workbook code is never executed. Unsupported formulas or nonnumeric amounts need source correction/recalculation. Blank and dashed account values remain missing, not zero. Numeric text supports English-style decimal points and correctly grouped comma thousands; ambiguous decimal-comma text requires numeric source cells or normalization instead of guessing. Source formulas in exported evidence are literal text.

## Financial calculations

The common schema includes revenue, direct costs/COGS, gross profit, operating expenses, EBITDA, net income, other/unmapped accounts, and separate operating profit, interest, income tax and depreciation/amortization where explicit.

Reported totals are used once. Detail rows can be summed when complete; intermediate subtotals are excluded. Reported totals are checked against mapped detail, and gross profit against revenue less direct costs. Discrepancies generate reconciliation findings rather than silent repairs. Reported amounts can remain visible when a detail check fails, but inconsistent gross margin is withheld.

EBITDA is **not** net income or operating profit. It must be reported explicitly, or calculated from net income plus explicit interest, income tax and D&A for the same period. EBITDA trends require matching definitions and comparable basis/units. No missing component is assumed zero. Adjusted EBITDA requires review and is not automatically treated as the same definition as ordinary EBITDA.

Available screens include revenue trends, gross margin changes, budget variances, expense outliers and basic reconciliation. Priority ranking shows up to three generic findings: material EBITDA budget misses and reconciliation first, then revenue budget deviations of at least 5%, margin deviations of at least one percentage point, expense increases of at least 25% and 1% of current revenue, followed by revenue and comparable EBITDA trends. These are illustrative screening thresholds, not an accounting materiality opinion. Missing comparisons appear in readiness, not in financial exception totals.

Covenant and billing modules remain specialized. The supplied covenant is a cap-only sensitivity, holding other add-backs unchanged; its March step-down is not a future-breach forecast. Scheduling removes exact duplicate rows, retains multiple positions per event, and separates uninvoiced contract-rate value from invoiced rate differences. Potential billing exceptions require reconciliation to invoices, credits, timing and contract amendments.

## Bounded follow-up investment investigation

The initial analysis and its prompt are preserved. After accepted provider analysis, `investigation.py` performs at most one additional pass over three to five independent issue groups. Targeted local retrieval can reread up to 2,400 relevant cells, capped at 400 per worksheet; the follow-up packet remains capped at 320 facts and 110,000 characters, including calculation dependencies and source context. It supplies no tools or open-ended request loop. `investigation_math.py` performs arithmetic locally with explicit company, entity, period, grain, scenario, currency and basis guards. Quarterly and monthly figures cannot be interchanged; source-specific pre-ownership periods cannot be added as comparable observations.

Each accepted investigation separates conclusion, evidence, financial implication, established versus unresolved assessment, and management action. Refined findings lead the dashboard and both Excel formats; initial validated findings for uncovered issues remain available. Investment Assessment text and Management Questions use accepted findings only. Failed siblings, invalid IDs, unsupported figures and unqualified sensitivities remain blocked. Initial results survive follow-up failure. Unknown accounting basis stays unknown; historical client fees are not forecast losses, aged balances are not write-offs, and a snapshot does not establish persistence.

The existing private report cache fingerprints both investigation modules. Failed investigations are not stored as successfully completed investigations. October 20 controlled evaluation reused preserved genuine initial analyses and made exactly one new GPT-6 Luna call for each of Tallis, Summit and the original event-staffing package: eight of ten follow-up findings survived validation. Two failed findings retained explicit source/number rejection reasons. Saved responses were replayed locally to correct validator false positives without more provider calls. The nine investigation tests and 254 existing tests pass. Private packets, receipts, calculations and both report formats are retained under `artifacts/bounded-investigation-v1/`; no answer keys were supplied as runtime inputs.

## Full-package investment analysis

`package_reader.py` adds a bounded source ledger to the existing financial review; `package_analysis.py` computes trends, exposures, cohort roll-forwards, within-unit comparisons and commentary tests; `analyst_ai.py` uses the existing Responses API integration pattern for optional business interpretation. `ai_evidence.py` supplies bounded unfamiliar-schedule cells, `investment_output.py` checks cited output, and `ai_runtime.py` shares consent, reservations and usage logging across workbook interpretation, initial investment analysis and the bounded follow-up investigation. There is no new service, database, workflow wizard or agent framework.

- Discovery is based on dated headers, explicit units, dimensional Actual/Budget headers, aging buckets and narrative content. No worksheet name, Summit-specific account or answer-key conclusion selects a rule. Worksheets can be renamed without changing findings.
- Monthly observations, point-in-time balances and explicit YTD comparisons keep separate grains. YTD prior-year comparisons are never added to monthly figures. Missing cells, duplicate dates, unclear units, unsupported formulas and invalid aging totals stay unavailable rather than becoming zero.
- A sustained trend requires at least three consecutive monthly changes and a material movement: 3 pp for ratios, or at least 1 pp plus 20% relative change for low-base ratios; 10% for other measures. Pipeline growth over a longer reported window is described with intervening fluctuations, not as an uninterrupted trend. Business direction comes from broad semantic concepts or a labeled AI proposal; unknown measures remain neutral.
- Aging exposure requires nonnegative bucket values that reconcile by row, bucket and grand total, with explicit units/date. GL tie status is separate and can be unknown. Receivable concentration is not revenue concentration. An allowance comparison prompts credit review and does not declare a write-off or required accounting charge.
- Same-period financial/operating cost observations can share an evidence path; correlated movements never establish weather, pricing, procurement or staffing causation. Unit contribution is not company EBITDA, and reconciliation differences are never allocated automatically.
- Management statements are tested as scoped assertions. Limited history can disprove a record but cannot prove an all-time record. Historical-quality tests disclose their ≥1 pp and >20% relative screen; budget-alignment tests disclose an explicit ±5% screen. Compound statements can have a supported numerical component while other explanations remain unverifiable.
- Ranking is a disclosed heuristic: bounded materiality, consecutive-period persistence, investment significance and evidence quality, with core financial/data-integrity priorities. Primary themes are deduplicated; supplementary details retain their original evidence IDs. Full facts, cumulative comparisons and claim outcomes appear in the existing Financial Performance/Source Evidence sheets; the original Exceptions checks remain intact.
- Bounds: 30 worksheets, 1,000 rows and 80 columns per sheet; oversized sheets are disclosed and skipped. AI packets are capped at 80 series, 500 sampled canonical source facts, 120 financial evidence rows, 30 narrative cells and 35 candidates, with a 170,000-character packet bound, 190,000-byte request ceiling, 7,000 output tokens and a configurable 45-second request timeout. These limits are not claims of exhaustive analysis.

Development-dataset evaluation, the generality audit and remaining gaps are recorded in [the package evaluation](docs/package-evaluation.md). The original demonstration and Northstar/Harbor financial regressions are retained; `C_Northgate.xlsx` adds an additional synthetic manufacturing regression package with expectations written before its parser run. All supplied and authored packages, including Summit, are development regressions, not held-out validation. Generalization to an unseen company remains unproven. Tests block real HTTP requests even when using dummy API keys.

## AI investment analysis and disclosure

The previous implementation called an LLM only when `OPENAI_API_KEY` was configured: `engine._analyze_financials → mapping_ai.automate/suggest` proposed unfamiliar labels/layouts, and `package_analysis.enhance → analyst_ai.interpret` interpreted existing Python-selected candidates. The Investment Assessment itself was assembled by Python. The local preview was launched with the key removed; all prior validation used offline/mock responses, so no paid model inference occurred.

The extended analysis call can now propose new source-cited relationships, risks, opportunities, management questions and a concise investment briefing, rather than only annotate existing variances. The same model output feeds the current dashboard and both Excel formats. Python still extracts financials, evaluates supported source formulas, calculates/reconciles figures and checks proposed numerical comparisons. No answer key or expected company findings are runtime inputs.

The Streamlit app loads the `.env` file beside `app.py`; explicit process/shell variables take precedence. Both workbook interpretation and investment analysis use the same `OPENAI_MODEL`; stage-specific model variables are not consumed. Restart the app after changing its environment. Configure **`OPENAI_API_KEY`** securely in `.env` or the app's launch environment; never commit or paste it into chat. **`OPENAI_MODEL`** remains configurable, with the existing `gpt-4o-mini` default. Availability depends on the provider/account; no live availability or quality result is claimed without a real validation run. This uses the existing standard-library HTTP path to `https://api.openai.com/v1/responses`, strict structured output and `store: false`; no new SDK, service, agent or database is required.

For the bundled synthetic demo files, Generate automatically uses the configured AI provider without an extra checkbox. Only exact, pinned file-content matches qualify; renamed copies qualify, while modified or unfamiliar uploads do not. For other uploads, open **External analysis permission** and explicitly authorize external analysis before generation. This authorizes sending bounded extracted facts, source labels and management quotations to OpenAI; raw workbooks and answer keys are not sent. Configuring a key alone does not authorize transmission. Consent persists only for those source bytes within the current session and resets on upload replacement. The optional account-suggestion button uses the same consent gate. Provider data policies still apply: `store: false` is not a promise of zero provider retention.

Without a key, required upload consent, usable pricing/budget, or an accepted grounded response, the dashboard shows a short warning after generation, and Excel includes the analysis mode. Technical details remain in collapsed Data Quality & Coverage; model and budget controls are not shown in the main upload flow. Fallback is useful deterministic review, not a full AI investment assessment. Mocked model results are explicitly labeled as offline validation. Successful source-validated AI reviews are reused from a private, persistent JSON cache when inputs and analysis configuration match. Current-run usage on a hit is zero and the original provider receipt is retained separately. Offline fallback and failed validation are never saved as successful cache entries. Upload authorization remains required for non-demo files.

### Evidence and numerical safeguards

The model receives bounded financial totals, source-referenced time-series observations, management quotations and an additional source-cell grid for unfamiliar schedules. The grid is capped at 350 cells, 80 per worksheet, across at most 30 worksheets; it inspects the first 250 rows and leaves oversized/unsupported structures unavailable. Formula evaluation uses the existing guarded reader and explicit Excel SUM semantics. This grid supports interpretation only and never enters financial aggregation. Currency/scale, period or metric meaning can remain unknown; a source-evaluated number is not an independently validated accounting conclusion.

Each investment finding is validated independently. Rejection diagnostics identify the finding index, failing field, code, reason and invalid/uncited IDs where relevant; they appear only in the existing collapsed Data Quality & Coverage; technical diagnostics stay out of the business-facing workbook. A rejected item does not discard valid findings. The Investment Assessment is assembled exclusively from accepted finding text, qualified implications and questions; independent model briefing prose is not used. New numerical prose uses exact fact-ID placeholders. Python inserts the cited local values and units; unsupported numeric literals, unknown IDs and causal certainty are rejected. Proposed cross-sheet relationships require evidence from different sheets. AI semantic judgments and business implications remain labeled interpretations/hypotheses. A locally verified numerical comparison applies only to a literal matched management threshold with compatible metric label, company, entity, period and unit; forecasts, negation, cumulative/monthly scope mismatches and unsupported claims remain unverifiable. It does not verify the rest of a management narrative. Briefings retain paragraph citations and the source evidence remains available in the report.

Model packets retain the existing bounded series/candidate context plus a single canonical source-fact ledger; sources are sampled to stay within a 170,000-character packet and a 190,000-byte request ceiling. Up to six insights and three short briefing paragraphs are accepted. Truncation and structural limits can omit relevant facts: this is not exhaustive package comprehension or a guarantee of semantic correctness. Independent unseen-company and real-model evaluations remain necessary.

Live synthetic validation on October 20, 2026 confirmed real responses from `gpt-4o-mini-2024-07-18`, but all three investment responses failed local output/source checks. They were rejected rather than presented as full AI analysis. Six total provider requests used 134,390 input and 10,727 output tokens, estimated at $0.0266 (not an invoice charge). A real, accepted management-claim contradiction and useful model briefing remain unvalidated. See `docs/package-evaluation.md` and local `artifacts/ai-activation-verification.json`. Offline tests alone do not close that quality gap.

### Spending, timeouts and logs

| Setting | Default / behavior |
|---|---|
| `COPILOT_AI_MAX_REVIEW_USD` | `$0.10` estimated upper reservation per review, shared by automatic interpretation and investment analysis |
| `COPILOT_AI_TIMEOUT_SECONDS` | `90` per request, configurable up to `180` |
| `COPILOT_AI_MAX_RETRIES` | `0`; optionally `1`, only for explicit HTTP 429; timeouts and ambiguous network failures do not retry |
| `OPENAI_INPUT_USD_PER_M`, `OPENAI_OUTPUT_USD_PER_M` | Both required for an unrecognized model; positive configured USD per million token rates |

Before each attempt, Python reserves a pessimistic byte-based input-token ceiling plus the configured maximum completion (3,000 mapping / 7,000 analysis tokens). All attempt reservations remain charged to the review cap, including failures and retries. No request starts if it would exceed that estimated limit. This is application-side reservation under configured prices, not an independently enforced provider billing quota; provider project limits remain appropriate for total account spend.

The built-in uncached list-price estimates are `$0.15` input / `$0.60` output per million tokens for `gpt-4o-mini`, and `$0.40` / `$1.60` for `gpt-4.1-mini` (including their documented snapshots), checked against [official model pricing](https://developers.openai.com/api/docs/models/gpt-4o-mini) and [GPT-4.1 mini pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini). `gpt-6-luna` uses documented standard rates of $0.10 input / $0.50 output per million tokens, with $0.01 cache reads and $0.125 cache writes where the provider reports those counters. Its reservation includes the higher cache-write rate. Unavailable configured models produce an explicit error; no fallback model is selected. Rates can change and overrides are operator-owned; these are estimates, not invoices. Missing usage or an unrecognized returned model has unknown estimated actual charge and retains its upper reservation.

The normal Python logger emits `copilot_review` and `copilot_inference` JSON metadata: review ID, timestamp, requested/returned model, whether a provider response completed, phase, attempts, reported token usage when available, approximate token counts, request latency, response/incomplete status, reservations, estimated cost and exact failure types. Real responses and item-level rejection diagnostics are retained privately under `.local/analysis-diagnostics/`, including failures, without needing another paid request. Logs do not contain source data, prompts or credentials. The same metadata is inspectable in collapsed Data Quality & Coverage and exported supporting sheets. A completed provider response can still fail source checks; that event remains logged while the report clearly falls back.

## Excel exports

The standard workbook retains **Executive Summary**, **Financial Performance**, **Exceptions**, and **Source Evidence**. Available metrics stay numeric, with period, company, units and definitions. Readiness and accounting limits are outside the Exceptions sheet. Company and report-period labels and filenames come from the current review.

Upload `sample_templates/Sample_Firm_Review_Template.xlsx` or choose the supplied sample in setup. Explicit `{{FIELD}}` tokens are filled in a copy. Original sheets, merged cells, formulas (including `C16`), and formatting remain intact; the Template Guide remains documentation. Supporting sheets are appended; existing supporting content is preserved. Unknown placeholders remain visible with a warning.

The original fields remain supported: `COMPANY_NAME`, `REPORT_PERIOD`, `PLATFORM_REVENUE` (compatibility alias for a single company's revenue), `GROSS_MARGIN_ACTUAL`, `GROSS_MARGIN_BUDGET`, `LEVERAGE_REPORTED`, `LEVERAGE_CAP_ONLY`, `COVENANT_MAX`, `SUBCONTRACT_ACTUAL`, `SUBCONTRACT_BUDGET`, `FINDING_COUNT`, `FINDING_1`–`FINDING_3`, `PARTNER_BRIEF`, and `CFO_Q1`–`CFO_Q3`. Generic templates may also use `REVENUE`, `GROSS_PROFIT`, `OPERATING_EXPENSES`, `EBITDA`, `NET_INCOME`, `CURRENCY`, and `ACCOUNTING_BASIS`.

Unsupported fields are marked unavailable. Monetary template fields remain unavailable if currency/scale is unconfirmed; source-unit values are still available in supporting sheets. For confirmed non-USD data, explicit dollar number formats in populated cells are relabeled to the stated currency with a warning, without currency conversion. Formulas are never overwritten. Every output is reopened and checked against calculated values, findings/evidence, mapped fields, sheet presence and preserved formulas/styles before download.

## Verification and development examples

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Two synthetic financial regression workbooks are in `tests/fixtures/`. Expected results were recorded in [expected_adaptive.json](tests/fixtures/expected_adaptive.json) **before ingestion implementation**, independently of the three demo workbooks:

| Example | Different structure | Expected results |
|---|---|---|
| `A_Northstar.xlsx` | Trading results, labels in B, actual/budget/prior/prior-year in C:F, USD thousands, April 2027 | Revenue $1,000,000; GP $500,000; margin 50% vs 54% budget; reported EBITDA $320,000; prior revenue $900,000 |
| `B_Harbor.xlsx` | Multi-sheet QB-style report, GL codes in A, descriptions B, data D:E, cash basis whole USD, February 2027 | Revenue $400,000; GP $200,000; opex $92,000; net income $94,000; EBITDA $118,000 from explicit components; reserve requires review |

Tests cover recorded development expectations, mapping correction and reuse, totals/subtotals, missing/dashed values, sign presentation, unknown basis/units, reconciliation mismatches, multiple monthly statements, separate companies, both Excel formats, model request/response validation, and the original full/partial demo regressions. The optional live model call has not been exercised without an API key.

With the app running, the existing `tests/browser_smoke.py` verifies the original demo and partial uploads. `tests/browser_adaptive.py` verifies actual new-company uploads, human mapping correction, persisted reuse, evidence navigation and standard/custom downloads using locally installed macOS Chrome (adjust its executable path on another platform). Use an isolated mapping store for that test:

```sh
PORTFOLIO_MAPPING_PATH=/tmp/portfolio-copilot-test-mappings.json .venv/bin/streamlit run app.py --server.address 127.0.0.1
# In another terminal:
.venv/bin/python tests/browser_adaptive.py
.venv/bin/python tests/browser_smoke.py
```

For the first adaptive browser run, choose a fresh test mapping file so Harbor's optional correction and saved-mapping reuse can be tested. Downloaded workbooks, browser results and screenshots are written to ignored `artifacts/`.

The original demo still calculates revenue $5,383,752; actual/budget margin 27.8313% / 34.5232%; leverage 4.2872x / cap-only 4.4645x; potential billing exceptions $27,978.75. Its platform accrual and add-on cash-basis numbers are not consolidated. The independent planted-issues answer key was absent from the supplied handoff and has never been read or added to runtime context.

See [the pre-change audit](docs/ingestion-audit.md) for the original coupling and retained-component boundaries.

## Summit upload regression (Task20)

`tests/fixtures/Summit_Home_Services_Sep2026.xlsx` is the supplied synthetic workbook. It generates without account approvals: September revenue $3,298,000; gross profit $1,433,000; EBITDA $502,000 against $659,000 budget; net income $183,000. The $47,000 branch-versus-consolidated difference is flagged without allocating it to a branch. These are test expectations, never runtime overrides. Changed-source tests verify recalculation.

Summary/monthly-detail overlap is corroborated by metric and used once, never summed. Conflicting metrics are withheld while other metrics continue. Branch/entity columns are treated as dimensional comparisons, not duplicate consolidated periods. Monthly and YTD columns are not mixed. Dollar units are recognized without inferring USD jurisdiction; unstated accounting basis is disclosed. Within-workbook comparisons are as reported; cross-workbook comparisons require comparable stated basis and units. The package extension now reads conventional operating time series, business-unit Actual/Budget grids, reconciled receivables aging and management narratives by content. Recognized facts, analysis coverage and unavailable/ambiguous measurements are reported explicitly. Numerical claim outcomes are scoped to the tested assertion; future recovery, weather causation, losses and reserve adequacy are not automatically established.

Offline tests cover immediate generation, optional corrections, partial uncertainty, source changes, source/AI reconciliation, rejected fabricated periods, both Excel modes, and the unchanged event-staffing demonstration. Live AI calls are not part of verification.

### Validation repair verification — October 20, 2026

A free model-access check returned HTTP 200 for `gpt-6-luna` using the `.env` key.
The older six-request diagnostics preceded the Luna configuration change; the
previous app did not load `.env`, so its unset model selected the mini default.
The repaired app records model origin and uses the configured model in both stages.

One large synthetic Tallis review completed workbook interpretation with Luna,
but investment analysis failed before a response; its token usage and billed cost
are unknown. It was not resubmitted. A bounded live run on the existing small
synthetic Example Group package then completed investment analysis with Luna:
three generated findings, three accepted, zero rejected. The source-linked revenue/
EBITDA comparison, scoped completion-claim check and regional completion comparison
appeared in the actual Streamlit dashboard and downloadable standard/custom Excel.
The standalone model briefing was excluded and rebuilt from accepted findings.
Provider usage was 3,088 input and 2,979 output tokens, including 1,398 cache reads
and 1,687 cache writes; estimated standard-list cost was $0.001714655. Actual invoice
charges are unavailable. These synthetic checks do not establish reliable acceptance
or latency for the larger Tallis package. Its unstated accounting basis remains unknown.

### Full-workbook and persistent-cache verification — October 20, 2026

Full Tallis analysis now passes: four accepted AI findings reach the dashboard,
accepted-only Investment Assessment and Management Questions, and standard/custom Excel.
The investment response took 45.1 seconds, exceeding the previous 45-second
request timeout; the bounded default is now 90 seconds. The independently
written model briefing failed its length check and was excluded, without losing
valid findings. The final briefing is assembled only from accepted findings.

The original demo exposed a separate ledger mismatch: numeric evidence records
supplied to the model were missing from the canonical facts checked by the
validator. Those locally validated numeric records now retain the same IDs in
that ledger; monetary units require a matching source cell. Textual notes do not
become numerical facts. Narrow checks also distinguish exact source entity IDs
and explicit denials of established causation from unsupported figures/assertions.
Fabricated references, raw financial figures and asserted causes remain blocked.
Saved genuine responses were revalidated locally without additional model calls.

`report_cache.py` stores complete validated reviews as owner-private atomic JSON
under `.local/analysis-cache/`; it uses no database or executable serialization.
Keys include file-content hashes and filenames (for citation provenance),
provider/model, prompt and analysis source versions, validation/runtime settings,
mapping decisions/profiles, authorization, and a credential-scope fingerprint.
Changed sources or relevant configuration invalidate reuse. Exports are regenerated
from the cached review, retaining original source references and template formulas.
No cache controls or technical settings were added to the interface.

Real GPT-6 Luna preparation and fresh Streamlit/browser restart checks:

| Dataset | Generated / accepted / rejected | Initial analysis | Cached Generate | New cached API calls |
|---|---|---|---|---|
| Original Platform A / Add-on B | 5 / 2 / 3 | 57.6 s | 1.1 s | 0 |
| Summit Home Services | 4 / 4 / 0 | 52.6 s | 2.2 s | 0 |
| Tallis Brook Accounting | 4 / 4 / 0 | 69.7 s | 2.3 s | 0 |

Provider requests were blocked during restart verification. Standard/custom
workbooks matched the validated source evidence, findings, briefing, Management Questions
and financial values; current-run inference metadata correctly reports zero calls.
Actual changed-source cache misses were verified for all datasets. Final offline
suite: **225 tests passed**. Four real preparation requests used 122,399 input and
15,658 output tokens, estimated at $0.021870705 including reported cache counters;
actual invoice cost is unavailable. The original demo still rejects three findings
for unsupported literal prose or a text-only reference supplied as a numerical fact.
Unstated accounting basis and unsupported extraction/claim scope remain uncertain.
Local evidence: `artifacts/p1-demo-cache/final-verification.json`.

### Investment-team Excel report

The Executive Summary presents financial KPIs, up to three accepted priority findings,
an **Investment Assessment**, and **Management Questions**, with a subtle
“For Investment Team Review” notice. Accepted AI findings supply both dashboard and
workbook conclusions; additional accepted findings remain on the Findings worksheet.
Supporting deterministic checks are retained separately in Exceptions.

Financial Performance separates actuals, budget, variances, same-month prior-year
and immediately preceding-month comparisons, with explicit dates and units.
Unavailable or incompatible comparisons remain blank. Extracted Detail retains
underlying financial and operating records; Data Quality contains material limitations.
Findings link to their Source Evidence records, which retain original filenames,
worksheets, cells, source values/formulas and validated values, with return links.
Technical inference and rejection diagnostics remain outside the business workbook.
Custom-template mappings, formulas and styles continue to be preserved, including
legacy placeholder names for compatibility.

### Frozen company-context and reliability verification

The current development regression passed **277 tests**. Fresh GPT-6 Luna runs verified source-backed summaries for Harrow Ridge, Tallis Brook and Summit, alongside accepted investment findings and both Excel export formats. Descriptive profile gaps fall back to exact validated source revenue captions and explicit operating-unit labels; unstated attributes remain omitted. Full results, costs, rejection reasons, source coverage and remaining limitations are in [the frozen evaluation report](artifacts/general-reliability-v4/REPORT.md). Prior baselines are preserved.

## Experimental skill analyst

The legacy engine remains the default. To try the single-workbook PE Investment Analyst v2 workflow:

```sh
./scripts/run_skill_demo.sh
```

The feature flag exposes an explicit legacy fallback. Skill runs use the existing model, consent and spending controls; failures are disclosed and never masquerade as completed skill assessments. See [implementation and limits](docs/skill-engine.md), [module migration map](docs/skill-engine-migration.md), and [benchmark results](docs/skill-engine-benchmark.md). No public deployment is included.

The [development checkpoint guide](docs/skill-engine-checkpoint.md) explains how to
verify and seed the three approved synthetic results in another checkout without
API calls. Ignored caches and credentials do not follow Git branches.
