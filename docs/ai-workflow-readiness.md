# AI Workflow Automation Readiness

Focused follow-up to Portfolio Intelligence v3 checkpoint `7bd764d3d602a2fe27a4dcbc72780ffb5abe9857`, on `feat/ai-workflow-readiness`. Harmony **#45** tracks this feature; completed v1/v2/v3 milestones remain closed.

## One-minute demonstration

Open **http://127.0.0.1:8502/?page=foundation** or choose **Data Foundation**.

1. Expand **GP data model and assessment methodology**. The GP defines **Monthly Portfolio Operating Review** in a versioned JSON file, independently of Streamlit presentation. It requests revenue and reported EBITDA, each actual/budget, for September 2026 monthly reporting, plus entity, period, currency/unit and source identities. Accounting basis is optional; unknowns remain unknown.
2. Inspect the compact **Data Mapping** table. Filter by company, metric, scenario or period. Expand **Inspect a mapping and its source evidence** and choose any row: original labels, workbook/cell, source-unit values, formula provenance, scaling/sign normalization, entity and verification/mapping/approval distinctions remain accessible.
3. Open Summit's **$47,000** Data Issue. Inspect the calculation and operands, then open the existing accepted finding and evidence. Tallis's unresolved classifications and blank historical observations remain visible; Harrow's annual reporting is explicitly blocked from satisfying the monthly intake.
4. Download the existing six-file data package. Extract it and run `python3 example_consumer.py`. A different application can use the structured records without Streamlit modules, original Excel workbooks, credentials, network or inference.

**Different company inputs → Configurable data model → Company-specific mappings → Validated structured subset → Multiple potential applications.** The Investment Workspace is one consumer of the normalized data, not its exclusive owner.

## Configuration and measured coverage

The configuration is [monthly_portfolio_operating_review.json](../data_foundation/models/monthly_portfolio_operating_review.json), schema `gp-workflow-model-1.0`, model version `1.0.0`. Canonical IDs are `financial.revenue` and `financial.ebitda`. It reuses the existing report adapter's chosen current reported totals, rather than aggregating account detail, duplicate presentations or adjusted EBITDA sensitivities. Configuring additional unsupported current totals does not create new mappings.

One required slot is **company × required metric × scenario**: three companies × two metrics × two scenarios = **12**. A covered slot must have an accepted mapping, numeric source verification, required context, and the configured period/grain.

| Evaluated check | Result |
| --- | ---: |
| Mapped required slots at original source frequency | 12 / 12 |
| Source-checked required numeric observations | 12 / 12 |
| Mapped slots matching September 2026 monthly scope | 8 / 12 = **67%** rounded |
| Known evidence-backed issue groups | **4** |
| Total Readiness Score | **Not Evaluated** |

No total score or arbitrary weighting is manufactured. Comprehensive semantic validation and cross-schedule reconciliation have not been evaluated. Known exceptions remain open; four curated review groups are not an exhaustive audit or a count of distinct observation rows. Source verification, automatic mapping acceptance and documented human approval are different states. Human mapping approval remains **not_recorded**. Original `$` labels are not promoted to ISO currency codes; no FX conversion or accounting consolidation is inferred.

## Actual company mappings

All values below come from approved normalized records; source amounts for Summit and Harrow use a retained scale of 1,000, while Tallis uses base units. Correct scaling is not a quality failure.

| Company / source | Metric | Actual | Budget | Original cells |
| --- | --- | ---: | ---: | --- |
| Summit · Income Statement · September monthly | Revenue | 3,298,000 | 3,207,000 | D15 / C15 |
| Summit · Income Statement · September monthly | Reported EBITDA | 502,000 | 659,000 | D44 / C44 |
| Tallis · Practice P&L · September monthly | Revenue | 3,475,418 | 3,651,832 | G12 / I12 |
| Tallis · Practice P&L · September monthly | Reported EBITDA | 684,306 | 946,225 | G41 / I41 |
| Harrow · P&L Summary · FY2026 annual | Revenue | 46,650,000 | 47,006,000 | F13 / G13 |
| Harrow · P&L Summary · FY2026 annual | Reported EBITDA | 9,712,000 | 10,895,000 | F34 / G34 |

Company namespace, approved run, source ID, original entity, period/scenario, workbook and snapshot hashes are retained. Harrow's annual values remain useful evidence and are displayed honestly; they do not satisfy September monthly requirements. No monthly/annual financial total is calculated.

## Source-backed Data Issues

