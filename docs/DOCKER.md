# Docker 運用メモ

- `host-tools/start.sh` : `docker/compose.yml` を使って runtime/staging/dashboard を起動
- `host-tools/stop.sh`  : サービスを停止
- `host-tools/backup.sh`: `runtime_state` と `runtime_logs` ボリュームをアーカイブ

staging コンテナは git worktree を前提としており、`/workspace/agent` にホストの `agent/` ディレクトリがマウントされる。テスト・差分生成はここで実施し、成功後に API 経由で runtime へ適用するフローを構築する。

runtime コンテナはポート `8080` で FastAPI を提供し、`/healthz`, `/status`, `/control/*`, `/patches`, `/patches/{id}`, `/patches/{id}/apply`, `/patches/{id}/rollback`, `/patches/applied`, `/patches/audit` を通じて状態を制御できる。staging からの diff は `/patches` に送信し、適用前に runtime を `/control/pause` で停止、承認後 `/patches/{id}/apply` で実適用を進める設計。登録されたメタデータは `state/patches/*.json` に保存され、アーティファクトは `PATCH_STORAGE_DIR`（デフォルト `state/patches/`）配下にコピーされる。適用処理は `PATCH_APPLY_MODE` / `PATCH_APPLY_HOOK` で挙動を切り替えられ、監査ログは `state/patches/audit.log`（`/patches/audit`）で参照できる。`/patches/{id}/rollback` は stub（今後実装）。
