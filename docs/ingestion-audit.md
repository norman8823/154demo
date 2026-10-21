# Adaptive ingestion audit (before changes)

The repository initially contained Streamlit intake/evidence UI (`app.py`), a known-format parser plus calculations (`engine.py`), and an independent Excel writer (`reports.py`). Baseline: 58 tests.

- Filenames: bundled demo loading uses `inputs/`; runtime role detection does not require source filenames. The sample template path and September report filenames are hardcoded.
- Worksheet/coordinate dependencies: Platform A uses `P&L!A5`, actual/budget columns B/C; `Operating KPIs!M4` and M-column labels; `Cover!A7`; named `CEO Letter`, `Covenant`, and formula-linked EBITDA/debt sheets. QuickBooks uses `Profit and Loss!A3/A5/E7`, September E-column accounts, named `Rate Card` with A:C, and a known CSV field vocabulary. The formula reader supports a bounded arithmetic vocabulary.
- File counts: partial uploads work, but only one platform workbook, one QuickBooks workbook and one schedule are permitted. Multiple company/monthly packages are rejected.
- Analysis coupling: profitability needs the entire platform-specific set of sheets and September columns. Covenant rules and billing matches are appropriate specialized adapters. Unknown general P&Ls cannot be normalized.
- Narratives: amounts are computed, but the three finding types/titles/questions are selected by adapter availability rather than general financial conditions. Period, company names, accounting caveats and UI headings assume the demo. No reusable revenue/EBITDA trend or reconciliation model exists.
- Mapping: the acquired-company preview contains three read-only classifications. There is no account review, saved mapping profile or LLM interpretation.
- Export: formatting, formula preservation, literal evidence text, reopening validation and placeholder fill are reusable. Metadata, metric names/statuses and placeholder semantics are demo-specific; report validation assumes known headline keys. These need a thin generic record path, not a new Excel writer.

Implementation boundary: retain the exact known-package adapter for original regression and specialized KPI/CEO, covenant and scheduling checks. Add conventional-statement extraction and a common normalized statement model with explicit source lineage, section/subtotal roles, period/basis/unit metadata and mapping review. Generic findings consume normalized records, never workbook coordinates. Reuse the existing UI cards, evidence tables and Excel fill/formatting engine.

## Implemented boundary and validation

The retained source-specific literals include the supplied sample template name and the known synthetic package signatures. New-company parsing does not use those signatures or hardcoded company/month cells. `ingestion.py` now emits reviewed normalized records; `financial_analysis.py` calculates general performance from those records. The original adapter also uses the shared normalized reducer for gross margin, while keeping its specialized KPI/CEO, covenant and schedule checks intact. `mapping_ui.py` supplies editable account/period review and `mapping_ai.py` supplies optional bounded, schema-validated interpretation. The existing Excel writer and dashboard components were extended rather than replaced.

Account and layout profiles use an ignored local JSON file, scoped to company/worksheet/account context. Dates and numeric facts are never saved as reusable assumptions. Two independently authored workbook structures and pre-recorded expectations are in `tests/fixtures/`. Final verification: 88 automated tests; actual Chrome upload, mapping correction, persistence, evidence and standard/custom Excel workflows; original full and partial demo browser regressions. No new runtime dependencies. Live API behavior remains untested without an API key; request/response validation and offline/manual fallback are tested.

## Task20 — optional mappings, source-first analysis

The former global mapping-approval gate is removed. Reported totals are used before account-level classification, and reconciled where source detail or an explicit EBITDA bridge is available. Material ambiguities are optional review suggestions; unconfirmed amounts never enter detail-based calculations. Conflicting or unsupported individual metrics are limited without blocking supported analysis. Overlapping summary/detail periods are not summed. Dimensional branch totals can be reconciled to the statement without treating branch columns as separate company statements.

The synthetic Summit regression and real upload/download checks cover one-click generation, changed source values, the actual EBITDA miss and unallocated $47K branch difference, optional mapping correction, and standard/custom Excel. Other narrative/KPI/AR interpretations remain explicitly outside the generic reader. No new dependency or infrastructure is introduced; source-specific known-package analysis is preserved.
