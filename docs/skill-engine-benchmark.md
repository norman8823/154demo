# Current company demo benchmark

All three final-code company runs completed fresh inference and passed independent numerical, Streamlit and both-format Excel checks. This section records tonight’s fresh application executions. The historical six-attempt experiment and its offline replay are preserved below; neither is counted as a fresh success tonight. Keep the global default legacy.

Runtime receives only the uploaded workbook, packaged PE Investment Analyst v2 and its own workbook-tool results. Standalone assessments and evaluation materials were read only after inference and never entered the runtime. Each run uses the real `engine.analyze(..., engine_name="skill")` application entry point and saves new immutable artifacts.

## Final company results

| Run | Status | Seconds | Estimated USD | Source / UI checks |
|---|---|---:|---:|---|
| harrow-17-final | completed | 570.87 | 0.054162 | passed |
| summit-05-final | completed | 457.71 | 0.052951 | passed |
| tallis-05-final | completed | 401.85 | 0.039618 | passed |

## Configuration and receipts

The demo launcher uses the existing configured model, high reasoning, 32,000 response tokens, 14 rounds, 160 tools, 900 seconds overall and a 300-second request timeout. A response allowance includes reasoning tokens: the 16,000-token high-reasoning trial used 15,118 for reasoning and could not finish its JSON. Final identities are `skill-analyst-4`, `workbook-tools-2`, `skill-output-4` and packaged `pe-investment-analyst-v2`; resource hashes are in each receipt. No stronger model was substituted. Defaults remain separately documented in `skill-engine.md`.

Rates per million tokens: input $0.10, output $0.50, cached reads $0.01, cache writes $0.125. Verified against [official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna). Receipts include provider cache and reasoning usage where reported. These are standard-rate estimates, not invoices or cold-cache forecasts.

Known token-based estimates across tonight’s saved runs: **$1.246230**. The persistent ledger conservatively commits **$1.305949 / $2**, including **$0.071784** retained for unknown/incomplete requests. The $0.25 analysis ceiling was enforced before each request. Unknown timeout charges are not reported as zero. The approximate $0.01 target was not established.

| Run | Status | Seconds | Input / output | Cached input | Tools | Known estimate USD | Conservative commitment USD |
|---|---|---:|---:|---:|---:|---:|---:|
| harrow-01 | partial | 398.87 | 445,113 / 38,516 | 55,111 | 74 | 0.068557 | 0.068557 |
| harrow-02 | failed | 246.13 | 118,541 / 5,390 | 87,672 | 31 | 0.007430 | 0.028978 |
| harrow-03 | partial | 274.67 | 322,593 / 24,028 | 80,078 | 55 | 0.043128 | 0.043128 |
| harrow-04 | completed; withdrawn | 332.63 | 369,151 / 25,461 | 68,264 | 67 | 0.051021 | 0.051021 |
| harrow-05 | failed | 337.54 | 239,369 / 12,019 | 70,656 | 60 | 0.027805 | 0.053026 |
| harrow-06 | partial | 367.64 | 364,375 / 29,705 | 47,650 | 63 | 0.054919 | 0.054919 |
| harrow-07 | partial | 283.46 | 285,074 / 21,474 | 92,380 | 54 | 0.035747 | 0.035747 |
| harrow-08 | partial | 367.27 | 358,589 / 27,421 | 128,878 | 62 | 0.043712 | 0.043712 |
| harrow-09 | partial | 335.45 | 403,391 / 24,896 | 162,174 | 63 | 0.044219 | 0.044219 |
| harrow-10 | partial | 213.71 | 184,934 / 17,960 | 45,358 | 43 | 0.026880 | 0.026880 |
| harrow-11 | completed; withdrawn | 279.63 | 407,097 / 24,409 | 137,021 | 60 | 0.047331 | 0.047331 |
| harrow-12-high | failed | 275.91 | 314,798 / 39,048 | 94,927 | 68 | 0.047956 | 0.060904 |
| harrow-13-high | partial | 326.31 | 399,497 / 44,286 | 111,208 | 66 | 0.059288 | 0.059288 |
| harrow-14-high | completed | 310.63 | 294,588 / 46,440 | 49,272 | 69 | 0.054376 | 0.054376 |
| harrow-15-final | partial | 341.06 | 390,438 / 45,888 | 139,218 | 59 | 0.055736 | 0.055736 |
| harrow-16-final | completed; withdrawn | 441.75 | 355,462 / 63,265 | 53,154 | 57 | 0.069950 | 0.069950 |
| harrow-17-final | completed | 570.87 | 295,501 / 44,677 | 44,461 | 59 | 0.054162 | 0.054162 |
| summit-01 | partial | 276.35 | 314,665 / 22,435 | 109,052 | 74 | 0.038007 | 0.038007 |
| summit-02-high | partial | 312.08 | 203,508 / 45,856 | 47,885 | 56 | 0.042859 | 0.042859 |
| summit-03-final | completed | 314.49 | 202,173 / 43,867 | 74,416 | 59 | 0.038647 | 0.038647 |
| summit-04-final | partial | 475.14 | 352,896 / 66,556 | 66,301 | 79 | 0.069763 | 0.069763 |
| summit-05-final | completed | 457.71 | 296,967 / 46,204 | 63,213 | 63 | 0.052951 | 0.052951 |
| tallis-01 | partial | 340.04 | 303,376 / 29,255 | 72,457 | 70 | 0.044214 | 0.044214 |
| tallis-02-high | completed; withdrawn | 291.29 | 180,151 / 44,528 | 44,811 | 52 | 0.039629 | 0.039629 |
| tallis-03-final | partial | 328.20 | 228,857 / 44,646 | 54,717 | 50 | 0.044637 | 0.044637 |
| tallis-04-final | completed | 301.56 | 216,518 / 43,561 | 44,827 | 57 | 0.043689 | 0.043689 |
| tallis-05-final | completed | 401.85 | 183,747 / 41,255 | 34,570 | 56 | 0.039618 | 0.039618 |

