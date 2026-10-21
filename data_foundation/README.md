# AI-ready operating data package

Schema: **operating-data-1.0**. The three companies and source packages are synthetic demo data. These files reuse the approved normalized Review contracts and retained source-verification records. No new extraction, mapping decisions or AI inference are performed by this export.

Extract all six files together, then run:

```sh
python3 example_consumer.py
```

The standalone consumer uses only Python's standard library. It checks package content hashes, reads CSV/JSON and emits a company financial comparison. It imports no application modules, opens no Excel workbooks, uses no credentials and makes no network/model calls. It selects explicitly marked reported totals; it never sums account details, subtotals or duplicate dashboard/statement presentations.

## Contents

- `financial_facts.csv`: retained normalized observations, including accepted automatic mappings, unresolved mappings and blank observations. A record is not automatically suitable for aggregation.
- `metric_definitions.json`: canonical metric definitions, field dictionaries, enums, scale/sign/period conventions and schema version.
- `source_lineage.csv`: one-to-one fact keys, normalized source aliases, retained observed-fact IDs, original workbook/sheet/cell/header coordinates, original values/formula provenance, and workbook/snapshot hashes.
- `quality_report.json`: technical verification, missing/blank observations, unresolved mappings, original analytical limitations, approval distinctions and SHA-256 hashes of the other five files. Hashes identify package content, not a digital signature or human approval.
- `example_consumer.py`: independent period-aware comparison using only these files.
- `README.md`: this guide.

## Semantics and safe reuse

`company_id` is the application registry identifier. `fact_key` qualifies the original `source_fact_id` by company and approved Review run; aliases such as `financial_34` are not globally unique. IDs are stable within that version, not promises of cross-cycle mapping persistence. `metric_id` names the retained financial category; `source_label`, `entity_name`, `context` and `role` retain account-level meaning. Unmapped observations use `unmapped.source_observation`, which is not a standardized financial metric. Do not infer a new classification from its name.

`period`, `period_grain` and `scenario` come directly from the Review. September monthly, fiscal-quarter and annual observations remain distinct; fiscal periods are not relabeled as calendar periods. `value` is the retained normalized base-unit value, with source scale and approved expense-sign normalization exposed. `raw_source_value` is in original source units. `unit` retains the observed fact's unit. `currency` preserves the source currency label: `$` remains `$`, not an inferred ISO currency. There is no currency conversion. Unknown units, basis and scale remain unknown. Blank CSV values mean missing, not zero. Booleans are lowercase `true`/`false`.

`comparison_selected=true` identifies only the existing report adapter's current-period, reported revenue/EBITDA actual/budget operands. It makes duplicate source presentations explicit rather than establishing an aggregation rule. All other history/details remain in the package. The consumer compares each company's own period and same-scope budget and derives EBITDA/revenue margin within the same source scope; it produces no cross-company financial total.

`verification_status=source_observation_verified` means a numeric source observation matches the retained checked workbook fact and approved version hashes. It does not certify a mapping, forecast, causal interpretation, collectibility judgment or valuation. `normalization_status` reports whether the retained scale/sign arithmetic reconciles. `mapping_accepted` and `mapping_status` distinguish existing automatic acceptance from unresolved classification; `accepted` is not human approval. `human_approval_status=not_recorded` means no explicit mapping sign-off evidence is present in this contract. The approved demo checkpoint and technical acceptance of 17 AI findings do not establish analyst approval of every mapping.

Original formulas in `source_lineage.csv` are JSON string literals in `original_formula_json`, for provenance only. Decode with `json.loads`; do not execute them. Source coordinates and hashes identify evidence but the ZIP deliberately contains no Excel workbooks. The application GP workbook separately includes navigable read-only source snapshots.

The synthetic investment ledger is deliberately excluded. Its hypothetical enterprise values, debt/cash assumptions, ownership, invested capital and returns are a separate provenance class and must never be joined into source-verified operating facts without that distinction.

This is a portable data handoff, not a database, API, automated reporting pipeline or approval system. First and subsequent reporting cycles are not fully automated. Persistent analyst-approved mapping reuse has not been built or validated. Source observations and arithmetic are verified; original narrative interpretations and unresolved classifications still require investment-team review. Consult `quality_report.json` before downstream use.
