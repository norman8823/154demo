#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export COPILOT_ANALYST_ENGINE=skill
export COPILOT_AI_MAX_REVIEW_USD=0.25
export COPILOT_AI_TIMEOUT_SECONDS=300
export COPILOT_SKILL_SECONDS=900
export COPILOT_SKILL_REASONING_EFFORT=high
export COPILOT_SKILL_OUTPUT_TOKENS=32000
export COPILOT_TASK_BUDGET_USD=2
export COPILOT_TASK_BUDGET_FILE="$PWD/artifacts/skill-engine-tonight/budget.json"
exec .venv/bin/streamlit run app.py --server.address 127.0.0.1 "$@"
