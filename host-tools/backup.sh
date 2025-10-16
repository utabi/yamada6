#!/usr/bin/env bash
# runtime/staging の重要データを tar.gz にまとめるシンプルなスクリプト。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE="$BACKUP_DIR/yamada6_backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

# Docker volume のバックアップは `docker run --rm` で取得する必要がある。
# ここでは runtime_state / runtime_logs のスナップショットを取る。
docker run --rm \
  -v yamada6_runtime_state:/data/state:ro \
  -v yamada6_runtime_logs:/data/logs:ro \
  -v "$BACKUP_DIR":/backup \
  alpine:3.19 \
  sh -c "cd /data && tar -czf /backup/$(basename "$ARCHIVE") state logs"

echo "Backup created: $ARCHIVE"
