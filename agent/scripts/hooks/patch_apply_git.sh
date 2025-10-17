#!/usr/bin/env bash
# git worktree を使って patch を安全に検証・適用するサンプル。
set -euo pipefail

PATCH_ID="$1"
PATCH_FILE="$2"

: "${PATCH_WORKSPACE:=$(pwd)}"
: "${PATCH_GIT_ROOT:=$(git rev-parse --show-toplevel)}"
WORKTREES_DIR="${PATCH_WORKSPACE}/.patch-worktrees"
mkdir -p "$WORKTREES_DIR"
WORKTREE_PATH="${WORKTREES_DIR}/${PATCH_ID}"

if git worktree list | grep -q "${WORKTREE_PATH}"; then
  git worktree remove --force "$WORKTREE_PATH"
fi

git worktree add "$WORKTREE_PATH"

pushd "$WORKTREE_PATH" >/dev/null
trap 'git reset --hard; popd >/dev/null; git worktree remove --force "$WORKTREE_PATH"' EXIT

git apply "$PATCH_FILE"

if command -v pytest >/dev/null 2>&1; then
  pytest >/tmp/patch_apply_${PATCH_ID}.log
fi

git reset --hard
