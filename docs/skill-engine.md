# Skill analyst engine (experimental)

The default remains the legacy engine. The new path is a single analyst workflow with packaged PE Investment Analyst v2 instructions and workbook-only tools. No Codex execution service, multi-agent orchestration, shell tool or model-authored Python is used.

## Enable and run

For prepared demo reuse in a new checkout, first follow the
[checkpoint and offline seeding guide](skill-engine-checkpoint.md). It preserves
the three approved provider receipts without rerunning inference; local caches
are not distributed by Git.

From the repository root, use the existing environment/model/API-key configuration:

```sh
./scripts/run_skill_demo.sh
```

Choose a local **Company workbook**, click **Load company workbook**, then **Generate Portfolio Review**, or upload one `.xlsx` workbook. The launcher opts into skill analysis and enforces tonight’s $0.25 per-analysis / $2 cumulative task allowance in `artifacts/skill-engine-tonight/budget.json`. The ledger persists across processes and restarts; the launcher never resets it. The ordinary application default remains legacy. The existing external-analysis consent policy applies. When enabled, the setup screen also offers **Legacy analyst (explicit fallback)**. Choosing legacy reruns that engine; a failed skill run never silently substitutes legacy findings. Omit the flag to retain the current default. These new flags are process environment settings; do not assume unrecognized `.env` keys are loaded by the existing loader.

Unattended measurement uses the same `engine.analyze` entry point as the UI and both existing export paths:

```sh
COPILOT_AI_MAX_REVIEW_USD=0.25 COPILOT_AI_TIMEOUT_SECONDS=300 \
COPILOT_SKILL_SECONDS=900 COPILOT_SKILL_OUTPUT_TOKENS=32000 \
COPILOT_SKILL_REASONING_EFFORT=high COPILOT_TASK_BUDGET_USD=2 \
COPILOT_TASK_BUDGET_FILE="$PWD/artifacts/skill-engine-tonight/budget.json" \
.venv/bin/python scripts/benchmark_skill.py /path/to/company.xlsx artifacts/new-run --authorize
```

The destination must be new so prior results are preserved. The script reads no answer keys, comparator reports or prior findings. The explicit authorization switch permits the configured API to process workbook values, labels, formulas and notes; the original binary workbook is not uploaded. A failed run saves its status, receipts and diagnostic exports, not a completed assessment. Do not treat a zero-call cache hit as a new unattended inference measurement.

## Bounds and measurement

The demo launcher uses the existing model with explicit `COPILOT_SKILL_REASONING_EFFORT=high` and a 300-second request timeout and 900-second overall allowance. Explicit reasoning effort is validated for documented supported models and included in cache identity. The launcher also sets `COPILOT_SKILL_OUTPUT_TOKENS=32000`: reasoning tokens share the response allowance, and the 16,000-token high-reasoning comparison exhausted it before finishing JSON. Earlier medium-reasoning reports had source-selection errors. These are development observations, not a controlled model benchmark.

Existing `OPENAI_MODEL`, pricing overrides, `COPILOT_AI_MAX_REVIEW_USD`, timeout and retry controls remain authoritative. No new model is hard-coded. Defaults for this path:

| Process setting | Default | Maximum |
|---|---:|---:|
| COPILOT_SKILL_ROUNDS | 14 | 20 |
| COPILOT_SKILL_TOOL_CALLS | 160 | 240 |
| COPILOT_SKILL_SECONDS | 600 | 900 |
| COPILOT_SKILL_OUTPUT_TOKENS | 16000 | 32000 |

Full coverage no longer disables tools. The analyst can investigate across sheets and perform multiple calculation passes. A required five-area, relevance-based completion check covers management claims, cash/reinvestment/debt, earnings quality, customer/operating exposures, and decisions/uncertainty/favorable developments. Each tested area cites workbook or calculation IDs. Material cohort totals must record selection criteria, fiscal/calendar boundaries, eligible row IDs and exclusions; period endpoints are inclusive unless the source says otherwise. Selected examples must be labeled subtotals. These checks record the analyst’s self-assessment; they do not establish completeness by themselves.

The final two rounds, twice the configured request timeout, and a conservative two-request monetary allowance are reserved for final output and one targeted repair. Tool calls are disabled only when a reserve boundary is reached, not after the first calculation batch. If an output has invalid findings, the repair receives those findings and the workbook state; it returns indexed replacements, never regenerating accepted siblings. Validation reports all prose-field failures together, including their bounds, so a repair can address them in one pass. The schema targets concise fields (60 words for conclusions); the adapter retains verified prose within a 160-word hard bound per model-provided prose field before fixed publication caveats and reports target-length warnings. Titles retain their short bound. Numerical checks are unchanged. Prior validation attempts remain in diagnostics. Each request reserves a conservative token-price upper bound before sending. For the skill path only, a completed provider response with known usage settles that reservation to the measured estimate; failures, missing usage and model mismatch retain the reservation. Settlement never raises the authorized ceiling. Estimates use configured standard token rates and reported cache usage; they are not invoices. Local calculations, network timeouts and before/after-request checks prevent late responses from being published.

The review records engine/methodology/tool/schema identities, resource hashes, model/returned model, per-call tokens, reasoning tokens and cache reads/writes where reported, requests, tool arguments/results status, runtime, source coverage, validation failures, completion/failure reason and estimated cost. Both Excel formats add an **Analyst Execution** sheet. For skill reports, only mapped template narrative row heights expand to fit longer text; template formulas, merged cells, widths and cell styles are preserved. Raw provider responses remain in the existing private diagnostics directory; financial payloads are not emitted to ordinary inference logs.

