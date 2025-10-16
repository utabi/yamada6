# Docker 運用メモ

- `host-tools/start.sh` : `docker/compose.yml` を使って runtime/staging/dashboard を起動
- `host-tools/stop.sh`  : サービスを停止
- `host-tools/backup.sh`: `runtime_state` と `runtime_logs` ボリュームをアーカイブ

staging コンテナは git worktree を前提としており、`/workspace/agent` にホストの `agent/` ディレクトリがマウントされる。テスト・差分生成はここで実施し、成功後に API 経由で runtime へ適用するフローを構築する。

runtime コンテナはポート `8080` で FastAPI を提供し、`/healthz` と `/status` を通じて状態確認が可能。将来的な PDCA 制御や承認フローはこの API を起点に拡張する。
