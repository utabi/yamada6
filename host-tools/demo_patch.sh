#!/usr/bin/env bash
# docs/OVERVIEW.md に自動で行追加し、runtime に登録・適用するデモ。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_ID="demo-auto-$(date +%s)"
SUMMARY="Auto demo patch $PATCH_ID"
TARGET="$ROOT_DIR/docs/OVERVIEW.md"
TMP_DIR=$(mktemp -d)
PATCH_FILE="$TMP_DIR/${PATCH_ID}.diff"

python - "$TARGET" "$PATCH_FILE" <<'PY'
import datetime as dt
import subprocess
import sys
from pathlib import Path

source = Path(sys.argv[1]).resolve()
patch_path = Path(sys.argv[2]).resolve()

text = source.read_text(encoding="utf-8").rstrip("\n")
timestamp = dt.datetime.utcnow().isoformat() + "Z"
addition = f"\n- Auto generated note at {timestamp}"

workdir = patch_path.parent
orig = workdir / "orig.txt"
mod = workdir / "mod.txt"
orig.write_text(text + "\n", encoding="utf-8")
mod.write_text(text + addition + "\n", encoding="utf-8")

result = subprocess.run(
    ["git", "diff", "--no-index", str(orig), str(mod)],
    capture_output=True,
    text=True,
    check=False,
)
if result.returncode not in (0, 1):
    raise SystemExit(result.stderr)
patch_path.write_text(result.stdout, encoding="utf-8")
PY

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

"$ROOT_DIR/host-tools/apply_patch.sh" "$PATCH_ID" "$PATCH_FILE" "$SUMMARY"
