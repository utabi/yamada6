#!/usr/bin/env bash
# 指定した diff ファイルを runtime に登録・適用する簡易ツール。
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <patch_id> <diff_file> [summary]" >&2
  exit 1
fi

PATCH_ID="$1"
DIFF_PATH="$2"
SUMMARY="${3:-Auto apply $PATCH_ID}"
BASE_URL="${PATCH_API_BASE:-http://127.0.0.1:8080}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT_DIR/.patch_env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.patch_env"
  set +a
fi

if [[ ! -f "$DIFF_PATH" ]]; then
  echo "diff file not found: $DIFF_PATH" >&2
  exit 1
fi

ABS_PATH=$(cd "$(dirname "$DIFF_PATH")" && pwd)/$(basename "$DIFF_PATH")

CREATED_AT=$(date -u "+%Y-%m-%dT%H:%M:%SZ")

pause_runtime() {
  curl -sf "$BASE_URL/control/pause" -X POST >/dev/null || true
}

resume_runtime() {
  curl -sf "$BASE_URL/control/resume" -X POST >/dev/null || true
}

register_patch() {
  python3 - <<'PY'
from pathlib import Path
import json
import os

payload = {
    "patch_id": os.environ['PATCH_ID'],
    "summary": os.environ['SUMMARY'],
    "author": os.environ.get('PATCH_AUTHOR', 'auto-staging'),
    "created_at": os.environ['CREATED_AT'],
    "artifact_uri": f"file://{os.environ['ABS_PATH']}",
    "notes": os.environ.get('PATCH_NOTES', ''),
    "diff_preview": Path(os.environ['ABS_PATH']).read_text(encoding='utf-8'),
}
print(json.dumps(payload))
PY
}

PATCH_AUTHOR=${PATCH_AUTHOR:-auto-staging}
PATCH_NOTES=${PATCH_NOTES:-}
export PATCH_ID SUMMARY CREATED_AT ABS_PATH PATCH_AUTHOR PATCH_NOTES

pause_runtime

JSON=$(register_patch)
REGISTER_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/patches" -H 'Content-Type: application/json' -d "$JSON")
REGISTER_BODY=$(echo "$REGISTER_RESP" | head -n1)
REGISTER_STATUS=$(echo "$REGISTER_RESP" | tail -n1)

if [[ "$REGISTER_STATUS" == "202" ]]; then
  echo "[info] patch queued: $PATCH_ID"
elif [[ "$REGISTER_STATUS" == "409" ]]; then
  echo "[warn] patch already exists (skipping register)"
else
  echo "[error] failed to register patch ($REGISTER_STATUS)\n$REGISTER_BODY" >&2
  exit 1
fi

APPLY_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/patches/$PATCH_ID/apply")
APPLY_BODY=$(echo "$APPLY_RESP" | head -n1)
APPLY_STATUS=$(echo "$APPLY_RESP" | tail -n1)

if [[ "$APPLY_STATUS" == "202" ]]; then
  if echo "$APPLY_BODY" | grep -q '"apply_success"'; then
    echo "[info] apply success: $PATCH_ID"
    resume_runtime
    exit 0
  else
    echo "[warn] apply returned non-success: $APPLY_BODY"
    exit 1
  fi
else
  echo "[error] apply failed ($APPLY_STATUS)\n$APPLY_BODY" >&2
  exit 1
fi
