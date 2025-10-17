# Yamada6

Yamada6 は、自律的に自己存続を守りつつ環境変化へ進化し続ける AI エージェントを Docker ベースで構築する計画です。全体方針は `yamada6_better.md` を参照してください。

## ドキュメント
- `AGENTS.md` — 作業前に必ず読む指針
- `yamada6_better.md` — 歴史と実装ロードマップ
- `yamada6.md` — 初期コンセプト概要
- `docs/PATCH_WORKFLOW.md` — staging → runtime のパッチ適用フロー案
- `docs/PATCH_HOOKS.md` — `PATCH_APPLY_HOOK` / `PATCH_ROLLBACK_HOOK` の使い方

## ディレクトリ概要
```
docker/        # Dockerfile と compose 設定
agent/         # ランタイムエージェントのソース・スクリプト・テスト
webui/         # ダッシュボード・API のフロント/バックエンド
host-tools/    # ホスト側ユーティリティ (起動/停止/バックアップ)
docs/          # 追加設計資料・運用メモ
volumes/       # Docker ボリュームのマウント先 (git では空)
```

## 着手順序
1. `yamada6_better.md` を読み、目的と Phase ロードマップを理解する
2. docker/ の scaffolding を整備し、staging → runtime の安全パイプラインを構築する
3. PDCA 制御・ドライブサイドカー・データライフサイクルを段階的に組み込む

- `uvicorn` で FastAPI を起動し、ランタイムループと同一プロセスで動作
- `/healthz`, `/status` に加え、`/control/pause`, `/control/resume`, `/patches`, `/patches/{id}`, `/patches/{id}/apply`, `/patches/{id}/rollback`, `/patches/applied`, `/patches/audit` を提供
- `/patches` は runtime を一時停止した状態でのみ受け付け、staging から送られたパッチメタデータをキューに積む
- `/patches/{id}/apply` は `artifact_uri` からアーティファクトをコピーし、`PATCH_APPLY_MODE` / `PATCH_APPLY_HOOK` に基づいて適用テストを実行。成功なら pending から除外し `/patches/applied` へ、失敗なら pending に残し `audit.log` に `apply_failed` を記録
- `/patches/audit` で全履歴（queued / artifact_copied / apply_success / apply_failed など）を JSON で取得可能

### 環境変数
- `PATCH_STORAGE_DIR` … アーティファクトと JSON メタデータを保存するパス (既定 `state/patches/`)
- `PATCH_WORKSPACE` … `PATCH_APPLY_HOOK` 実行時の作業ディレクトリ (既定 `cwd`)
- `PATCH_APPLY_MODE` … `noop` / `fail` で疑似適用挙動を切り替え
- `PATCH_APPLY_HOOK` … パッチ適用時に呼び出すスクリプト
- `PATCH_ROLLBACK_HOOK` … ロールバック時に呼び出すスクリプト
- これらのエンドポイントをダッシュボード/承認フローから利用し、手動適用前の状態遷移を可視化する

## ライセンス
未定
