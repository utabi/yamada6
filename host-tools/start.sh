#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ -f .patch_env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .patch_env
  set +a
fi

docker compose -f docker/compose.yml up -d "$@"
