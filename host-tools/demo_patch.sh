#!/usr/bin/env bash
# docs/OVERVIEW.md に自動で1行追加し、patch を適用するデモ。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_ID="demo-auto-$(date +%s)"
SUMMARY="Auto demo patch $PATCH_ID"
TARGET_REL="docs/OVERVIEW.md"
TARGET_PATH="$ROOT_DIR/$TARGET_REL"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/yamada6_demo.XXXXXX")
PATCH_FILE="$TMP_DIR/${PATCH_ID}.diff"

python - "$TARGET_PATH" "$PATCH_FILE" "$TARGET_REL" <<'PY'
import datetime as dt
import difflib
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
patch_path = Path(sys.argv[2])
rel = sys.argv[3]
text = source_path.read_text(encoding="utf-8").splitlines()
addition = f"- Auto generated note at {dt.datetime.utcnow().isoformat()}Z"
modified = text + [addition]

# difflib unified diff
patch = difflib.unified_diff(
    text,
    modified,
    fromfile=f"a/{rel}",
    tofile=f"b/{rel}",
    lineterm="\n",
)
patch_path.write_text("".join(patch), encoding="utf-8")
PY

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

"$ROOT_DIR/host-tools/apply_patch.sh" "$PATCH_ID" "$PATCH_FILE" "$SUMMARY"
