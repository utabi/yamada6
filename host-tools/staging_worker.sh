#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT_DIR/.patch_env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.patch_env"
  set +a
fi

VENV_ACTIVATE="$ROOT_DIR/agent/.venv/bin/activate"
if [[ -f "$VENV_ACTIVATE" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
fi

python3 -m agent.staging.worker "$@"
