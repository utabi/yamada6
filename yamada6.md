# Yamada6 概要 (Docker 自律エージェント構想)

## 1. コンセプト
- 自己編集／自己修復を Docker コンテナ内部で完結させる。
- ホスト環境は最小限のコントローラに留め、エージェントの「身体」をコンテナに封じ込める。
- 破損した場合はコンテナ再生成で即リセット可能。状態管理は volume / DB に切り出す。
- ホストとの I/O はダッシュボード/REST API 経由に限定し、直接ファイルを触らせない。

## 2. アーキテクチャ
```
yamada6/
  README.md, DESIGN.md
  docker/
    Dockerfile.runtime       # 実行用コンテナ
    Dockerfile.staging       # 自己編集検証用コンテナ
    compose.yml              # runtime / staging / dashboard / db
  agent/
    src/
      planner.py
      executor.py
      scheduler.py
      ...
    tests/
      unit/ integration/
    scripts/
      manage.py
      apply_patch.py
  webui/
    dashboard/
    api/
  host-tools/
    start.sh / stop.sh
    backup.sh
  volumes/ (docker volume に紐づくデータ)
```

### コンテナ構成
1. **runtime**
   - エージェント本体 (planner / executor / scheduler)
   - 状態データ `state/`, `logs/` を docker volume で永続化
   - webhook/API から指示を受け付ける

2. **staging**
   - runtime のソースを同期し、自己編集やテストを実施する専用コンテナ
   - diff 生成 → テスト → 成功時に runtime へ適用
   - 安全策: staging 内の `git worktree`、コンパイル/pytest/ruff を全てここで実行

3. **dashboard** / **api**
   - ブラウザ UI (チャット・タスク表示・状態可視化)
   - runtime と WebSocket/REST で連携
   - 人間からの承認や指示を入力する窓口

4. **（任意）DB**
   - ログ・メトリクスが巨大化する場合は SQLite/Postgres 等で管理
   - Prometheus + Grafana を入れてもよい

## 3. 自己編集フロー
1. runtime がプランを生成し、自分の改善案 (`self_edits`) を staging に投げる
2. staging コンテナでソースを `git clone` → diff 生成 → `pytest` / `ruff` / `py_compile`
3. すべて合格後、runtime に適用 API を送る (`git apply` or `rsync`)
4. 失敗時は staging 側でロールバックし、runtime には触れない
5. 適用結果・エラーは dashboard に集約

## 4. 開発ステップ（最初の TODO）
1. **docker scaffolding**
   - `docker/Dockerfile.runtime` / `Dockerfile.staging` を用意
   - `docker-compose.yml` で各サービスと volume を定義
2. **インフラ基盤**
   - runtime コンテナに planner/executor/scheduler のベースコードを移植
   - staging コンテナで `scripts/apply_patch.py` を整備
3. **ダッシュボード API**
   - 人間チャット入力、承認ワークフロー、状態閲覧
   - `/api/self_edits`, `/api/status`, `/api/logs`
4. **テスト + セーフティ**
   - 全編集前に staging で `pytest`, `ruff`, `py_compile`
   - 失敗→ staging 内でロールバック、result を dashboard に表示
5. **運用ツール**
   - `host-tools/start.sh` -> `docker compose up`
   - `host-tools/stop.sh` -> `docker compose down`
   - `host-tools/backup.sh` -> volume スナップショット

## 5. 今後の課題
- LLM で diff の精度が低い場合の fallback 戦略（AST 編集や別 LLM）
- コンテナ越しに安全に API やネットワークを扱う権限設計
- 長期メモリ（DB）の構成、バックアップポリシー
- ダッシュボードから staging のテスト結果を監視・承認する UX
- 困難な編集を人間承認に切り替えるワークフロー

---
まずは `docker/` と `host-tools/` の骨組み、staging ワークフローを優先実装すると安定した自律環境が構築できます。EOF
