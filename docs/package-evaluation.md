# Full-package analysis: development evaluation and generality audit

## Validation boundary

Summit Home Services is a **development dataset**. Its answer key was read only after the initial source-based analysis was generated, but subsequent development used that knowledge. Neither Summit nor the synthetic Northstar, Harbor and Northgate regression fixtures is a held-out validation set. Passing these tests does not establish generalization. The planned unseen-company evaluation must be run separately, without tuning to its answers.

The runtime does not read an answer key. Company names, filenames, sheet titles, debtor names and planted dollar figures do not select new analytical rules. Source labels and references remain in evidence, and company identity is used to prevent inappropriate consolidation. The original demo's explicitly guarded legacy covenant/billing adapters remain for compatibility; those specialized formats are not claimed to work on arbitrary companies.

## Final overfitting audit

Reviewed the added reader, deterministic analysis, optional model packet/response validation, and changes to the financial wrapper, dashboard and exports. Removed:

- A section-caption shortcut that discarded budget columns after an operating-KPI heading. Explicit populated scenario columns now determine availability.
- Handpicked plural substitutions for development-package terms; conservative English plural normalization applies uniformly, and ambiguous matches remain unverifiable.
- A seasonal-demand reference, temporary-labor explanation and fixed covenant month in new generic narrative code.
- Industry-specific staffing/service assumptions and an unsupported assumption about new sales sustaining a customer base.

Also corrected general reporting defects: falling collection measures cannot be described as increasing, and a known aging/GL mismatch stays in the concise executive card. These changes do not add detectors for answer-key issues. Existing general trend, commentary, reconciliation, receivables and unit-performance methods are retained.

Additional negative/value-variation tests use generic CSVs and a dimensional schedule: different companies with improving, worsening, flat and fluctuating values; unknown KPI vocabulary; and actual/budget data under arbitrary captions. Renamed worksheet tests retain source references without relying on original tab names. These are regression checks, not an unseen-company benchmark.

## What the system actually analyzes

- Conventional monthly P&L actual/budget comparisons, reported totals, source arithmetic, margins and material expense movements through the existing financial engine.
- Dated numeric schedules with recognizable units: consecutive monthly trends, selected longer-window growth, and evidence-linked observations. Explicit cumulative prior-year financial comparisons are kept separate from monthly facts.
- Conventional dimensional Actual/Budget grids: unit contribution comparisons and associated operating measures, without allocating consolidated reconciliation differences or equating contribution with EBITDA.
- Explicit customer receivable aging: row/bucket/total reconciliation, over-90-day balances, receivable concentration, available ledger tie and allowance evidence. These are exposures, not proven losses or revenue concentration.
- A small set of scoped narrative assertions: record highs, latest increases, majority-current balances, stated cost/budget alignment and certain historical-consistency claims. Unsupported causes, forecasts and compound narrative explanations remain unverified.
- Optional AI interpretation of unfamiliar KPI meaning and candidate business significance. The model receives bounded cited facts; local code calculates numbers and claim outcomes. AI semantic judgments are labeled hypotheses, not independently verified financial facts.

Financial calculations and source traceability remain deterministic. Main findings are deduplicated into at most three themes, with additional observations and commentary checks available separately. The same presentation and source ledger feed both Excel modes.

## Summit: development observations, not an accuracy score

| Area | Current capability and remaining limit |
|---|---|
| Revenue ahead of budget / EBITDA shortfall | Source amounts and variance are detected; cost ratios and financial detail share an evidence path. Pricing pass-through and causal attribution are not established. |
| Persistent overtime increase | Monthly persistence is observed. Weather or a one-time explanation cannot be proved or disproved solely from that series. |
| Unit contribution and quality | Unit shortfall and peer quality measures are available. Contribution is not allocated company EBITDA; the separate reconciliation discrepancy limits attribution. |
| Renewals and active customer base | Retention trend, a reconciling latest cohort movement and a scoped record-claim contradiction are available where source identity/periods match. |
| Receivables | Aged counterparty exposure, available allowance and DSO evidence are available. Reserve adequacy, recoverability and a broad claim that collections are “solid” are not established. |
| Branch/consolidated reconciliation | Existing financial reconciliation exposes the discrepancy separately from business performance. It does not diagnose or repair its cause. |
| Positive developments | Source-supported ticket, backlog, unit and cumulative financial improvements can appear as positive observations. Their future conversion, profitability and sustainability are unverified. |

## Important limitations for the unseen-company evaluation

