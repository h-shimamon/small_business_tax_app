#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUFF="${ROOT_DIR}/venv/bin/ruff"

if [[ ! -x "${RUFF}" ]]; then
  echo "ruff executable not found at ${RUFF}" >&2
  exit 1
fi

${RUFF} check \
  app/pdf \
  app/company/forms \
  app/company/services/filings_service.py \
  tests/helpers/regression_utils.py \
  --select F,B,UP,I,C90 "$@"