Each directory under `artifacts/skill-engine-tonight/` contains the original result, review, findings, view and both Excel files; successful final runs additionally contain `verification.json`, `render-check.json` and an independent `quality-review.json`. `evaluation.json` consolidates results, while `budget.json` is the authoritative locked authorization ledger. Raw provider responses are private diagnostics under `.local/analysis-diagnostics/`.

## Fixes and interpretation

Full coverage no longer forces finalization after a single calculation batch. One analyst can follow cross-sheet hypotheses, with finalization and one indexed repair reserved. Five relevance-based completion checks address claims, cash/reinvestment/debt, earnings quality, customer/operating exposure and decisions/uncertainty/positives. Accepted siblings survive failed repairs as PARTIAL; dependent summary/questions/exports are rebuilt from accepted claims only. Partial reports never enter the completed cache.

Generic fixes include scaled percentage points, DSO/day conventions, Excel SUM blank semantics, per-unit currency scale, source-bound fiscal/entity/aging descriptors, all-field repair diagnostics and bounded negation handling. Numerical/source/quote/unit/affirmative-causation failures still reject a finding. The adapter deterministically adds illustrative labels from tool provenance; it does not require a model keyword to classify a recorded calculation. Concise prose targets remain in the schema, with a160-word hard publication bound per prose field (titles keep their short bound); exceeding a target records a warning without silently truncating verified claims. Lexical uncertainty is advisory: unclear qualification gets an explicit investment-team-review caveat and diagnostic, not a false numerical rejection.

Harrow04 was withdrawn for an unscaled percentage-point result. Harrow07 selected average vehicle age as a numerator for unavailable trucks. Harrow11 passed arithmetic/source validation but used a valid calculation with the wrong economic inputs in its cash narrative, and described the adjustment components imprecisely; its cache was quarantined. Harrow16 omitted a contract exactly on the next fiscal-year boundary and mislabeled the selected subtotal as the eligible cohort; it was also withdrawn. The final generic methodology requires explicit date boundaries, inclusion of endpoints and reconciliation of every source row, with no workbook-specific values. These are preserved failures of semantic reliability. Deterministic checks do not prove denominator meaning, economic scope, causal explanation or analytical completeness.

## Independent analytical review

### Harrow — complete, with specific omissions

The final fresh Harrow17 report derives $2.3m CFO after cash capex (23.7% of EBITDA), negative $0.7m after principal, $7.3m economic asset deployment kept separate from repayments, and the $2m increase in net debt. It correctly includes the fiscal-endpoint contract in the $5.7m/12.2% disclosed next-year renewal subtotal. It calculates the $10.312m fee-only earnings sensitivity after excluding $1.145m commodity/rental adjustments, East’s $119,292 quarterly cost proxy, and North’s 4.1% physical tons-per-route-day improvement versus14.1% revenue-per-route-day growth. South’s22.2% unavailable fleet,5.9pp downtime deterioration and33.9% maintenance increase are correct. Manual review and independent reconstruction found no material numerical error in the final accepted report.