This is not universal workbook comprehension. Horizontal dated tables, explicit units/scenarios and conventional aging structures are required. Transposed tables, interleaved schedules, inconsistent units, mixed accounting definitions, ambiguous entities, unsupported formulas or narrative-only claims may remain unavailable. Coverage indicates recognized structures, not a completeness or audit opinion. Review the disclosed per-sheet coverage and source evidence before relying on conclusions.

Vocabulary-based metric direction and screening thresholds are heuristics. Unknown offline KPI meanings remain neutral; industry-specific economics can invalidate a generic interpretation. Ranking is not independently calibrated, and model citation/schema checks do not establish semantic truth. Narrative verification is deliberately narrower than general fact-checking. No weather, pricing, staffing or customer-loss causation is inferred from correlation. Working-capital coverage is primarily receivables, not a complete cash-flow, inventory or payables analysis. Company-wide concentration is not inferred from receivable balances.

Bounds are documented in README. The optional live model integration was tested with mocked responses and failures only; no paid provider requests were made. Offline regressions cannot validate real-model interpretation quality. An unseen third-company package and live-model quality remain unevaluated.

## Verification

Final offline regression: **147 passed** (`python -m pytest -q`, 33.34 seconds). All three browser scripts passed: `browser_smoke.py`, `browser_adaptive.py`, and `browser_summit.py`.

Regression results and browser evidence are recorded in `artifacts/task22-final-verification.json` locally. Tests block provider HTTP calls. Browser checks run with the API key removed and an isolated mapping store. They cover the original full/partial demo, Northstar/Harbor uploads and optional mapping reuse, Summit development upload, evidence navigation, responsive results and standard/custom Excel downloads.


## Subsequent recognition regression

Tallis Brook's initial blind recognition failed: the fallback counted raw numbers but not safely evaluated formula totals; generic financial headers and fee-revenue/reported-EBITDA labels were missed; “US dollars” was not recognized; acquisition dates were mistaken for financial periods. The recognition fix uses source content, not company or sheet names, and automatically recovers September 2026 revenue of $3,475,418 and reported EBITDA of $684,306. After this change Tallis is development regression data. The earlier test totals above describe the prior analytical-depth release; current recognition verification is recorded separately in local `artifacts/recognition-verification.json`.

Currency/scale inference now uses explicit denomination text, consistent same-company mastheads and currency formats with source references. Missing accounting basis remains unknown. Negative tests cover absent metadata, conflicting units/bases, blank future columns, populated contradictions, renamed companies/tabs and model proposals that cannot invent dates or ordinary EBITDA. Source units permit partial analysis and Excel export without approval. Remaining layout and schedule limits are documented in README; this change does not claim comprehensive extraction of every Tallis supporting table or validate its management narrative in full.


## AI activation validation boundary

The original analyst helper only annotated deterministic candidates and the briefing remained templated. The extended helper can propose new cross-sheet insights and source-cited briefing paragraphs. Generic synthetic tests pass a management assertion and an independently extracted KPI from different worksheets through the structured model contract; Python verifies the contradictory numerical predicate, persists its source references and exports the briefing. Negative tests reject invented figures/IDs, causal overclaims, fabricated quotations, mismatched periods/entities/units and negated claims. This proves the contract and local verification, **not real-model discovery or narrative quality**.

The key was subsequently supplied through the local app's ignored `.env`. Three explicitly authorized synthetic Tallis validation runs completed six real requests (workbook interpretation and investment analysis), returning `gpt-4o-mini-2024-07-18`. Total provider-reported usage was 134,390 input and 10,727 output tokens, estimated at $0.0265947 using configured uncached list rates; this is not a verified invoice charge. No confidential uploads or answer keys were sent.

**Live analysis acceptance failed.** The model repeated narrative claims as facts, cited unavailable or inappropriate evidence IDs, supplied literal unsupported figures, and/or violated the scoped output contract. All three investment responses were rejected; the visible limited-analysis fallback and both Excel formats remain functional. A bounded general prompt/schema clarification added field descriptions and a neutral placeholder example without relaxing validation, but did not establish an accepted real cross-sheet contradiction or useful model briefing. Those acceptance criteria remain unmet; connectivity is not proof of analytical quality. No further paid tests were run. Tallis remains a development regression package, not independent validation.

Current activation verification: **195 offline tests passed** (41.33 seconds), including 52 focused AI/package tests (5.41 seconds). Previously completed original-demo, Summit and Tallis browser regressions include standard/custom Excel. A fresh browser check confirmed that the restarted preview recognizes the credential while per-upload consent defaults off. Local metadata evidence: `artifacts/ai-activation-verification.json`. External financial processing still requires per-upload authorization; the synthetic development permission does not cover confidential workbooks.
