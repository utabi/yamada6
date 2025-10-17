# Patch Hook 設定メモ

`PATCH_APPLY_HOOK` と `PATCH_ROLLBACK_HOOK` を利用すると、runtime の `/patches/{id}/apply` / `/patches/{id}/rollback` が任意のスクリプトを呼び出すように設定できる。hook には `(patch_id, artifact_path)` の順で引数が渡される。

## 1. apply hook の例
`agent/scripts/hooks/patch_apply_sample.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

PATCH_FILE="$1"

# 例: git worktree で安全に適用し、テストを実行
# git worktree add -f /tmp/yamada6-apply
# cd /tmp/yamada6-apply
# git apply "$PATCH_FILE"
# pytest
# git reset --hard
# git worktree remove /tmp/yamada6-apply

echo "patch applied: $PATCH_FILE"
```

上記スクリプトを実行可能にし、`PATCH_APPLY_HOOK` にパスを指定すると、適用時に stdout/stderr が `audit.log` に記録される。

## 2. rollback hook の例
`agent/scripts/hooks/patch_rollback_sample.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail

PATCH_ID="$1"
# 任意のクリーンアップ処理を記述
# 例: git reset --hard && git clean -fd

echo "rollback executed for $PATCH_ID"
```

`PATCH_ROLLBACK_HOOK` を設定すると、`/patches/{id}/rollback` が発火時にこのスクリプトを呼び出す。終了コードが 0 の場合は `rollback_success`、それ以外は `rollback_failed` として `audit.log` に記録される。

## 3. git worktree を利用した標準フック
`agent/scripts/hooks/patch_apply_git.sh` は git worktree を用いて patch を検証するサンプル。環境変数 `PATCH_WORKSPACE` を指定すると、`<workspace>/.patch-worktrees/<patch_id>` に一時 worktree を作成し `git apply` → `pytest` を実行する。

設定例:

```bash
export PATCH_WORKSPACE="$HOME/.yamada6"
export PATCH_APPLY_HOOK="$(pwd)/agent/scripts/hooks/patch_apply_git.sh"
```

## 3. テスト用モード
- `PATCH_APPLY_MODE=fail` … `/patches/{id}/apply` が強制的に失敗し、pending に残る
- 設定無し（デフォルト `noop`） … 適用成功として扱う

## 4. 監査ログ
`state/patches/audit.log` に JSONL 形式で書き込まれる。`/patches/audit` を叩けば API で一覧取得できる。`stdout` / `stderr` / `command` 情報も格納される。