## Tools and validation

- ZIP/XML preflight accepts one `.xlsx`, up to 8 MB compressed / 32 MB expanded, 30 sheets, 2,000 rows and 80 columns per sheet, 30,000 stored cells and 120,000 total grid positions. DTD/entities, VBA, macro sheets and embedded executable objects are rejected. External workbook links are not followed. Calculations are capped at 100. Cell text, aggregate formula-range expansion before local normalization, formula evaluation, paging and calculation counts are bounded. A cell too large for one tool page fails explicitly instead of producing an empty continuation loop.
- Inventory includes hidden sheets. Range reads return labels, values, original formulas, computed values, available formula caches and comments. Search is literal and paged. Result pages return explicit continuation offsets, never relevance-based truncation. Completion requires all populated source cells to have been read.
- Calculations support fact IDs, finite numeric constants, `+ - * /`, bounded `sum`, `min`, `max`, `abs`, and `days(ratio, calendar_day_count)`. They preserve source operands and expressions. Unsupported Excel formulas/caches are disclosed and excluded from numerical citations; a directly cited blank is unavailable. Excel SUM ignores blank spacer cells, matching Excel semantics.
- Explicit source units normalize monetary values before calculations. Dimension checks reject unscaled ratio differences labeled as percentage points; multiply by 100 explicitly. Explicit DSO, WIP-day and lockup labels use days; client-count headers use counts; monetary aging buckets remain money. These local labels and per-unit currency labels override sheet-level monetary scale. Economic constants or explicit scenario flags mark illustrative calculations; growth identity and percentage-point conversion constants remain historical arithmetic. A divisor matching the number of distinct, same-unit source terms in an unweighted mean is a recorded arithmetic convention, not an economic scenario. Explanatory notes alone do not turn a historical comparison into a sensitivity. Period, entity, accounting basis, denominator meaning and economic appropriateness still require review: arithmetic alone cannot validate those judgments.
- Findings use the existing accepted insight/card/evidence contract through `skill_output.py`. Figures must be cited placeholders. Fiscal-year descriptors are bound to cited cell headers or explicit sheet headings; numbered entity names and negated certainty are distinguished from literal quantities and affirmative claims. Source values and calculations are recomputed; quotes must match read cells. Existing numerical prose grounding, source quotation, affirmative-causation and question validation remain between model output and publication. Recorded illustrative flags deterministically produce explicit report labels and caveats, even if the model omitted those words; assumptions remain in the calculation ledger and no arithmetic is altered. A lexical uncertainty screen is advisory: when qualification is unclear, the adapter adds an explicit investment-team-review caveat and records a warning instead of rejecting numerically supported findings. This does not certify the narrative or erase its original text. Rejected candidates and validation failures are retained visibly. If repair fails or a limit is reached after validated findings exist, the valid subset is published as a conspicuous **PARTIAL REVIEW**. Cards, briefing, questions and exports are rebuilt solely from accepted findings. Rejected findings and diagnostics remain available; partial results are not saved in the completed-report cache. With no valid findings the status is failed. Complete requires all source cells read, completion checks present and no unresolved validation rejection.
- Context compaction retains every read cell value/label and calculation, removes repeated tool envelopes, and keeps original formulas accessible by range reads. It does not select just prominent rows or introduce another model summarizer.

## Remaining limits

This is an opt-in single-workbook implementation, not a production accounting or legal assurance system. There is no arbitrary Python, macros, external links, PDF contract retrieval, FX conversion, invoice joins, full Excel formula engine or cross-workbook consolidation. Resource limits deliberately exclude large packages. The underlying financial extraction and company description still use existing local heuristics; their coverage limitations remain visible. Numbers embedded only in text (such as a management threshold or replacement-cost note) are not exposed as typed numeric cells; calculations may use recorded literal assumptions with quoted context and are conservatively labeled illustrative. A literal price embedded only in a note also lacks a monetary type: count × literal price cannot safely become money under the current dimension rules. Replacement-cost and similar scenarios therefore need a structured source price cell or a future source-bound numeric extraction tool. This is a concrete tool limitation; no arbitrary Python environment was added. The model can choose an economically inappropriate expression even if its arithmetic is correct. Narrative explanations and source scope require human investment-team review. Elapsed limits are cooperative checks plus bounded network socket timeouts: late results are never published, but this implementation does not forcibly kill a slow OS/network call or isolate normalization in a worker process.

The supplied skill resource attribution is retained verbatim. Its referenced upstream SOURCES_AND_CHANGES.md and license notice were absent from the installed package; see the packaged NOTICE.md. Resolve that provenance gap before broader redistribution.

Optional `COPILOT_TASK_BUDGET_FILE` and `COPILOT_TASK_BUDGET_USD` add a locked, persistent request-reservation ledger across analyses. Each request reserves before network access; known completed usage settles to estimated cost. Unknown/incomplete requests retain their upper reservation. A changed ledger ceiling fails closed. Per-review ceilings still apply independently. These controls constrain estimates, not the provider’s invoice.

Official API features were checked against [Responses function calling](https://developers.openai.com/api/docs/guides/function-calling) and [the configured model's documentation and standard pricing](https://developers.openai.com/api/docs/models/gpt-6-luna) on October 20, 2026. These URLs document implementation and pricing assumptions, not a promised per-review cost.
