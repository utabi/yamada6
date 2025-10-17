# パッチ適用ワークフロー案

1. staging コンテナで diff を生成し、テスト結果と共に runtime API へ登録
   - POST `/control/pause`
   - POST `/patches` でメタデータ + S3/volume パスを通知（`artifact_uri` / `test_report_uri`）
   - GET `/patches` / `/patches/{id}` で承認者が内容を確認
2. 人間 or ダッシュボードで承認 → runtime が `/patches/{id}/apply` で取り込み
3. runtime はパッチを適用し、結果をステータスに反映
   - `artifact_uri` が `file://` の場合、`PATCH_STORAGE_DIR`（`state/patches/`）へコピー (`*.artifact`)
   - 成功なら `/status` から pending queue を除外し、`/patches/applied` と `/patches/audit` に記録
   - 失敗なら `/patches/{id}/rollback` などで再実施を検討（今後実装）

現状は `file://` のアーティファクトコピーと監査ログの記録まで対応。実際の `git apply` やテスト再実行は今後追加予定。メタデータは `state/patches/<id>.json` に保存され、再起動後も参照できる。
