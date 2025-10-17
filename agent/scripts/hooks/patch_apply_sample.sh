#!/usr/bin/env bash
set -euo pipefail

PATCH_FILE="$1"

# TODO: 安全な git worktree / テスト実行手順をここに記述
# 例:
# WORKTREE_DIR=$(mktemp -d)
# git worktree add "$WORKTREE_DIR"
# pushd "$WORKTREE_DIR" >/dev/null
# git apply "$PATCH_FILE"
# pytest
# git reset --hard
# popd >/dev/null
# git worktree remove "$WORKTREE_DIR"

echo "patch apply hook executed for $PATCH_FILE"
