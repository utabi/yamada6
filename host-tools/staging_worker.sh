#!/usr/bin/env bash
# 簡易 staging worker: 自動で差分を生成し、runtime に登録 → 適用する
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_ID="auto-$(date +%s)"
SUMMARY="Auto generated patch $PATCH_ID"
TARGET_REL="docs/OVERVIEW.md"
TARGET_PATH="$ROOT_DIR/$TARGET_REL"
TMP_BASE="$ROOT_DIR/tmp/staging_worker"
mkdir -p "$TMP_BASE"
TMP_DIR=$(mktemp -d "$TMP_BASE/XXXXXX")
PATCH_FILE="$TMP_DIR/${PATCH_ID}.diff"

python3 <<'PY'
from datetime import datetime, timezone
import difflib
import os
from pathlib import Path

source_path = Path(os.environ['TARGET_PATH'])
patch_path = Path(os.environ['PATCH_FILE'])
rel = os.environ['TARGET_REL']

text = source_path.read_text(encoding='utf-8').splitlines()
addition = f"- staging worker note {datetime.now(timezone.utc).isoformat()}"
modified = text + [addition]

patch = difflib.unified_diff(
    text,
    modified,
    fromfile=f"a/{rel}",
    tofile=f"b/{rel}",
    lineterm='\n',
)
patch_path.write_text(''.join(patch), encoding='utf-8')
PY

trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/host-tools/apply_patch.sh" "$PATCH_ID" "$PATCH_FILE" "$SUMMARY"
