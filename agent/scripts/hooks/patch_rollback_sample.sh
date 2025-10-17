#!/usr/bin/env bash
set -euo pipefail

PATCH_ID="$1"

# TODO: 適用時に作成した一時ファイルなどをクリーンアップ
# 例:
# git reset --hard
# git clean -fd

echo "rollback hook executed for $PATCH_ID"
