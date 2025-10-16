# Docker 運用メモ

- `host-tools/start.sh` : `docker/compose.yml` を使って runtime/staging/dashboard を起動
- `host-tools/stop.sh`  : サービスを停止
- `host-tools/backup.sh`: `runtime_state` と `runtime_logs` ボリュームをアーカイブ

staging コンテナは git worktree を前提としており、`/workspace/agent` にホストの `agent/` ディレクトリがマウントされる。テスト・差分生成はここで実施し、成功後に API 経由で runtime へ適用するフローを構築する。
