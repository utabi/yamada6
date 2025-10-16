# Yamada6

Yamada6 は、自律的に自己存続を守りつつ環境変化へ進化し続ける AI エージェントを Docker ベースで構築する計画です。全体方針は `yamada6_better.md` を参照してください。

## ドキュメント
- `AGENTS.md` — 作業前に必ず読む指針
- `yamada6_better.md` — 歴史と実装ロードマップ
- `yamada6.md` — 初期コンセプト概要
- `docs/PATCH_WORKFLOW.md` — staging → runtime のパッチ適用フロー案

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

## Runtime API (現在のひな形)
- `uvicorn` で FastAPI を起動し、ランタイムループと同一プロセスで動作
- `/healthz`, `/status` に加え、`/control/pause`, `/control/resume`, `/patches`, `/patches/{id}/apply` を提供
- `/patches` は runtime を一時停止した状態でのみ受け付け、staging から送られたパッチメタデータをキューに積む
- `/patches/{id}/apply` は適用リクエストを受け取り、現状はキューから除外するだけの雛形（実適用は今後実装）
- これらのエンドポイントをダッシュボード/承認フローから利用し、手動適用前の状態遷移を可視化する

## ライセンス
未定
