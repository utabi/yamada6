# パッチ適用ワークフロー案

1. staging コンテナで diff を生成し、テスト結果と共に runtime API へ登録
   - POST `/control/pause`
   - POST `/patches` でメタデータ + S3/volume パスを通知（`artifact_uri` / `test_report_uri`）
   - GET `/patches` / `/patches/{id}` で承認者が内容を確認
2. 人間 or ダッシュボードで承認 → runtime が `/patches/{id}/apply` で取り込み
3. runtime はパッチを適用し、結果をステータスに反映
   - `artifact_uri` が `file://` の場合、`PATCH_STORAGE_DIR`（`state/patches/`）へコピー (`*.artifact`)
   - `/patches/{id}/apply` は `PATCH_APPLY_MODE` / `PATCH_APPLY_HOOK` に基づき適用テストを実行し、結果を `audit.log` に `apply_success` / `apply_failed` として記録
   - 成功時は `/status` から pending queue を除外し `/patches/applied` に反映。失敗時は pending に残り、`/patches/{id}/rollback` (stub) や再実行で対応

現状は `file://` のアーティファクトコピーと監査ログ・疑似適用フローまで実装済み。`PATCH_APPLY_MODE=fail` で失敗動作をテストできる。`PATCH_APPLY_HOOK` を使えば任意スクリプト（例: git worktree で `git apply` → テスト → `git reset --hard`）を呼び出せる。Docker を使わず `./host-tools/run_runtime.sh` で runtime API を起動して試験可能。メタデータは `state/patches/<id>.json` に保存され、再起動後も参照可能。
