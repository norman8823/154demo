# Minimal skill engine migration map

Audit: no applicable AGENTS.md was found in the workspace/ancestor instructions. Existing uncommitted application files are preserved. The sole runtime source for this vertical slice is the uploaded workbook, not any prior review or evaluation fixture.

| Area | Actual modules and contracts | Migration |
|---|---|---|
| Loading / normalization | engine.Book (restricted Excel arithmetic), ingestion.inspect_files/apply_decisions/normalized_records, financial_analysis.analyze_intake; package_reader.read_package | Preserve. Add preflight ZIP/XML/resource bounds before any skill-path load; reuse Book in workbook tools. Retain local financial extraction independently of analyst interpretation. |
| Analysis | engine.analyze/_analyze_package; analyst_ai.interpret; investigation.investigate and investigation_math | Preserve legacy unchanged. Add skill_engine.py single bounded multi-pass Responses workflow, targeted indexed repair and validated partial publication, selected by COPILOT_ANALYST_ENGINE=skill. No initial legacy findings enter model input. |
| Validation / contract | engine.Review; investment_output.grounded/management_question; investigation.publish; company_context | Add skill_output.py adapter. Recompute referenced cells/calculations, reuse prose grounding, retain diagnostics; no numerical check certifies narrative truth. |
| UI | app.compute/overview/evidence_view/readiness; executive.present/report_findings; card_presentation | Preserve cards, evidence, questions and summary. Add engine/complete/partial/failure disclosure, explicit legacy selection and local company workbook selector. Normalize untouched mapping defaults so UI and unattended runs share valid caches. |
| Exports | reports.export_report/fields/validate_export; excel_layout | Preserve standard and custom-template routes; include execution/validation metadata in both and fit mapped narrative row heights while preserving template formulas, styles, merges and widths. |
| Runtime / spend | ai_runtime.configuration/complete/inference_session/persist_diagnostics | Reuse model, authorization and conservative spending reservations. Add deadline support, cached-token reporting and task_budget.py locked cumulative reservations alongside existing per-review limits. |
| Cache | report_cache.cache_key/successful/ReportCache | Separate engine, resource content, tools, schema and limits; cache only completed supported skill results. |
| New tools/resources | skill_tools.py; resources/pe-investment-analyst-v2 | Paged inventory/range/search and source-linked restricted arithmetic, explicit percentage-point scaling, typed day-count calculations, per-unit money and Excel SUM blank handling; no filesystem/network/code execution tool. |

Standalone comparator: artifacts/harrow_ridge_fy2026/{investment_assessment.md,findings.json,evidence_ledger.csv}. Source: user-specified Harrow workbook in Documents/NL Intelligence/154. Existing Harrow evaluation materials under artifacts/general-reliability-* and artifacts/harrow-authorization-holdout remain evaluation-only and are not imported by the engine.

Official API references checked: https://developers.openai.com/api/docs/guides/function-calling (Responses function_call/function_call_output, call IDs, strict schemas); https://developers.openai.com/api/docs/models/gpt-6-luna (configured model, Responses support, current standard token rates). Skills are application instructions/resources here, not an assumed Codex execution endpoint.

Tonight’s follow-up adds `scripts/run_skill_demo.sh` (local opt-in launcher with authorized spending caps), a local workbook selector, and `scripts/verify_skill_run.py` (read-only verification of fresh saved receipts). No additional runtime agent or arbitrary-code execution environment was introduced.
