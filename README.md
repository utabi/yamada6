# Yamada6

Yamada6 は、自律的に自己存続を守りつつ環境変化へ進化し続ける AI エージェントを Docker ベースで構築する計画です。全体方針は `yamada6_better.md` を参照してください。

## ドキュメント
- `AGENTS.md` — 作業前に必ず読む指針
- `yamada6_better.md` — 歴史と実装ロードマップ
- `yamada6.md` — 初期コンセプト概要

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
- `uvicorn` で `agent.runtime.entrypoint` が FastAPI を起動し、`/healthz` と `/status` を公開
- `/status` は最後に生成したプランや実行結果を簡易 JSON で返す（将来的に PDCA 情報へ拡張）
- `docker/compose.yml` ではポート `8080` を公開し、ダッシュボードや staging から参照できるようにしている

## ライセンス
未定
