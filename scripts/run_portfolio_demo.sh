#!/bin/sh
# Prepared-only portfolio app; no credential loading or analytical entrypoint.
set -eu
cd "$(dirname "$0")/.."
export COPILOT_ENV_FILE=''
exec .venv/bin/python -m streamlit run portfolio_app.py --server.address 127.0.0.1 --server.port 8502 "$@"
