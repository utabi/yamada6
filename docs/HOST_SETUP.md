# ホスト初期設定メモ

1. パッチ用ディレクトリ・hook を設定
   ```bash
   ./host-tools/configure-hooks.sh
   source .patch_env
   ```

2. `PATCH_WORKSPACE` 配下に git worktree 用の一時ディレクトリが作成される（既定 `$HOME/.yamada6`）。

3. docker-compose 起動前に `.patch_env` を `source` しておくと、runtime が hook を利用できる。

4. staging コンテナからは、`PATCH_APPLY_MODE` を `noop` または `fail` に設定して挙動をテストできる。
