#!/usr/bin/env bash
# docs/OVERVIEW.md に自動で1行追加し、patch を適用するデモ。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_ID="demo-auto-$(date +%s)"
SUMMARY="Auto demo patch $PATCH_ID"
TARGET_REL="docs/OVERVIEW.md"
TARGET_PATH="$ROOT_DIR/$TARGET_REL"
TMP_BASE="$ROOT_DIR/tmp/demo_patch"
mkdir -p "$TMP_BASE"
TMP_DIR=$(mktemp -d "$TMP_BASE/XXXXXX")
PATCH_FILE="$TMP_DIR/${PATCH_ID}.diff"

export TARGET_PATH PATCH_FILE TARGET_REL

python3 <<'PY'
from datetime import datetime, timezone
import difflib
import os
from pathlib import Path

source_path = Path(os.environ['TARGET_PATH'])
patch_path = Path(os.environ['PATCH_FILE'])
rel = os.environ['TARGET_REL']

text = source_path.read_text(encoding='utf-8').splitlines()
addition = f"- Auto generated note at {datetime.now(timezone.utc).isoformat()}"
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

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

"$ROOT_DIR/host-tools/apply_patch.sh" "$PATCH_ID" "$PATCH_FILE" "$SUMMARY"