- **Summit — Review Required:** original accepted finding `10004`. `calc_6 = s3_L19 − s2_D44`: Branch Results L19 **549,000** less Income Statement D44 **502,000** = **47,000**. `calc_22 = s3_L9 − s2_D25`: cost of services **1,818,000 − 1,865,000 = −47,000**. `calc_48 = s3_L19 − s3_L17 + s3_L18 = 0` confirms internal branch arithmetic. Equal differences do not establish root cause or an additional economic loss. Request a ledger-backed allocations, eliminations, scope and cutoff bridge. The original descriptions/actions/caveats and full source closure are reused unchanged.
- **Tallis — Review Required:** **204 unresolved observation rows across 22 source labels**, repeated across periods and presentations. These include unfamiliar financial classifications and an ambiguous adjusted EBITDA label. Current reported revenue/EBITDA remain mapped. The queue retains the affected references, source values, mapping statuses and verification states; it does not claim 204 separate business issues or accept these rows automatically.
- **Tallis — Review Required:** **six blank historical comparator observations**, Dashboard **C10:C15**, September 2025. They cover LTM pro forma adjusted EBITDA, FTEs, revenue/FTE, realization, lockup days and retention. Missing values remain missing, not zero. Some overlap the unresolved-mapping queue, so the groups are not additive row counts.
- **Harrow — Blocked for monthly intake:** the four current revenue/EBITDA actual/budget headline operands are **FY2026 annual**. Obtain the requested monthly figures or explicitly configure a different workflow. The annual statements are not characterized as erroneous and are not divided into invented monthly values.

## Broader structured data and reuse

The workflow's 12-row candidate subset is separate from the broader data foundation. The existing ZIP remains **byte-identical to the v3 browser-downloaded package**, SHA-256 `b2e5da282e8b950dbae6a4c48cd45d4694a0441ac8cdbe35bc2d26fe72811a7b`:

- `financial_facts.csv`: **1,002** observations, including history, supporting metrics, unresolved classifications and blanks.
- `metric_definitions.json`: unchanged schema `operating-data-1.0` and semantics.
- `source_lineage.csv`: original source identities, coordinates, values/formulas and version hashes.
- `quality_report.json`: **996** checked numeric observations, **6** blanks, **204** unresolved mapping rows and approval distinctions.
- `example_consumer.py`: independent standard-library financial comparison.
- `README.md`: usage and limitations.

Illustrative investment-ledger assumptions remain excluded. Investment Monitoring, Underwriting, Due Diligence, Portfolio Operations, Expense Benchmarking and Compliance are **potential** downstream uses, not newly implemented or validated workflows. New-period ingestion, persistent approved mapping reuse and exhaustive source extraction are not automated by this feature.

## Verification and preview

- Full offline regression suite: **393 passed**, 248.63 seconds. A subsequent negative mapping/context test and the final visual correction were covered by **10 focused tests**, all passing in 22.73 seconds.
- Three approved prepared analyses verified with **zero new model calls**; original analytical code, approved snapshots, ledger and exporter are unchanged.
- Actual Chrome: desktop and mobile checked; source detail, original-finding navigation, ZIP download and independent consumer pass, with **zero external requests or browser errors**.
- Full existing v3 Chrome journey: all three company selectors/reviews, all **six company Excel downloads**, GP workbook with **34 sheets** and **17 issue-to-source chains**, Investment Issues, independent package consumer and mobile checks pass.
- Independent read-only review by `/root/readiness_review`: **no material findings**. The visual correction placed source operands and checked values ahead of long filenames in the issues table.
- Isolated consumer regression uses `-I -S` and audit hooks prohibiting application/third-party imports, original Excel access, network and out-of-package data reads.

Screenshots: [desktop](images/ai-readiness/desktop.png), [source inspection](images/ai-readiness/source-details.png), [reconciliation operands](images/ai-readiness/issue-operands.png), [mobile](images/ai-readiness/mobile.png). Full local receipts and downloaded artifacts remain in `artifacts/ai-readiness/` (ignored from source control).

Restart from the repository root using `./scripts/run_portfolio_demo.sh`. It binds **127.0.0.1:8502** and disables credential-file loading. Leave the frozen analytical-engine instance on 8501 untouched. For focused checks:

```sh
COPILOT_ENV_FILE='' .venv/bin/python -m pytest tests/test_portfolio_readiness.py tests/test_portfolio_foundation.py -q
COPILOT_ENV_FILE='' .venv/bin/python tests/browser_readiness.py
COPILOT_ENV_FILE='' .venv/bin/python scripts/seed_demo_results.py --verify-only
```

No deployment or merge is performed. Collect once, structure carefully, reuse across workflows.