Depth is substantially better than the historical offline replay. Relative to the standalone assessment, it still lacks a South replacement/rebuild funding scenario, the partial-year contract repricing illustration, independent commodity-normalization reconstruction and a North capital-return assessment. Some prices exist only inside text notes; the restricted tool does not turn those into typed monetary inputs, which prevents safe count-times-unit-price scenarios. No Python execution environment was added. Repair estimates, collection evidence and contractual pass-through support remain genuinely absent. These omissions remain visible limitations; deterministic checks do not certify scope or narrative truth.

Harrow16’s incomplete fiscal-boundary aggregation and Harrow11’s incorrect cash-comparison inputs are preserved as withdrawn results. Harrow14 was an earlier valid fresh report; it is not substituted for the final-code run. The high-reasoning results are encouraging, but the development sequence was not a controlled model experiment.

### Summit — complete

The final report detects YTD margin/cost pressure beyond the untested September weather explanation, overdue builder concentration and higher DSO, weaker renewal cohorts beneath new sales, Lakeshore’s contribution/service indicators and the separate$47k branch/consolidated reconciliation. It derives the78.5% weighted renewal ratio and identifies that September’s active base is below August’s record. It keeps revenue/ticket/backlog improvements and states that monthly cohort events are not unique customers. Costs, branch contribution and company EBITDA are not added together as separate losses. No material numerical error was found in manual source review or independent reconstruction.

Remaining gaps include a funded branch recovery case, causal staffing/job-cost analysis, cohort revenue and lifetime-value implications, and a complete organic/perimeter bridge. Invoice-level collectibility, cohort pricing/cancellations and customer-level retention data are absent, so forward losses are appropriately unquantified.

### Tallis — complete

The final report identifies the$1.395m YTD EBITDA shortfall; separates$1.826m of pre-acquisition/future-compensation adjustments from other unverified addbacks; and computes a$6.116m illustrative alternative to management’s$7.941m pro forma figure. Redfern’s realization, write-down concentration,$555,100 over90-day WIP and153.1-day lockup are quantified. Ashcombe’s98 lost clients from610,83.9% count retention versus94.0% firmwide, and$634k listed historical relationship fees challenge the transition claim without calling them forecast lost revenue. Acquisition perimeter is separated from the favorable5.6% legacy-month growth observation. Client counts and days now retain correct units. No material numerical error was found in final review or reconstruction.

The aging narrative could name its over90-day threshold more clearly; it does not separately isolate over120-day WIP or aged AR. Staffing/utilization/rate-driver depth remains limited. Partner compensation is part of direct costs, so the listed pressure points must not be added again. A full comparable YTD organic bridge, engagement-level collection evidence and a forecast are not supplied by the workbook.


## Verification and recommendation

Final source verification reconstructs the tool trace, recalculates source facts and calculation dimensions, checks cited IDs/quotes, and reopens both Excel formats. Streamlit AppTest loads each company through the actual selector and completed cache with HTTP blocked, checks dashboard titles and evidence navigation, and regenerates the supplied custom template while preserving C16. Cache hits are presentation checks, never fresh inference measurements. Excel checks cover usable sheet contents, links, wrap/row sizing and formula preservation; mapped template narrative rows expand while styles, merges, widths and formulas remain intact; no desktop Excel/PDF visual fidelity claim is made.

The final full regression suite passed **343 tests in123.59seconds**, followed by the company-selector, evidence and export checks. The UI-only cache correction normalizes generated header-reference provenance; real mapping edits remain distinct. All three completed reports are cached under the final analytical identity. Recommend a curated opt-in company demo and broader controlled reliability testing before changing the default. Do not infer production reliability from eventual success after many development attempts. Restricted tools were sufficient for the relevant bridges, comparisons and sensitivities; arbitrary Python and orchestration are not justified. No public deployment or portfolio rollup was built.

# Historical integration experiment — before tonight’s fixes

The feature-flagged engine is implemented, but **fresh unattended completion is not yet proven**. Keep the legacy engine as default. Six development attempts were preserved as failures; the final saved model response passes the corrected source/wording validation in an offline replay. Replay is a regression check, not a new successful inference benchmark. No further paid calls were made after the final attempt.

