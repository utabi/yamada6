#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_DIR="$ROOT_DIR/agent/scripts/hooks"
WORKSPACE_DIR="${PATCH_WORKSPACE:-$HOME/.yamada6}"
mkdir -p "$WORKSPACE_DIR"

echo "Using PATCH_WORKSPACE=$WORKSPACE_DIR"

if [[ -z "${PATCH_APPLY_HOOK:-}" ]]; then
  export PATCH_APPLY_HOOK="$HOOK_DIR/patch_apply_git.sh"
fi

if [[ -z "${PATCH_ROLLBACK_HOOK:-}" ]]; then
  export PATCH_ROLLBACK_HOOK="$HOOK_DIR/patch_rollback_sample.sh"
fi

cat <<ENV > "$ROOT_DIR/.patch_env"
PATCH_WORKSPACE=$WORKSPACE_DIR
PATCH_APPLY_HOOK=$PATCH_APPLY_HOOK
PATCH_ROLLBACK_HOOK=$PATCH_ROLLBACK_HOOK
ENV

echo "Patch hook configuration written to $ROOT_DIR/.patch_env"
