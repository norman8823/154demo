# Skill analyst development checkpoint

The checkpoint belongs on `feat/skill-analyst`. The analytical engine and model
configuration are frozen at the successful Harrow17, Summit05 and Tallis05 runs.
The global engine default remains legacy; `scripts/run_skill_demo.sh` opts into
the skill path. There is no portfolio implementation in this checkpoint.

## Prepared synthetic results and another checkout

Git includes the three synthetic source workbooks in `demo_workbooks/`, the
original event-staffing synthetic inputs in `inputs/`, regression fixtures in
`tests/fixtures/`, and the sample firm template in `sample_templates/`.
`demo_results/manifest.json` pins each approved result, workbook, methodology,
pricing receipt and analysis source file by SHA-256. Compact JSON/gzip snapshots
contain the completed Review contract, evidence, calculations and original
provider receipts. Only developer-local configuration paths were sanitized.
They contain neither credentials nor comparator/answer-key inputs. No evaluation
report is imported by the runtime analyst.

An ignored `.local/analysis-cache/` does **not** follow a Git branch or worktree.
The same is true of `.env`, the virtual environment, diagnostics and budget ledger.
Each checkout must install dependencies and seed its own cache:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
COPILOT_ENV_FILE='' .venv/bin/python scripts/seed_demo_results.py --verify-only
```

Verification is credential-free and recomputes retained source references,
arithmetic and quoted cells. It makes no model calls. It does not certify every
narrative conclusion. Source changes invalidate the prepared import rather than
silently labeling old findings as a new assessment.

The existing UI scopes its cache to the configured API credential and model and
requires a key even for cache lookup. Supply the **existing** configuration
securely, either through process environment or an untracked `.env`; never commit
or print it. A second local worktree can reference the original configuration
without copying the credential:

```sh
export COPILOT_ENV_FILE=/path/to/your/untracked/local/.env
.venv/bin/python scripts/seed_demo_results.py
./scripts/run_skill_demo.sh --server.port 8502
```

The import uses the launcher's analysis limits, verifies the existing model and
pricing against the receipts, and writes credential-scoped cache entries for all
three companies. It blocks HTTP requests internally and never invokes an analyst.
Changing the credential or effective settings requires seeding again; changing
analysis sources or the model causes a clear refusal. Do not use an invented key
to bypass the application's configuration requirement.

Choose a **Company workbook**, **Load company workbook**, then **Generate
Portfolio Review**. Unedited prepared companies reuse completed results; current
usage is zero calls/$0 and original usage remains under the receipt's `origin`.
This is prepared-result reuse, **not fresh inference**. Both Excel formats are
generated locally from the saved Review, and evidence navigation remains usable.
Tests exercise the actual company selector, dashboard, evidence and both exports
with provider access blocked. Modified uploads or mappings can miss the cache;
the ordinary launcher is inference-capable and is not an offline sandbox.

The historical task's cumulative budget file stays local and is not reset or
distributed. A second checkout does not inherit that authorization balance.
Seeding and displaying the approved results need no new paid inference; any new
paid experiment requires its own authorization and retained spend controls.

## Scope and exclusions

Source, tests, requirements, Streamlit theme, packaged methodology/NOTICE,
documentation and approved synthetic fixtures/results are included. `.env*`
(including a malformed hidden filename with a carriage return), Streamlit secrets,
private keys, `.local/`, `artifacts/`, virtual environments, Python/test caches,
logs, temporary files and original local design screenshots are excluded. Raw
provider responses, failed/withdrawn run bundles and generated Excel exports stay
local. The three approved snapshots are the deliberate generated-data exception.
Existing provenance limitations remain documented in the packaged NOTICE; no
upstream license grant is invented.

## Known reporting follow-ups

These presentation issues are accepted for this development checkpoint and are
not changes to the analytical engine:

- Remove stale AI-unavailable language from successful skill reports.
- Improve negative-dollar number formatting.
- Make custom-template headings period-aware.
- Reduce executive narrative repetition and review finding prioritization.

Analytical limitations and historical failed/replayed/withdrawn attempts remain
in `skill-engine-benchmark.md`. Prepared outputs do not resolve those limitations.

## Checkpoint verification

The freeze passed **349 tests** in 162.28 seconds on Python 3.14.6; dependency
consistency checks passed. All 90 staged files were audited, including decompressed
approved reviews and workbook XML, with no credentials or private runtime paths
found. A staged-only export verified all three prepared sources/calculations
without credentials, ignored caches or provider access. Existing source whitespace
is preserved, including the original CSV line endings and a legacy trailing space;
the analytical source hashes remain identical to the successful runs.

The staged-only export also passed all six prepared-result checks in 40.22
seconds, including all three dashboards, evidence navigation and both exports.
Tested dependencies were Streamlit 1.66.0, openpyxl 3.1.5, pandas 3.0.6, pytest
9.1.1 and Playwright 1.64.0; the requirements files retain the application's
existing supported version ranges.

Run `.venv/bin/python -m pytest -q` and `.venv/bin/python -m pip check`.
`tests/test_prepared_demo.py` verifies portable imports, credential/configuration
boundaries and all three actual Streamlit company flows with HTTP blocked,
including both Excel formats, evidence hyperlinks and the preserved template
formula. To reproduce the commit identity use `git rev-parse HEAD`; the handoff
records the exact checkpoint SHA and remote verification after commit/push.

Only after the skill checkpoint is committed and its GitHub branch verified may
`feat/portfolio-overview` be created from that exact SHA at
the portfolio repository. Creating that branch/worktree does not
authorize portfolio implementation, merging or deployment.