## Inputs and separation

Source: `Harrow_Ridge_Environmental_FY2026.xlsx`, SHA256 `bdd9c427e57f4c55fa4a135a0126bd25f5fbdae5781b7c192067bbb937788efb`. The workbook explicitly identifies itself as fictional/synthetic; its content hash was already in the application's external-processing allowlist. Execution used `engine.analyze(..., engine_name='skill')`, the entry point called by Streamlit, with existing model/configuration and authorization controls.

Runtime received only packaged methodology, the uploaded workbook and its own tool results. It did not receive prior findings, evaluation keys, standalone scripts or comparator outputs. After paid execution stopped, the preserved `artifacts/harrow_ridge_fy2026` assessment/evidence and existing `artifacts/general-reliability-v4/harrow/evaluation.json` were inspected independently. No Harrow-specific expected answers or exact finding count were added to runtime prompts, tools or tests.

Run receipts, review snapshots and both Excel formats are under `artifacts/skill-engine-harrow/run-01` through `run-06`. Original failed results remain unchanged and were not saved as successful production cache entries. `revalidated-06` preserves an intermediate failed offline replay; `revalidated-06b` contains the completed offline replay, numerical check, UI check and regenerated exports. These local artifacts are git-ignored; preserve them separately when sharing benchmark evidence.

## Measured execution

Configured model: `gpt-6-luna`; methodology: packaged PE Investment Analyst v2; engine/tool/schema versions and resource hashes are in each receipt. Rates per million tokens: input $0.10, output $0.50, cached read $0.01, cached write $0.125, as recorded from the existing configuration and checked against [official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna). These are estimates, not billing invoices. Cached reads materially affect these measurements; do not extrapolate them to cold starts.

| Attempt | Seconds | Provider responses | Tool calls | Input / output tokens | Cached input | Estimated USD | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|
| 01 | 2.70 | 0 | 0 | unknown | unknown | unknown | Network failure; $0.006753 upper reservation retained |
| 02 | 52.78 | 4 | 32 | 153,565 / 4,070 | 96,439 | 0.010140 | Expanded tool history exceeded request byte limit |
| 03 | 66.50 | 5 | 36 | 124,733 / 5,298 | 21,861 | 0.015726 | Repeated calculation requests exhausted conservative reservations |
| 04 | 109.98 | 4 | 26 | 85,191 / 8,592 | 50,130 | 0.009178 | Final response hit the then-configured 6,000 output-token cap |
| 05 | 137.97 | 5 | 28 | 127,406 / 15,574 | 17,631 | 0.021681 | Bounded repair still failed validation |
| 06 | 121.79 | 5 | 24 | 94,842 / 9,205 | 39,784 | 0.011880 | Completed response had validation rejections; repair blocked by remaining spend cap |

Across these attempts, known token-based estimates total **$0.068606**. Including the unknown first request's reservation and retaining the incomplete fourth response's upper reservation gives **$0.087171** of conservative commitments within the existing $0.10 development allowance. Later review ceilings were reduced as the allowance was consumed; run 06 used $0.0247. This is not a controlled repeated-trial experiment at identical settings. The approximately $0.01 target has **not** been demonstrated: even the final failed attempt cost about $0.01188.

Changes prompted by failures were generic: lossless context compaction; one targeted calculation pass then forced finalization; settlement of known completed token usage; a 10,000 output-token ceiling; and validators that distinguish historical arithmetic from sensitivities, capitalization-only quote differences, negated causation, supported fiscal-year labels and explicit evidence uncertainty. Each change is independent of Harrow's answer key. No incomplete provider response was treated as a completed assessment.

## Numerical support and reasoning

Offline replay used the five original run-06 responses unchanged in analytical content, with networking blocked and simulated current usage set to zero. Original paid receipts remain separate. All five proposed findings were accepted after generic validation fixes. This does not prove that a new model run would behave identically.

Independent tool reconstruction recomputed **2,155 numerical facts**, including **eight recorded calculations**, and checked **40 cited numerical IDs** plus **nine distinct text IDs**. All **2,665 populated cells across ten sheets** were read. There were no unresolved citations, source-value mismatches or formula errors. Ten quoted excerpts occur across findings, including repeated source IDs. Source-supported values and arithmetic are verified; the narrative's completeness and economic interpretation are not certified.

| Issue | Application response | Remaining gap against standalone assessment |
|---|---|---|
| Cash quality / capital | Challenges management's $6.712m free-cash-flow definition; identifies CFO, interest, tax, cash investment, lease principal and declining cash | Does not derive $2.3m CFO less cash capex, negative $0.3m after lease principal, $7.3m economic capital deployment, or the net-debt increase. Says a post-financing FCF measure is not provided despite sufficient inputs to derive a bridge. No funded South replacement decision. |
| Adjusted earnings | Separates $11.457m adjusted from $9.712m reported EBITDA and questions $1.745m of addbacks | Does not isolate the $1.145m commodity/rental challenge and $10.312m sensitivity retaining sponsor fees; no independent commodity addback reconstruction. |
| Customer renewal | Identifies National Account 01's $2.86m revenue and $228,800 annual price sensitivity, explicitly not an EBITDA forecast | Omits combined $5.7m next-year renewal exposure and the $171,600 partial-year sensitivity. |
| Operating pressures | Quantifies plan miss and segment shortfalls; connects South fleet downtime, recycling price decline and East disposal cost | Broad grouping loses East's quantified disposal-rate impact and segment-specific intervention depth. Associations remain qualified; no full causal EBITDA bridge is claimed. |
| North growth | Retains favorable EBITDA performance and separates annualized contract wins from realized results | Omits physical tons-per-route improvement, customer growth and capital consumption, limiting assessment of repeatability and growth quality. |

No unsupported numerical assertion was found in the accepted cited amounts. The cash wording “declined by -$700k” is awkward signed presentation; the source value is correct. The claim of missing residual-cash information is analytically weak, even though the workbook lacks that exact named metric. This is an example of why deterministic validation cannot establish narrative completeness.

The preserved prior legacy evaluation recorded 136.33 seconds, three API calls, 57,425 input / 12,397 output tokens and $0.012493 estimated cost, with a successful cached result. It prioritized leased fleet/cash conversion, adjustments and South fleet disruption. It is a historical comparator, not a fresh matched control. Standalone Codex timing/token receipts were not available, so no standalone cost or speed advantage is asserted. Current evidence does not establish that this application engine reproduces the standalone reasoning advantage.

## Presentation and checks

With the completed **offline replay fixture**, Streamlit AppTest passed generation, dashboard priority titles, evidence navigation, session reuse and custom-template regeneration while HTTP inference was blocked. Both standard and custom Excel exports contain Findings, Source Evidence, Financial Performance and Analyst Execution; findings/evidence hyperlinks resolve, no Excel error-valued cells were found, and the sample template's C16 formula is preserved. Generated finding and diagnostic rows wrap to accommodate longer text; supplied template geometry remains intact. This checks document structure and Streamlit rendering, not a desktop Excel/PDF visual inspection.

The full suite passed **311 tests in 122.07 seconds**. After the final preflight/page-boundary hardening, the focused skill suite passed **38 tests**; Harrow also passed the tightened preflight. The new generic tests cover workbook/file boundaries, paging, malicious archives, source/calculation tampering, illustrative assumptions, schema and quote grounding, limit/failure handling, spend settlement, cache separation, mock full-workflow compatibility and both export paths. Run the suite with `.venv/bin/python -m pytest -q` (the bare `pytest` entry point in this environment does not put the repository root on the import path).

## Recommendation

Keep the feature opt-in and retain legacy. Expand **controlled reliability testing**, not rollout: first obtain a fresh successful run on the final code under the normal authorized cap, then use varied held-out workbooks to assess completion rate, reasoning depth, false rejections, unsupported interpretation and cold-cache cost. The restricted calculation tools can express the missing cash bridges, ratios and sensitivities; arbitrary Python or multi-agent orchestration is not justified by these results. Prioritize analytical selection and validation reliability. Resolve missing upstream license/provenance material before broader distribution.

## Reproducible development checkpoint

The three final approved synthetic Review snapshots and their source/receipt hashes
are versioned in `demo_results/`. See [checkpoint setup](skill-engine-checkpoint.md)
for offline verification and per-worktree cache import. Prepared-result reuse is
zero new inference and does not count as another fresh run. Raw diagnostics, failed
run bundles, live budget ledgers and generated exports remain ignored local files.
The four accepted presentation follow-ups are listed in that guide. No model or
analytical-engine change was made for the checkpoint.
